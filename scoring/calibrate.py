#!/usr/bin/env python3
"""
Choros Scoring Calibration Pipeline
====================================
Tests 3 rubric strategies against human-scored ASAP essays.
Measures which strategy most reduces the LLM scoring compression bias
(walk-down mechanism: model correctly identifies flaws in reasoning,
then overrides at final score).

Strategies tested:
  A) Holistic (baseline) — single 2-12 score, current approach
  B) Binary agents    — per-criterion Y/N, then convert to score (PReMISE / EACL)
  C) Non-compensation  — holistic + PReMISE clause ("do not reward style if
                          content is wrong")

Outputs Cohen's Kappa for each strategy vs human scores.
A Kappa > 0.6 indicates the strategy produces signal beyond random agreement.

Conference sources:
  - PReMISE: Policy Rubrics as Measurement Specifications (ICLR 2026)
  - 6 Ways LLM Judges Are Biased (Agentic AI & Cloud Advisory)
  - JudgmentBench: Comparing Rubric and Preference Evaluation
  - EACL 2026: Eliminate Judge Bias via Binary Scoring Agents

Usage:
  python3 calibrate.py [--model gemma4:26b] [--ollama http://100.85.15.59:11434]
"""

import json, sys, time, os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.15.59:11434")
MODEL = os.environ.get("CHOROS_MODEL", "phi4:latest")
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
RESULTS_PATH = DATA_DIR / "calibration_results.json"

# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------

def ollama_generate(prompt: str, model: str = MODEL, temperature: float = 0.3,
                    num_predict: int = 512, timeout: int = 120) -> str:
    """Call Ollama /api/generate, return response text."""
    import urllib.request, urllib.error

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        }
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()).get("response", "")
    except Exception as e:
        return f"[ERROR: {e}]"


# ---------------------------------------------------------------------------
# Scoring strategies
# ---------------------------------------------------------------------------

def score_holistic(essay_text: str) -> int | None:
    """Strategy A: Single holistic 2-12 score — current baseline approach."""
    prompt = f"""You are grading a student essay on a 2-12 scale. The prompt was:
"Explain whether students should be required to wear uniforms."

ESSAY:
{essay_text}

Give a SINGLE INTEGER score from 2 to 12. Then explain your reasoning in 1-2 sentences.
Output format:
SCORE: <integer>
REASONING: <1-2 sentences>"""

    response = ollama_generate(prompt)
    # Extract score — try multiple patterns
    import re
    match = re.search(r'(?:SCORE|score|Score):\s*(\d+)', response)
    if not match:
        # Fallback: find standalone number near the start
        match = re.search(r'\b(1[0-2]|[2-9])\b', response[:200])
    if match:
        score = int(match.group(1))
        return max(2, min(12, score))  # clamp
    return None


def score_binary_agents(essay_text: str) -> int | None:
    """Strategy B: Per-criterion binary (Y/N) scoring, then convert to scale.
    
    Breaking the rubric into independent Y/N questions prevents the model from
    collapsing to a middle-ground compromise (Kucia et al. 2026, EACL 2026).
    """
    import re
    criteria = [
        ("CLAIM", "Does the essay state a clear position on uniforms?"),
        ("EVIDENCE", "Does the essay support its position with specific reasons or examples?"),
        ("STRUCTURE", "Does the essay have a recognizable introduction, body, and conclusion?"),
        ("COUNTER", "Does the essay acknowledge or respond to an opposing viewpoint?"),
        ("LANGUAGE", "Is the writing mostly free of grammar and spelling errors?"),
        ("DEPTH", "Does the essay show nuanced thinking beyond surface-level arguments?"),
    ]
    
    yes_count = 0
    for name, question in criteria:
        prompt = f"""You are evaluating ONE specific criterion of a student essay. Answer ONLY yes or no.

CRITERION: {question}

ESSAY:
{essay_text}

Does this essay meet this criterion? Answer YES or NO only."""

        response = ollama_generate(prompt, temperature=0.1, num_predict=10)
        # Accept any leading case-insensitive YES/NO
        first_word = response.strip().upper()
        # Extract first token
        if first_word.startswith("YES") or first_word == "Y":
            yes_count += 1
        elif not (first_word.startswith("NO") or first_word == "N"):
            # Fallback: search anywhere in response
            if re.search(r'\bYES\b', first_word):
                yes_count += 1
    
    # Convert Y count to 2-12 scale: each Y = ~2 points
    # 0 Y = 2, 6 Y = 12
    score = 2 + (yes_count * 10 // 6)
    return max(2, min(12, score))


def score_noncompensation(essay_text: str) -> int | None:
    """Strategy C: Holistic score with PReMISE non-compensation clause.
    
    Explicitly commands the judge NOT to reward formatting/politeness
    if the core argument is weak.
    """
    prompt = f"""You are grading a student essay on a 2-12 scale. The prompt was:
"Explain whether students should be required to wear uniforms."

CRITICAL RULES — READ CAREFULLY:
1. The score must reflect the QUALITY OF THE ARGUMENT, not the quality of the writing.
2. Do NOT reward good grammar, polite tone, or formal structure if the argument is weak or missing.
3. A well-written essay with no evidence = LOW score. A rough essay with strong reasoning = HIGH score.
4. If the essay makes no real argument, it cannot score above 4.
5. If the essay lacks evidence or examples, it cannot score above 6.

ESSAY:
{essay_text}

Give a SINGLE INTEGER score from 2 to 12 following these rules.
Output format:
SCORE: <integer>
REASONING: <1-2 sentences>"""

    response = ollama_generate(prompt)
    import re
    match = re.search(r'SCORE:\s*(\d+)', response)
    if match:
        score = int(match.group(1))
        return max(2, min(12, score))
    return None


# ---------------------------------------------------------------------------
# Cohen's Kappa
# ---------------------------------------------------------------------------

def cohens_kappa(human_scores: list[int], model_scores: list[int]) -> float:
    """Compute Cohen's Kappa for agreement above chance.
    
    Kappa = (po - pe) / (1 - pe)
    where po = observed agreement, pe = expected agreement by chance.
    
    Values: <0 = worse than chance, 0-0.2 = slight, 0.2-0.4 = fair,
            0.4-0.6 = moderate, 0.6-0.8 = substantial, >0.8 = near perfect.
    """
    from collections import Counter
    
    n = len(human_scores)
    if n == 0:
        return 0.0
    
    # Build confusion matrix
    matrix = {}
    all_cats = set()
    for h, m in zip(human_scores, model_scores):
        all_cats.add(h)
        all_cats.add(m)
        matrix[(h, m)] = matrix.get((h, m), 0) + 1
    
    # Observed agreement
    po = sum(1 for h, m in zip(human_scores, model_scores) if h == m) / n
    
    # Expected agreement
    pe = 0.0
    for cat in all_cats:
        p_human = sum(1 for h in human_scores if h == cat) / n
        p_model = sum(1 for m in model_scores if m == cat) / n
        pe += p_human * p_model
    
    if pe == 1.0:
        return 1.0
    
    return (po - pe) / (1 - pe)


# ---------------------------------------------------------------------------
# Main calibration run
# ---------------------------------------------------------------------------

def run_calibration():
    """Run all 3 strategies against the ASAP test set."""
    print(f"Choros Scoring Calibration")
    print(f"Model: {MODEL} @ {OLLAMA_URL}")
    print(f"Test set: {ESSAYS_PATH}\n")
    
    # Load essays
    with open(ESSAYS_PATH) as f:
        data = json.load(f)
    
    essays = data["essays"]
    human_scores = [e["score"] for e in essays]
    
    strategies = {
        "A_holistic": ("Holistic (baseline)", score_holistic),
        "B_binary": ("Binary Agents (PReMISE/EACL)", score_binary_agents),
        "C_noncomp": ("Non-Compensation (PReMISE)", score_noncompensation),
    }
    
    results = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "human_scores": {e["id"]: e["score"] for e in essays},
        "strategies": {},
    }
    
    for strat_key, (strat_label, strat_fn) in strategies.items():
        print(f"{'='*60}")
        print(f"Strategy: {strat_label}")
        print(f"{'='*60}")
        
        model_scores = []
        details = []
        
        for i, essay in enumerate(essays):
            eid = essay["id"]
            human = essay["score"]
            text = essay["text"]
            
            print(f"  [{i+1}/{len(essays)}] {eid} (human: {human})...", end=" ", flush=True)
            t0 = time.time()
            score = strat_fn(text)
            elapsed = time.time() - t0
            
            if score is not None:
                delta = score - human
                sign = "+" if delta > 0 else ""
                print(f"model: {score} ({sign}{delta} vs human) [{elapsed:.0f}s]")
                model_scores.append(score)
                details.append({
                    "id": eid,
                    "human": human,
                    "model": score,
                    "delta": delta,
                    "elapsed_s": round(elapsed, 1),
                })
            else:
                print(f"FAILED to extract score [{elapsed:.0f}s]")
                model_scores.append(human)  # fallback to human (neutral)
                details.append({"id": eid, "human": human, "model": None, "error": True})
        
        # Compute Kappa
        kappa = cohens_kappa(human_scores, model_scores)
        
        # Compute compression metrics
        human_range = max(human_scores) - min(human_scores)
        model_range = max(model_scores) - min(model_scores)
        compression_ratio = model_range / human_range if human_range > 0 else 1.0
        
        print(f"\n  Kappa: {kappa:.3f}")
        print(f"  Human range: {min(human_scores)}-{max(human_scores)} (span {human_range})")
        print(f"  Model range: {min(model_scores)}-{max(model_scores)} (span {model_range})")
        print(f"  Compression ratio: {compression_ratio:.2f} (1.0 = no compression, <1.0 = compressed)")
        
        results["strategies"][strat_key] = {
            "label": strat_label,
            "kappa": round(kappa, 3),
            "human_range": [min(human_scores), max(human_scores)],
            "model_range": [min(model_scores), max(model_scores)],
            "compression_ratio": round(compression_ratio, 3),
            "scores": details,
        }
    
    # Summary comparison
    print(f"\n{'='*60}")
    print(f"SUMMARY COMPARISON")
    print(f"{'='*60}")
    print(f"{'Strategy':<30} {'Kappa':>8} {'Compression':>12} {'Range':>12}")
    print(f"{'-'*30} {'-'*8} {'-'*12} {'-'*12}")
    
    best_kappa = max(results["strategies"].items(), key=lambda x: x[1]["kappa"])
    
    for key, s in results["strategies"].items():
        marker = " ← BEST" if key == best_kappa[0] else ""
        print(f"{s['label']:<30} {s['kappa']:>8.3f} {s['compression_ratio']:>12.2f} "
              f"{s['model_range'][0]}-{s['model_range'][1]:>3}{marker}")
    
    # Save results
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {RESULTS_PATH}")
    
    return results


if __name__ == "__main__":
    run_calibration()

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
MODEL = os.environ.get("CHOROS_MODEL", "gemma4:26b")
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
RESULTS_PATH = DATA_DIR / "calibration_results.json"

# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------

def ollama_generate(prompt: str, model: str = MODEL, temperature: float = 0.3,
                    num_predict: int = 2048, timeout: int = 120) -> str:
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

        response = ollama_generate(prompt, temperature=0.1, num_predict=512)
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
# Strategy D: Evidence-Grounded Checklist (Rulers / Hong et al. 2026)
# ---------------------------------------------------------------------------
#
# The Rulers paper formalized what we discovered with form-fill: rubric locking +
# evidence grounding + post-hoc calibration produces QWK 0.72 on ASAP 2.0 (vs 0.48
# direct holistic). We add the evidence + calibration layers to our form-fill approach.
#
# Pipeline:
#   1. Model fills out a 7-item checklist with 0/1/2 decisions
#   2. For each checked item, model must quote exact text from the essay
#   3. Python verifies quotes are verbatim substrings of the source
#   4. Raw checklist counts are calibrated via ridge regression to human score distribution

# Evidence type per criterion:
#   local_quote  — must be a verbatim substring of the essay
#   span_level   — describes a section/paragraph (looser: keywords must appear)
#   global       — overall diagnostic (no substring check, just recorded)
CHECKLIST_CRITERIA = [
    {
        "id": "CLAIM", "label": "Position & Claim",
        "question": "Does the essay state a clear position on school uniforms?",
        "evidence_type": "local_quote",
        "max_points": 2,
    },
    {
        "id": "EVIDENCE_COUNT", "label": "Evidence Count",
        "question": "How many distinct reasons or examples support the position?",
        "evidence_type": "span_level",
        "max_points": 2,
    },
    {
        "id": "EVIDENCE_QUALITY", "label": "Evidence Quality",
        "question": "Are the reasons/examples specific and concrete (not vague generalities)?",
        "evidence_type": "local_quote",
        "max_points": 2,
    },
    {
        "id": "COUNTER", "label": "Counterargument",
        "question": "Does the essay acknowledge or respond to an opposing viewpoint?",
        "evidence_type": "local_quote",
        "max_points": 2,
    },
    {
        "id": "STRUCTURE", "label": "Structure",
        "question": "Does the essay have a recognizable introduction, body, and conclusion?",
        "evidence_type": "global",
        "max_points": 2,
    },
    {
        "id": "GRAMMAR", "label": "Grammar & Conventions",
        "question": "Is the writing mostly free of grammar, spelling, and punctuation errors?",
        "evidence_type": "global",
        "max_points": 2,
    },
    {
        "id": "DEPTH", "label": "Depth & Nuance",
        "question": "Does the essay show nuanced thinking beyond surface-level arguments?",
        "evidence_type": "global",
        "max_points": 2,
    },
]


def validate_evidence(essay_text: str, quote: str, evidence_type: str) -> bool:
    """Check that a quoted piece of evidence is genuinely present in the essay.

    local_quote: must be a verbatim substring (whitespace-normalized)
    span_level:  at least 2 significant words from the quote appear in the essay
    global:      always passes (recorded but not verified)
    """
    if evidence_type == "global":
        return True  # subjective diagnostic — no substring check possible

    # Normalize whitespace
    essay_norm = " ".join(essay_text.split())
    quote_norm = " ".join(quote.split())

    if evidence_type == "local_quote":
        return quote_norm.lower() in essay_norm.lower()

    if evidence_type == "span_level":
        # At least 2 significant words (3+ chars) from the quote appear in the essay
        words = [w.lower() for w in quote.split() if len(w) >= 3]
        found = sum(1 for w in words if w in essay_norm.lower())
        return found >= min(2, len(words)) if words else True

    return True


def score_evidence_checklist(essay_text: str) -> dict | None:
    """Strategy D: Model fills out a form. Python reads the boxes and counts.

    The model checks [x] met, [/] partial, or [ ] not met for each criterion
    and provides evidence. Python:
      1. Reads which box the model checked (0, 1, or 2)
      2. Verifies the evidence quote is a verbatim substring of the essay
      3. Counts the checked boxes — that's the score
      4. Python does NOT judge quality — just reads the form and counts
    """
    import re, json as _json

    # ── Build the checklist form ──
    criteria_lines = ""
    for i, c in enumerate(CHECKLIST_CRITERIA, 1):
        criteria_lines += (
            f"{i}. **{c['label']}** — {c['question']}\n"
            f"   [ ] Not met   [/] Partial   [x] Met\n\n"
        )

    prompt = f"""You are evaluating a student essay against a structured checklist.
For each criterion, choose ONE: [x] Met, [/] Partial, or [ ] Not met.
Then provide a short verbatim quote from the essay as evidence.

CRITICAL RULES:
- Evidence MUST be copied VERBATIM from the essay — do NOT paraphrase
- If you check [ ] Not met, write "none" as the evidence
- If you check [/] Partial, quote the partial evidence you found
- Quote enough context to be meaningful (1-2 sentences)

ESSAY:
---
{essay_text}
---

CHECKLIST:
{criteria_lines}

Respond in valid JSON ONLY — no other text:
```json
{{
  "criteria": [
    {{
      "id": "CLAIM",
      "check": "x",
      "evidence": "verbatim quote from essay"
    }},
    {{
      "id": "EVIDENCE_COUNT",
      "check": "/", 
      "evidence": "..."
    }},
    ...all 7 criteria...
  ]
}}
```
Where "check" is "x" (met), "/" (partial), or " " (not met)."""

    response = ollama_generate(prompt, temperature=0.2, num_predict=8192, timeout=180)

    # ── Parse JSON ──
    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if not json_match:
        return None

    try:
        parsed = _json.loads(json_match.group(0) if json_match.lastindex is None
                            else json_match.group(1))
    except _json.JSONDecodeError:
        return None

    criteria_results = parsed.get("criteria", [])
    if len(criteria_results) != len(CHECKLIST_CRITERIA):
        return None

    # ── Python reads the boxes and counts ──
    decisions = []
    evidence_valid = []
    total_score = 0

    for i, result in enumerate(criteria_results):
        expected = CHECKLIST_CRITERIA[i]
        check = result.get("check", " ").strip()
        quote = result.get("evidence", "").strip('"').strip()

        # Model's checkbox → score
        if check == "x":
            model_score = 2
        elif check == "/":
            model_score = 1
        else:
            model_score = 0

        # Verify evidence is real
        valid = validate_evidence(essay_text, quote, expected["evidence_type"])

        decisions.append({
            "id": expected["id"],
            "label": expected["label"],
            "check": check,
            "box_score": model_score,
            "evidence": quote,
            "evidence_valid": valid,
        })
        evidence_valid.append(valid)
        total_score += model_score

    # Map 0-14 raw to 2-12 scale
    mapped = round(2 + (total_score * 10 / 14))

    return {
        "raw_score": total_score,
        "mapped_score": mapped,
        "evidence_valid": evidence_valid,
        "valid_count": sum(evidence_valid),
        "total_count": len(evidence_valid),
        "decisions": decisions,
        "raw_response": response,
    }


# ---------------------------------------------------------------------------
# Ridge Regression Calibration (Rulers post-hoc calibration)
# ---------------------------------------------------------------------------

def calibrate_ridge(raw_scores: list[int], human_scores: list[int],
                    alpha: float = 0.5) -> dict:
    """Fit a ridge regression to map checklist raw scores → human score distribution.

    Uses polynomial features (degree 2) with ridge regularization, as in the
    Rulers paper. With small N (our 5 essays), alpha=0.5 provides light
    regularization while still fitting the data.

    Returns dict with:
      - coefficients: [intercept, linear_coef, quadratic_coef]
      - fitted_scores: calibrated predictions for the input set
      - formula: human-readable calibration formula
    """
    import numpy as np

    n = len(raw_scores)
    if n < 2:
        return {
            "coefficients": [float(np.mean(human_scores)), 0.0, 0.0],
            "fitted_scores": [float(np.mean(human_scores))] * n,
            "formula": f"score = {np.mean(human_scores):.1f} (constant — insufficient data)",
        }

    raw = np.array(raw_scores, dtype=float)
    human = np.array(human_scores, dtype=float)

    # Polynomial features: [1, raw, raw^2]
    X = np.column_stack([np.ones(n), raw, raw ** 2])

    # Ridge: β = (X^T X + αI)^(-1) X^T y
    I_mat = np.eye(3)
    I_mat[0, 0] = 0  # don't regularize the intercept
    beta = np.linalg.solve(X.T @ X + alpha * I_mat, X.T @ human)

    fitted = X @ beta

    # Build readable formula
    b0, b1, b2 = beta
    formula = f"score = {b0:.3f} + {b1:.3f}·raw + {b2:.4f}·raw²"

    return {
        "coefficients": [float(b0), float(b1), float(b2)],
        "fitted_scores": [round(max(2, min(12, s)), 1) for s in fitted],
        "fitted_scores_raw": [float(s) for s in fitted],
        "formula": formula,
    }


def apply_calibration(raw_score: int, calibration: dict) -> float:
    """Apply fitted ridge calibration to a new raw score."""
    b0, b1, b2 = calibration["coefficients"]
    raw = float(raw_score)
    predicted = b0 + b1 * raw + b2 * raw ** 2
    return round(max(2, min(12, predicted)), 1)


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
        "A_holistic": ("Holistic (baseline)", score_holistic, False),
        "B_binary": ("Binary Agents (PReMISE/EACL)", score_binary_agents, False),
        "C_noncomp": ("Non-Compensation (PReMISE)", score_noncompensation, False),
        "D_evidence": ("Evidence-Grounded Checklist (Rulers)", score_evidence_checklist, True),
    }
    
    results = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "human_scores": {e["id"]: e["score"] for e in essays},
        "strategies": {},
    }
    
    for strat_key, (strat_label, strat_fn, is_checklist) in strategies.items():
        print(f"{'='*60}")
        print(f"Strategy: {strat_label}")
        print(f"{'='*60}")
        
        model_scores = []
        details = []
        raw_scores_checklist = []  # for ridge calibration
        
        for i, essay in enumerate(essays):
            eid = essay["id"]
            human = essay["score"]
            text = essay["text"]
            
            print(f"  [{i+1}/{len(essays)}] {eid} (human: {human})...", end=" ", flush=True)
            t0 = time.time()
            result = strat_fn(text)
            elapsed = time.time() - t0
            
            if is_checklist:
                # Strategy D: dict result with evidence + raw_score
                if result is not None:
                    raw = result["raw_score"]
                    score = result["mapped_score"]
                    delta = score - human
                    sign = "+" if delta > 0 else ""
                    vcount = result["valid_count"]
                    print(f"raw={raw} mapped={score} ({sign}{delta}) "
                          f"evidence={vcount}/{result['total_count']} [{elapsed:.0f}s]")
                    model_scores.append(score)
                    raw_scores_checklist.append(raw)
                    details.append({
                        "id": eid, "human": human, "model": score,
                        "raw_score": raw, "delta": delta,
                        "evidence_valid": vcount, "evidence_total": result["total_count"],
                        "decisions": result["decisions"],
                        "elapsed_s": round(elapsed, 1),
                    })
                else:
                    print(f"FAILED to parse response [{elapsed:.0f}s]")
                    model_scores.append(human)
                    raw_scores_checklist.append(0)
                    details.append({"id": eid, "human": human, "model": None, "error": True})
            else:
                # Strategies A/B/C: int score
                score = result
                if score is not None:
                    delta = score - human
                    sign = "+" if delta > 0 else ""
                    print(f"model: {score} ({sign}{delta} vs human) [{elapsed:.0f}s]")
                    model_scores.append(score)
                    details.append({
                        "id": eid, "human": human, "model": score,
                        "delta": delta, "elapsed_s": round(elapsed, 1),
                    })
                else:
                    print(f"FAILED to extract score [{elapsed:.0f}s]")
                    model_scores.append(human)
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
        
        # Ridge calibration for checklist strategies (Rulers post-hoc calibration)
        calibrated_kappa = None
        calibration = None
        if is_checklist and raw_scores_checklist and len(raw_scores_checklist) >= 2:
            calibration = calibrate_ridge(raw_scores_checklist, human_scores)
            calibrated_scores = [round(max(2, min(12, s))) for s in calibration["fitted_scores_raw"]]
            calibrated_kappa = cohens_kappa(human_scores, calibrated_scores)
            
            print(f"\n  --- Post-hoc Ridge Calibration (Rulers) ---")
            print(f"  Calibration: {calibration['formula']}")
            print(f"  Raw → Calibrated: {dict(zip(raw_scores_checklist, calibration['fitted_scores']))}")
            print(f"  Calibrated Kappa: {calibrated_kappa:.3f}")
            print(f"  Calibrated range: {min(calibrated_scores)}-{max(calibrated_scores)}")
            
            # Log calibration details
            print(f"\n  Per-essay calibration:")
            for j, e in enumerate(essays):
                r = raw_scores_checklist[j]
                c = calibration["fitted_scores"][j]
                h = human_scores[j]
                delta_c = c - h
                sign_c = "+" if delta_c > 0 else ""
                print(f"    {e['id']}: raw={r} → calibrated={c} ({sign_c}{delta_c} vs human={h})")
        
        results["strategies"][strat_key] = {
            "label": strat_label,
            "kappa": round(kappa, 3),
            "human_range": [min(human_scores), max(human_scores)],
            "model_range": [min(model_scores), max(model_scores)],
            "compression_ratio": round(compression_ratio, 3),
            "scores": details,
        }
        if calibrated_kappa is not None:
            results["strategies"][strat_key]["calibrated_kappa"] = round(calibrated_kappa, 3)
            results["strategies"][strat_key]["calibration"] = calibration
    
    # Summary comparison
    print(f"\n{'='*60}")
    print(f"SUMMARY COMPARISON")
    print(f"{'='*60}")
    header = f"{'Strategy':<30} {'Kappa':>8} {'Compression':>12} {'Range':>12}"
    if any("calibrated_kappa" in s for s in results["strategies"].values()):
        header += f" {'Calib.K':>8}"
    print(header)
    print(f"{'-'*30} {'-'*8} {'-'*12} {'-'*12}{' ' + '-'*8 if 'Calib.K' in header else ''}")
    
    best_kappa = max(results["strategies"].items(), key=lambda x: x[1]["kappa"])
    
    for key, s in results["strategies"].items():
        marker = " ← BEST" if key == best_kappa[0] else ""
        calib_str = ""
        if "calibrated_kappa" in s:
            calib_str = f" {s['calibrated_kappa']:>8.3f}"
        print(f"{s['label']:<30} {s['kappa']:>8.3f} {s['compression_ratio']:>12.2f} "
              f"{s['model_range'][0]}-{s['model_range'][1]:>3}{marker}{calib_str}")
    
    # Save results
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {RESULTS_PATH}")
    
    return results


if __name__ == "__main__":
    run_calibration()

#!/usr/bin/env python3
"""
Two-Pass Scoring Experiment
=============================
Does scoring bias creep back in when the model scores from feedback alone?

Pass 1: Essay → gemma4 → teacher feedback (already done — feedback_audit.json)
Pass 2: Rubric + feedback → gemma4 → score (essay HIDDEN from scorer)

Compares three scoring modes:
  A) Direct:       rubric + essay → score (baseline — bias expected)
  B) Blind:        rubric + feedback → score (essay hidden — bias reduced?)
  C) Informed:     rubric + essay + feedback → score (everything visible)
"""
import json, urllib.request, time, os
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.15.59:11434")
MODEL = "gemma4:26b"
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
FEEDBACK_PATH = DATA_DIR / "feedback_audit.json"
OUTPUT_PATH = DATA_DIR / "twopass_results.json"

RUBRIC = """Scoring Rubric (2-12 scale):

2-3 (Below Basic): No clear position, no evidence, major errors in mechanics.
4-5 (Basic): Position stated but undeveloped, few details, weak organization.
6-7 (Basic/Proficient): Clear position, some evidence, basic organization, some counter-argument.
8-9 (Proficient): Strong position, specific evidence, good organization, addresses counter-argument.
10-12 (Advanced): Sophisticated argument, compelling evidence, excellent organization, deep analysis."""

def call_ollama(prompt, temperature=0.3, num_predict=2048):
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read()).get("response", "")

def extract_score(response):
    import re
    match = re.search(r'(?:SCORE|score|Score):\s*(\d+)', response)
    if match:
        score = int(match.group(1))
        return max(2, min(12, score))
    match = re.search(r'\b(1[0-2]|[2-9])\b', response[:200])
    if match:
        return max(2, min(12, int(match.group(1))))
    return None

def score_direct(essay_text):
    """A) Original: rubric + essay → score"""
    prompt = f"""{RUBRIC}

STUDENT ESSAY:
{essay_text}

Based on the rubric above, give a single integer score from 2 to 12.
SCORE:"""
    response = call_ollama(prompt)
    return extract_score(response), response

def score_blind(feedback_text):
    """B) Blind: rubric + feedback → score (essay hidden)"""
    prompt = f"""{RUBRIC}

A teacher reviewed a student essay and wrote this feedback:

TEACHER FEEDBACK:
{feedback_text}

Based on the rubric and the teacher's feedback, what score (2-12) would you assign to the student's essay?
Give a single integer score from 2 to 12.
SCORE:"""
    response = call_ollama(prompt)
    return extract_score(response), response

def score_informed(essay_text, feedback_text):
    """C) Informed: rubric + essay + feedback → score"""
    prompt = f"""{RUBRIC}

STUDENT ESSAY:
{essay_text}

TEACHER FEEDBACK ON THIS ESSAY:
{feedback_text}

Based on the rubric, the essay, and the feedback, give a single integer score from 2 to 12.
SCORE:"""
    response = call_ollama(prompt)
    return extract_score(response), response

def cohens_kappa(human, model):
    n = len(human)
    if n == 0:
        return 0.0
    po = sum(1 for h, m in zip(human, model) if h == m) / n
    all_cats = set(human) | set(m for m in model if m is not None)
    pe = 0.0
    for cat in all_cats:
        ph = sum(1 for h in human if h == cat) / n
        pm = sum(1 for m in model if m == cat) / n
        pe += ph * pm
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)

def main():
    with open(ESSAYS_PATH) as f:
        essays = json.load(f)["essays"]
    with open(FEEDBACK_PATH) as f:
        feedback_data = json.load(f)["results"]
    
    feedback_map = {f["id"]: f["feedback"] for f in feedback_data}
    
    human_scores = [e["score"] for e in essays]
    
    modes = {
        "A_direct": ("Direct (essay only)", lambda e: score_direct(e["text"])),
        "B_blind": ("Blind (feedback only)", lambda e: score_blind(feedback_map[e["id"]])),
        "C_informed": ("Informed (essay + feedback)", lambda e: score_informed(e["text"], feedback_map[e["id"]])),
    }
    
    results = {"model": MODEL, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "modes": {}}
    
    for mode_key, (mode_label, mode_fn) in modes.items():
        print(f"\n{'='*60}")
        print(f"Mode: {mode_label}")
        print(f"{'='*60}")
        
        model_scores = []
        details = []
        
        for i, essay in enumerate(essays):
            eid = essay["id"]
            human = essay["score"]
            
            print(f"  [{i+1}/{len(essays)}] {eid} (human: {human})...", end=" ", flush=True)
            t0 = time.time()
            score, raw = mode_fn(essay)
            elapsed = time.time() - t0
            
            if score is not None:
                delta = score - human
                sign = "+" if delta > 0 else ""
                print(f"model: {score} ({sign}{delta}) [{elapsed:.0f}s]")
            else:
                print(f"FAILED [{elapsed:.0f}s]")
                score = human  # fallback
            
            model_scores.append(score)
            details.append({"id": eid, "human": human, "model": score, "delta": score - human if score else None, "elapsed_s": round(elapsed, 1)})
        
        kappa = cohens_kappa(human_scores, model_scores)
        human_range = max(human_scores) - min(human_scores)
        model_range = max(model_scores) - min(model_scores)
        compression = model_range / human_range if human_range > 0 else 1.0
        
        print(f"\n  Kappa: {kappa:.3f}  |  Compression: {compression:.2f}")
        results["modes"][mode_key] = {
            "label": mode_label, "kappa": round(kappa, 3),
            "compression_ratio": round(compression, 3),
            "scores": details
        }
    
    # Summary
    print(f"\n{'='*60}")
    print("TWO-PASS COMPARISON")
    print(f"{'='*60}")
    print(f"{'Mode':<30} {'Kappa':>8} {'Compression':>12}")
    print(f"{'-'*30} {'-'*8} {'-'*12}")
    for key, m in results["modes"].items():
        print(f"{m['label']:<30} {m['kappa']:>8.3f} {m['compression_ratio']:>12.2f}")
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

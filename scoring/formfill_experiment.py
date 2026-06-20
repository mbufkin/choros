#!/usr/bin/env python3
"""
Form-Fill Scoring Experiment
=============================
Model fills out a structured Markdown rubric form (checkboxes + notes).
Python parses the filled form and computes the score — the model never
produces a number. If bias exists here, it's in what the model checks,
not in a score it's unwilling to give.
"""
import json, urllib.request, time, os, re
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.15.59:11434")
MODEL = "gemma4:26b"
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
OUTPUT_PATH = DATA_DIR / "formfill_results.json"

RUBRIC_FORM = """## Essay Rubric — Uniform Debate

Read the student essay below. For each criterion, mark [x] if the essay meets it.
Leave it [ ] if it does not. Be strict — only check if clearly demonstrated.

### Claim & Position
- [ ] States a clear position on school uniforms
- [ ] Position is maintained consistently

### Evidence & Support
- [ ] Provides at least one specific reason
- [ ] Provides at least one concrete example
- [ ] Uses data, statistics, or cited evidence

### Organization
- [ ] Has a recognizable introduction
- [ ] Body paragraphs develop the argument
- [ ] Has a conclusion that wraps up the position

### Counter-Argument
- [ ] Mentions or acknowledges an opposing viewpoint
- [ ] Responds to or rebuts the opposing view

### Mechanics
- [ ] Spelling is mostly correct
- [ ] Grammar and sentence structure are mostly correct
- [ ] Capitalization and punctuation are standard

### Notes (optional)
<!-- Write any observations here. What did the student do well? What needs work? -->

STUDENT ESSAY:
{essay}

Fill out the rubric above by marking [x] for criteria the essay meets."""

def call_ollama(prompt):
    payload = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2048}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read()).get("response", "")

def parse_form(filled_form):
    """Count checked boxes in the filled form."""
    # Count [x] or [X] markers
    checked = len(re.findall(r'-\s*\[[xX]\]', filled_form))
    # Count unchecked for reference
    unchecked = len(re.findall(r'-\s*\[\s\]', filled_form))
    total_criteria = checked + unchecked
    
    # Extract notes section
    notes_match = re.search(r'### Notes.*?\n(.*?)(?:\n\n|---|\Z)', filled_form, re.DOTALL)
    notes = notes_match.group(1).strip() if notes_match else ""
    
    return {
        "checked": checked,
        "unchecked": unchecked,
        "total_criteria": total_criteria,
        "score_pct": round(checked / max(total_criteria, 1) * 100, 1),
        "notes": notes[:500]
    }

def main():
    with open(ESSAYS_PATH) as f:
        essays = json.load(f)["essays"]
    
    results = []
    
    for i, essay in enumerate(essays):
        eid = essay["id"]
        human = essay["score"]
        expected_tier = human / 12  # what fraction of criteria should be checked
        
        print(f"[{i+1}/{len(essays)}] {eid} (human: {human})...", end=" ", flush=True)
        t0 = time.time()
        
        prompt = RUBRIC_FORM.format(essay=essay["text"])
        filled = call_ollama(prompt)
        parsed = parse_form(filled)
        
        elapsed = time.time() - t0
        expected_checks = round(expected_tier * parsed["total_criteria"])
        
        print(f"{parsed['checked']}/{parsed['total_criteria']} checks "
              f"(expect ~{expected_checks}) [{elapsed:.0f}s]")
        
        results.append({
            "id": eid,
            "human_score": human,
            "level": essay["level"],
            "checked": parsed["checked"],
            "unchecked": parsed["unchecked"],
            "total_criteria": parsed["total_criteria"],
            "score_pct": parsed["score_pct"],
            "expected_checks": expected_checks,
            "notes": parsed["notes"],
            "elapsed_s": round(elapsed, 1)
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("FORM-FILL RESULTS")
    print(f"{'='*60}")
    print(f"{'Essay':<25} {'Human':>6} {'Checks':>8} {'Expected':>9} {'Pct':>6}")
    print(f"{'-'*25} {'-'*6} {'-'*8} {'-'*9} {'-'*6}")
    for r in results:
        print(f"{r['id']:<25} {r['human_score']:>6} {r['checked']:>4}/{r['total_criteria']:<3} {r['expected_checks']:>9} {r['score_pct']:>5.0f}%")
    
    output = {"model": MODEL, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": results}
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Choros Feedback Audit — gemma4:26b teacher-style feedback on ASAP essays.
No scoring. Just feedback. Then we analyze: substantive or generic?
"""
import json, urllib.request, time, os, sys
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.15.59:11434")
MODEL = "gemma4:26b"
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
OUTPUT_PATH = DATA_DIR / "feedback_audit.json"

PROMPT = """You are a classroom teacher providing feedback on a student essay. The writing prompt was:
"Explain whether students should be required to wear uniforms."

Read the student's essay below and write the feedback you would give them. 

Rules:
- Write in plain English, like you're talking to the student
- Point out specific strengths (quote the essay if helpful)
- Point out specific weaknesses or things to improve
- Be honest — don't praise if there's nothing to praise
- If the essay is weak, say what's missing and how to fix it
- No scores, no grades, no rubrics — just feedback

ESSAY:
{essay}

FEEDBACK:"""

def call_ollama(prompt):
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read()).get("response", "")

def main():
    with open(ESSAYS_PATH) as f:
        essays = json.load(f)["essays"]
    
    results = []
    
    for i, essay in enumerate(essays):
        eid = essay["id"]
        human_score = essay["score"]
        level = essay["level"]
        
        print(f"[{i+1}/{len(essays)}] {eid} ({level}, human: {human_score})...", end=" ", flush=True)
        t0 = time.time()
        
        prompt = PROMPT.format(essay=essay["text"])
        feedback = call_ollama(prompt)
        
        elapsed = time.time() - t0
        
        word_count = len(feedback.split())
        print(f"{word_count} words [{elapsed:.0f}s]")
        print(f"  {feedback[:120]}...")
        
        results.append({
            "id": eid,
            "human_score": human_score,
            "level": level,
            "word_count": word_count,
            "feedback": feedback,
            "elapsed_s": round(elapsed, 1)
        })
    
    output = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        print(f"{r['id']} ({r['level']}, human={r['human_score']}): {r['word_count']} words")
        print(f"  → {r['feedback'][:200]}")
        print()

if __name__ == "__main__":
    main()

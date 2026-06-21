#!/usr/bin/env python3
"""Strategy D: raw completions + think-stripping for qwen3.6"""
import os, json, time, re, sys
sys.path.insert(0, '/home/mbufkin/choros/scoring')
os.environ['CHOROS_BACKEND'] = 'llamacpp'
os.environ['LLAMACPP_URL'] = 'http://100.85.15.59:8080'

from calibrate import llamacpp_generate
from sklearn.metrics import cohen_kappa_score

with open('/home/mbufkin/choros/scoring/guardrails/essays.json') as f:
    essays = json.load(f)['essays']

CHECKLIST_CRITERIA = [
    {"id": "CLAIM", "label": "Position & Claim", "question": "Does the essay state a clear position on school uniforms?", "evidence_type": "local_quote"},
    {"id": "EVIDENCE_COUNT", "label": "Evidence Count", "question": "How many distinct reasons or examples support the position?", "evidence_type": "span_level"},
    {"id": "EVIDENCE_QUALITY", "label": "Evidence Quality", "question": "Are the reasons/examples specific and concrete?", "evidence_type": "local_quote"},
    {"id": "COUNTER", "label": "Counterargument", "question": "Does the essay acknowledge an opposing viewpoint?", "evidence_type": "local_quote"},
    {"id": "STRUCTURE", "label": "Structure", "question": "Does the essay have intro, body, conclusion?", "evidence_type": "global"},
    {"id": "GRAMMAR", "label": "Grammar & Conventions", "question": "Is the writing mostly free of errors?", "evidence_type": "global"},
    {"id": "DEPTH", "label": "Depth & Nuance", "question": "Does the essay show nuanced thinking?", "evidence_type": "global"},
]

def build_prompt(essay_text):
    criteria_lines = ""
    for i, c in enumerate(CHECKLIST_CRITERIA, 1):
        criteria_lines += f"{i}. **{c['label']}** — {c['question']}\n   [ ] Not met   [/] Partial   [x] Met\n\n"
    
    return f"""You are evaluating a student essay against a structured checklist.
For each criterion, choose ONE: [x] Met, [/] Partial, or [ ] Not met.
Then provide a short verbatim quote from the essay as evidence.

CRITICAL RULES:
- Evidence MUST be copied VERBATIM from the essay — do NOT paraphrase
- If you check [ ] Not met, write "none" as the evidence
- If you check [/] Partial, quote the partial evidence you found

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
      "evidence": "verbatim quote"
    }},
    ...all 7 criteria...
  ]
}}
```
Where "check" is "x" (met), "/" (partial), or " " (not met)."""


def strip_thinking(text):
    """Remove <think>...</think> blocks from qwen3.6 output."""
    return re.sub(r'<think>[\s\S]*?</think>', '', text).strip()


human_scores = []
model_scores = []
timings = []

print("QWEN3.6 CUDA RAW + think-strip — STRATEGY D\n")

for e in essays:
    essay_text = e['text']
    prompt = build_prompt(essay_text)
    
    start = time.time()
    response = llamacpp_generate(prompt, temperature=0.2, n_predict=8192, timeout=180)
    elapsed = time.time() - start
    
    # Strip thinking tags
    clean = strip_thinking(response)
    
    # Parse JSON
    json_match = re.search(r'\{[\s\S]*\}', clean)
    if not json_match:
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', clean)
    
    score = 0
    parsed = False
    if json_match:
        try:
            if json_match.lastindex:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(json_match.group(0))
            criteria = data.get('criteria', [])
            for c_item in criteria:
                check = c_item.get('check', ' ').strip()
                if check == 'x':
                    score += 2
                elif check == '/':
                    score += 1
            parsed = True
        except json.JSONDecodeError as ex:
            pass
    
    human = e['score']
    human_scores.append(human)
    model_scores.append(score)
    timings.append(elapsed)
    
    status = "✓" if parsed else "✗ (parse fail)"
    print(f"{e['id']}: {score} (human={human}) | {elapsed:.1f}s {status}")

kappa = cohen_kappa_score(human_scores, model_scores)
avg_t = sum(timings)/len(timings)

print(f"\n{'='*60}")
print(f"qwen3.6:35b CUDA — raw + think-strip")
print(f"Kappa: {kappa:.3f}")
print(f"Avg: {avg_t:.1f}s/essay")
print(f"Human:  {human_scores}")
print(f"Model:  {model_scores}")
print(f"CPU Kappa was: 0.545 with Ollama's GGUF")
print(f"Note: unsloth GGUF may differ from Ollama GGUF")

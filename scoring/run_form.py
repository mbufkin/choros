#!/usr/bin/env python3
"""Run the form-fill checklist pipeline against any model.

Supports multiple backends via environment variables:
  CHOROS_BACKEND=llamacpp  → local Lenovo CUDA llama.cpp server
  CHOROS_BACKEND=nvidia    → NVIDIA NIM free tier API
  CHOROS_BACKEND=ollama    → Ollama (deprecated)

For NVIDIA NIM: set NVIDIA_API_KEY environment variable.

Usage:
  python3 run_form.py [model_name] [output_path]
  python3 run_form.py gemma4-26b
  CHOROS_BACKEND=nvidia python3 run_form.py deepseek-ai/deepseek-v4-pro
"""
import json, sys, time, re, os
sys.path.insert(0, '.')

# Import from calibrate
from calibrate import (
    generate, generate_chat, CHECKLIST_CRITERIA,
    validate_evidence, cohens_kappa, calibrate_ridge,
    ESSAYS_PATH, BACKEND
)

# NIM support
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def nvidia_generate(system_prompt, user_prompt, temperature=0.2, max_tokens=4096, timeout=180):
    """Call NVIDIA NIM API chat completions."""
    import urllib.request, urllib.error

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        NVIDIA_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR: {e}]"

# ── Config ──
MODEL = sys.argv[1] if len(sys.argv) > 1 else None
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else (
    f"/tmp/form_{MODEL.replace(':', '_').replace('/', '_')}.txt"
    if MODEL else "/tmp/form_output.txt"
)

with open(ESSAYS_PATH) as f:
    data = json.load(f)

essays = data["essays"]
human_scores = [e["score"] for e in essays]
raw_scores, model_scores = [], []

out = open(OUTPUT, "w")
def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log(f"{MODEL or 'default'} — form-fill checklist (backend={BACKEND})")
log(f"{'='*60}")

for i, essay in enumerate(essays):
    eid, human, text = essay["id"], essay["score"], essay["text"]
    log(f"\n[{i+1}/5] {eid} (human={human})")
    t0 = time.time()

    # Build the checklist prompt
    criteria_lines = ""
    for j, c in enumerate(CHECKLIST_CRITERIA, 1):
        criteria_lines += (
            f"{j}. **{c['label']}** — {c['question']}\n"
            f"   [ ] Not met   [/] Partial   [x] Met\n\n"
        )

    user_prompt = f"""You are evaluating a student essay against a structured checklist.
For each criterion, choose ONE: [x] Met, [/] Partial, or [ ] Not met.
Then provide a short verbatim quote from the essay as evidence.

CRITICAL RULES:
- Evidence MUST be copied VERBATIM from the essay
- If you check [ ] Not met, write "none" as the evidence
- Quote enough context (1-2 sentences)

ESSAY:
---
{text}
---

CHECKLIST:
{criteria_lines}

Respond in valid JSON ONLY:
```json
{{
  "criteria": [
    {{"id":"CLAIM","check":"x","evidence":"quote"}},
    {{"id":"EVIDENCE_COUNT","check":"/","evidence":"..."}},
    {{"id":"EVIDENCE_QUALITY","check":" ","evidence":"none"}},
    {{"id":"COUNTER","check":" ","evidence":"none"}},
    {{"id":"STRUCTURE","check":" ","evidence":"none"}},
    {{"id":"GRAMMAR","check":"/","evidence":"..."}},
    {{"id":"DEPTH","check":" ","evidence":"none"}}
  ]
}}
```"""

    # Route to appropriate backend
    system_prompt = "You are an expert essay grader."
    if BACKEND == "nvidia":
        response = nvidia_generate(system_prompt, user_prompt,
                                   temperature=0.2, max_tokens=4096, timeout=180)
    elif BACKEND == "llamacpp":
        # Use chat endpoint for better model template handling
        response = generate_chat(system_prompt, user_prompt,
                                temperature=0.2, num_predict=4096, timeout=180)
        # Strip think tags if using raw completions fallback
        response = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
    else:
        # Ollama backend — use raw completions with full prompt
        response = generate(user_prompt, temperature=0.2, num_predict=8192, timeout=180)

    elapsed = time.time() - t0

    # Parse JSON response
    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if not json_match:
        log(f"  FAILED parse [{elapsed:.0f}s]")
        log(f"  Raw: {response[:200]}")
        raw_scores.append(0); model_scores.append(human)
        continue

    try:
        parsed = json.loads(json_match.group(0) if json_match.lastindex is None
                           else json_match.group(1))
    except json.JSONDecodeError:
        log(f"  FAILED json [{elapsed:.0f}s]")
        log(f"  Raw: {response[:200]}")
        raw_scores.append(0); model_scores.append(human)
        continue

    criteria_results = parsed.get("criteria", [])
    if len(criteria_results) != 7:
        log(f"  FAILED count={len(criteria_results)} [{elapsed:.0f}s]")
        raw_scores.append(0); model_scores.append(human)
        continue

    total = 0; vcount = 0
    for j, cr in enumerate(criteria_results):
        expected = CHECKLIST_CRITERIA[j]
        check = cr.get("check", " ").strip()
        quote = cr.get("evidence", "").strip('"').strip()
        score = 2 if check == "x" else 1 if check == "/" else 0
        valid = validate_evidence(text, quote, expected["evidence_type"])
        if valid: vcount += 1
        total += score
        box = {"x": "[x]", "/": "[/]", " ": "[ ]"}.get(check, "?")
        vmark = "v" if valid else "X"
        log(f'    {vmark} {expected["id"]:<18} {box} {score}  "{quote[:80]}"')

    mapped = round(2 + (total * 10 / 14))
    log(f"  Raw: {total}/14  Mapped: {mapped}  Valid: {vcount}/7  [{elapsed:.0f}s]")
    raw_scores.append(total); model_scores.append(mapped)

kappa = cohens_kappa(human_scores, model_scores)
log(f"\n{'='*60}")
log(f"{MODEL or 'default'} Kappa: {kappa:.3f}")
log(f"Human: {human_scores}")
log(f"Boxes: {model_scores}")
log(f"Raw:   {raw_scores}")

if len(raw_scores) >= 2:
    cal = calibrate_ridge(raw_scores, human_scores)
    cal_scores = [round(max(2, min(12, s))) for s in cal["fitted_scores_raw"]]
    cal_k = cohens_kappa(human_scores, cal_scores)
    log(f"Ridge: {cal['formula']}")
    log(f"Calibrated Kappa: {cal_k:.3f}")
    for j, e in enumerate(essays):
        h = human_scores[j]
        c = cal["fitted_scores"][j]
        delta_c = c - h
        sign_c = "+" if delta_c > 0 else ""
        log(f"  {e['id']}: raw={raw_scores[j]} -> cal={c} ({sign_c}{delta_c} vs human={h})")

out.close()
print(f"\nResults saved: {OUTPUT}")

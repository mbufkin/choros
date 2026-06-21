#!/usr/bin/env python3
"""Batch grade with prompt-specific rubrics — the missing third leg.
Routes each essay to its prompt, then grades against that prompt's locked rubric.
"""
import json, sys, time, re, os
sys.path.insert(0, '.')
from calibrate import generate_chat, validate_evidence, cohens_kappa, calibrate_ridge
from asap_rubrics import detect_topic, ASAP_RUBRICS, get_rubric_for_essay

BACKEND = os.environ.get("CHOROS_BACKEND", "llamacpp")
ESSAYS_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/asap200.json"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/batch200_prompt_specific.txt"
START_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with open(ESSAYS_FILE) as f:
    data = json.load(f)

essays = data["essays"]
if START_IDX:
    essays = essays[START_IDX:]

out = open(OUTPUT, "a" if START_IDX else "w")
def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log(f"Prompt-specific batch grade — {len(essays)} essays — backend={BACKEND}")
log(f"{'='*60}")

human_scores = []
raw_scores = []

for i, essay in enumerate(essays):
    eid, human, text = essay["id"], essay["score"], essay["text"]
    actual_idx = START_IDX + i
    
    # PASS 1: Route to prompt-specific rubric
    rubric = get_rubric_for_essay(text)
    if rubric is None:
        log(f"[{actual_idx+1}/{START_IDX+len(essays)}] {eid} (human={human}) — UNROUTED, skipping")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    prompt_text = rubric["prompt"]
    criteria = rubric["criteria"]
    
    log(f"[{actual_idx+1}/{START_IDX+len(essays)}] {eid} (human={human}, {len(text.split())}w)")
    t0 = time.time()
    
    # Build prompt-specific checklist
    criteria_lines = ""
    for j, c in enumerate(criteria, 1):
        criteria_lines += (
            f"{j}. **{c['label']}** — {c['question']}\n"
            f"   [ ] Not met   [/] Partial   [x] Met\n\n"
        )
    
    user_prompt = f"""A student was given the following writing prompt:

WRITING PROMPT:
---
{prompt_text}
---

The student wrote this essay in response:

STUDENT ESSAY:
---
{text}
---

You are grading this essay against a rubric designed specifically for this prompt.
For each criterion, choose ONE: [x] Met, [/] Partial, or [ ] Not met.
Then provide a short verbatim quote from the STUDENT ESSAY as evidence.

CRITICAL RULES:
- Evidence MUST be copied VERBATIM from the student essay (no paraphrasing)
- If you check [ ] Not met, write "none" as the evidence

NON-COMPENSATION RULES — DO NOT REWARD SURFACE FEATURES:
- [ ] is the DEFAULT. [x] and [/] must be EARNED with real substance.
- Good grammar or polite tone do NOT earn [x] if the argument/content is weak.
- [x] requires CONCRETE, SPECIFIC content relevant to THIS PROMPT.
- Do NOT give partial credit ([/]) to be polite. Use [ ] when the criterion is truly absent.

FORMAT: Respond with JSON ONLY. Start with ```json and end with ```.

RUBRIC:
{criteria_lines}

Respond in valid JSON:
```json
{{
  "criteria": [
    {{"id":"{criteria[0]['id']}","check":"x","evidence":"quote"}},
    {{"id":"{criteria[1]['id']}","check":"/","evidence":"..."}},
    {{"id":"{criteria[2]['id']}","check":" ","evidence":"none"}},
    {{"id":"{criteria[3]['id']}","check":" ","evidence":"none"}},
    {{"id":"{criteria[4]['id']}","check":" ","evidence":"none"}},
    {{"id":"{criteria[5]['id']}","check":"/","evidence":"..."}},
    {{"id":"{criteria[6]['id']}","check":" ","evidence":"none"}}
  ]
}}
```"""

    system_prompt = "You are an expert essay grader. Grade against the specific prompt and rubric provided."
    response = generate_chat(system_prompt, user_prompt,
                            temperature=0.2, num_predict=32768, timeout=600)
    response = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()
    elapsed = time.time() - t0
    
    # Parse JSON
    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if not json_match:
        log(f"  FAILED parse [{elapsed:.0f}s] raw[0]")
        log(f"  Raw: {response[:200]}")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    try:
        parsed = json.loads(json_match.group(0) if json_match.lastindex is None
                           else json_match.group(1))
    except json.JSONDecodeError:
        log(f"  FAILED json [{elapsed:.0f}s] raw[0]")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    criteria_results = parsed.get("criteria", [])
    if len(criteria_results) != 7:
        log(f"  FAILED count={len(criteria_results)} [{elapsed:.0f}s] raw[0]")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    total = 0; vcount = 0
    for j, cr in enumerate(criteria_results):
        expected = criteria[j]
        check = cr.get("check", " ").strip()
        quote = cr.get("evidence", "").strip('"').strip()
        score = 2 if check == "x" else 1 if check == "/" else 0
        valid = validate_evidence(text, quote, expected["evidence_type"])
        if valid: vcount += 1
        total += score
        box = {"x": "[x]", "/": "[/]", " ": "[ ]"}.get(check, "?")
        vmark = "v" if valid else "X"
        log(f'    {vmark} {expected["id"]:<22} {box} {score}  "{quote[:80]}"')
    
    log(f"  Raw: {total}/14  Valid: {vcount}/7  [{elapsed:.0f}s]")
    human_scores.append(human)
    raw_scores.append(total)

# Final stats
log(f"\n{'='*60}")
log(f"Complete: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Filter to essays with valid scores (raw > 0 or explicitly scored)
valid_idx = [j for j, r in enumerate(raw_scores) if r > 0]
valid_raw = [raw_scores[j] for j in valid_idx]
valid_human = [human_scores[j] for j in valid_idx]
failed = len(raw_scores) - len(valid_idx)

log(f"Valid: {len(valid_idx)}/{len(raw_scores)} ({failed} failed/parse errors)")

if len(valid_idx) >= 10:
    mapped = [round(1 + (r * 5 / 14)) for r in valid_raw]
    k = cohens_kappa(valid_human, mapped)
    log(f"Direct-mapped Kappa: {k:.3f}")
    
    cal = calibrate_ridge(valid_raw, valid_human)
    cal_scores = [round(max(1, min(6, s))) for s in cal["fitted_scores_raw"]]
    cal_k = cohens_kappa(valid_human, cal_scores)
    log(f"Calibrated Kappa: {cal_k:.3f}")
    
    try:
        from sklearn.metrics import cohen_kappa_score
        qwk = cohen_kappa_score(valid_human, cal_scores, weights='quadratic')
        log(f"Quadratic Weighted Kappa: {qwk:.3f}")
    except:
        pass
    
    # Per-score breakdown
    from collections import defaultdict
    by_score = defaultdict(list)
    for j in valid_idx:
        by_score[valid_human[j]].append((raw_scores[j], cal_scores[valid_idx.index(j)]))
    
    log(f"\nPer-score accuracy:")
    for s in sorted(by_score):
        pairs = by_score[s]
        deltas = [cs - s for _, cs in pairs]
        avg_d = sum(deltas)/len(deltas)
        log(f"  score={s} (n={len(pairs)}): mean delta={avg_d:+.2f}")

out.close()
print(f"\nResults: {OUTPUT}")

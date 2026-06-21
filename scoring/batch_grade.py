#!/usr/bin/env python3
"""Batch grade 200 ASAP essays with generic non-comp form-fill rubric.
Uses gemma4-26b via CUDA llama.cpp server. ~8 hour run.
"""
import json, sys, time, re, os, csv
sys.path.insert(0, '.')

from calibrate import generate_chat, validate_evidence, cohens_kappa, calibrate_ridge

# ── Generic rubric (prompt-agnostic) ──
GENERIC_CRITERIA = [
    {"id": "THESIS", "label": "Thesis & Position",
     "question": "Does the essay state a clear, specific position or argument?",
     "evidence_type": "local_quote"},
    {"id": "EVIDENCE_COUNT", "label": "Support Count",
     "question": "How many distinct reasons, examples, or pieces of evidence support the position?",
     "evidence_type": "span_level"},
    {"id": "EVIDENCE_QUALITY", "label": "Support Quality",
     "question": "Are the reasons/examples specific and concrete (not vague generalities)?",
     "evidence_type": "local_quote"},
    {"id": "COUNTER", "label": "Counterargument",
     "question": "Does the essay acknowledge or address opposing views or limitations?",
     "evidence_type": "local_quote"},
    {"id": "ORGANIZATION", "label": "Organization",
     "question": "Is the essay logically organized with clear structure (intro/body/conclusion)?",
     "evidence_type": "span_level"},
    {"id": "MECHANICS", "label": "Language Mechanics",
     "question": "Is grammar, spelling, and punctuation generally correct?",
     "evidence_type": "local_quote"},
    {"id": "DEPTH", "label": "Depth & Sophistication",
     "question": "Does the reasoning go beyond surface-level to show nuance or insight?",
     "evidence_type": "local_quote"},
]

# ── Config ──
LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")
ESSAYS_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/asap200.json"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/batch200_results.txt"
START_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with open(ESSAYS_FILE) as f:
    data = json.load(f)

essays = data["essays"]
if START_IDX:
    essays = essays[START_IDX:]
    print(f"Starting from essay {START_IDX} (remaining: {len(essays)})")

human_scores = [e["score"] for e in essays]  # 1-6 scale
raw_scores = []

out = open(OUTPUT, "a" if START_IDX else "w")
def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log(f"Batch grade — {len(essays)} essays — generic non-comp form-fill")
log(f"{'='*60}")
log(f"Start: {time.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"")

for i, essay in enumerate(essays):
    eid = essay["id"]
    human = essay["score"]
    text = essay["text"]
    actual_idx = START_IDX + i

    log(f"[{actual_idx+1}/{START_IDX+len(essays)}] {eid} (human={human}, {len(text.split())} words)")
    t0 = time.time()

    # Build generic checklist
    criteria_lines = ""
    for j, c in enumerate(GENERIC_CRITERIA, 1):
        criteria_lines += (
            f"{j}. **{c['label']}** — {c['question']}\n"
            f"   [ ] Not met   [/] Partial   [x] Met\n\n"
        )

    system_prompt = "You are an expert essay evaluator."
    user_prompt = f"""You are evaluating a student essay against a structured checklist.
For each criterion, choose ONE: [x] Met, [/] Partial, or [ ] Not met.
Then provide a short verbatim quote from the essay as evidence.

CRITICAL RULES — YOU MUST FOLLOW THESE:
- Evidence MUST be copied VERBATIM from the essay (no paraphrasing)
- If you check [ ] Not met, write "none" as the evidence
- Quote enough context (1-2 sentences)

NON-COMPENSATION RULES — DO NOT REWARD SURFACE FEATURES:
- [ ] is the DEFAULT. [x] and [/] must be EARNED with real substance.
- Good grammar, polite tone, or formal structure do NOT earn [x] if the argument is weak.
- [x] requires CONCRETE, SPECIFIC content — not just "the essay mentions a topic."
- Do NOT give partial credit ([/]) to be polite. Use [ ] when the criterion is truly absent.

FORMAT: Respond with JSON ONLY. No introduction, no explanation. Start with ```json and end with ```.

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
    {{"id":"THESIS","check":"x","evidence":"quote"}},
    {{"id":"EVIDENCE_COUNT","check":"/","evidence":"..."}},
    {{"id":"EVIDENCE_QUALITY","check":" ","evidence":"none"}},
    {{"id":"COUNTER","check":" ","evidence":"none"}},
    {{"id":"ORGANIZATION","check":" ","evidence":"none"}},
    {{"id":"MECHANICS","check":"/","evidence":"..."}},
    {{"id":"DEPTH","check":" ","evidence":"none"}}
  ]
}}
```"""

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
        raw_scores.append(0)
        continue

    try:
        parsed = json.loads(json_match.group(0) if json_match.lastindex is None
                           else json_match.group(1))
    except json.JSONDecodeError:
        log(f"  FAILED json [{elapsed:.0f}s] raw[0]")
        raw_scores.append(0)
        continue

    criteria_results = parsed.get("criteria", [])
    if len(criteria_results) != 7:
        log(f"  FAILED count={len(criteria_results)} [{elapsed:.0f}s] raw[0]")
        raw_scores.append(0)
        continue

    total = 0; vcount = 0
    for j, cr in enumerate(criteria_results):
        expected = GENERIC_CRITERIA[j]
        check = cr.get("check", " ").strip()
        quote = cr.get("evidence", "").strip('"').strip()
        score = 2 if check == "x" else 1 if check == "/" else 0
        valid = validate_evidence(text, quote, expected["evidence_type"])
        if valid: vcount += 1
        total += score
        box = {"x": "[x]", "/": "[/]", " ": "[ ]"}.get(check, "?")
        vmark = "v" if valid else "X"
        log(f'    {vmark} {expected["id"]:<18} {box} {score}  "{quote[:80]}"')

    log(f"  Raw: {total}/14  Valid: {vcount}/7  [{elapsed:.0f}s]")
    raw_scores.append(total)

# ── Final stats ──
log(f"\n{'='*60}")
log(f"Complete: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Filter failures
valid_indices = [j for j, (r, h) in enumerate(zip(raw_scores, human_scores)) if r > 0]
valid_raw = [raw_scores[j] for j in valid_indices]
valid_human = [human_scores[j] for j in valid_indices]

log(f"Valid essays: {len(valid_indices)}/{len(essays)} ({len(essays)-len(valid_indices)} failed)")

if len(valid_indices) >= 10:
    # Direct mapping: raw 0-14 → 1-6
    mapped = [round(1 + (r * 5 / 14)) for r in valid_raw]
    kappa = cohens_kappa(valid_human, mapped)
    log(f"Direct-mapped Kappa: {kappa:.3f}")

    # Ridge calibration
    cal = calibrate_ridge(valid_raw, valid_human)
    cal_scores = [round(max(1, min(6, s))) for s in cal["fitted_scores_raw"]]
    cal_k = cohens_kappa(valid_human, cal_scores)
    log(f"Ridge: {cal['formula']}")
    log(f"Calibrated Kappa: {cal_k:.3f}")

    # Quadratic Weighted Kappa (QWK)
    try:
        from sklearn.metrics import cohen_kappa_score
        qwk = cohen_kappa_score(valid_human, cal_scores, weights='quadratic')
        log(f"Quadratic Weighted Kappa: {qwk:.3f}")
    except ImportError:
        log("QWK: sklearn not available")

    # Per-score breakdown
    log(f"\nPer-score accuracy:")
    for s in sorted(set(valid_human)):
        idxs = [j for j, h in enumerate(valid_human) if h == s]
        deltas = [cal_scores[j] - valid_human[j] for j in idxs]
        avg_delta = sum(deltas) / len(deltas)
        log(f"  score={s} (n={len(idxs)}): mean delta={avg_delta:+.2f}, range=[{min(deltas):+.0f},{max(deltas):+.0f}]")

out.close()
print(f"\nResults saved: {OUTPUT}")

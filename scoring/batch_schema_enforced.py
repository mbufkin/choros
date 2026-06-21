#!/usr/bin/env python3
"""Schema-enforced batch grader — JSON Schema → GBNF grammar via llama.cpp.

The key insight: llama.cpp converts JSON Schema to GBNF grammars internally,
enforcing valid JSON at the token level. No more JSON parse failures, ever.

Uses /v1/completions with json_schema (NOT /v1/chat/completions) because:
  1. /v1/completions has no thinking/reasoning split — all output goes to `text`
  2. /v1/chat/completions drains tokens into reasoning_content on gemma4,
     even with thinking=False, causing empty content + finish_reason=length
"""
import json, sys, time, re, os
import urllib.request, urllib.error

sys.path.insert(0, '.')
from calibrate import validate_evidence, cohens_kappa, calibrate_ridge
from asap_rubrics import detect_topic, ASAP_RUBRICS, get_rubric_for_essay

BACKEND = os.environ.get("CHOROS_BACKEND", "llamacpp")
LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")

# ----- JSON Schema for rubric output -----
# One schema covers ALL rubrics — same structure, same 7 criteria.
RUBRIC_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "enum": ["THESIS", "EVIDENCE_COUNT", "EVIDENCE_QUALITY",
                                 "COUNTER", "ORGANIZATION", "MECHANICS", "DEPTH"]
                    },
                    "check": {"type": "string", "enum": ["x", "/", " "]},
                    "evidence": {"type": "string"}
                },
                "required": ["id", "check", "evidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["criteria"],
    "additionalProperties": False
}


def generate_schema(system_prompt: str, user_prompt: str,
                    temperature: float = 0.1,
                    n_predict: int = 32768, timeout: int = 600) -> str:
    """Call llama.cpp /v1/chat/completions WITH json_schema enforcement + thinking.
    
    Uses chat completions (not raw completions) so gemma4 can REASON before
    producing constrained output. The model generates reasoning_content first
    (unconstrained thinking), then produces content that MUST match the schema.
    max_tokens must be high enough to accommodate both phases.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    payload = json.dumps({
        "messages": messages,
        "temperature": temperature,
        "max_tokens": n_predict,
        "stream": False,
        # Let gemma4 THINK before producing constrained output
        # No chat_template_kwargs — let thinking happen naturally
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "rubric_grading",
                "schema": RUBRIC_SCHEMA,
            }
        },
    }).encode()
    
    req = urllib.request.Request(
        f"{LLAMACPP_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read())
        msg = raw["choices"][0]["message"]
        content = msg.get("content", "")
        # If thinking drained all tokens and content is empty, use reasoning as fallback
        if not content.strip():
            content = msg.get("reasoning_content", "")
        return content
    except Exception as e:
        return f"[ERROR: {e}]"


# ----- Main -----
ESSAYS_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/asap200.json"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/batch20_schema_enforced.txt"
START_IDX = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with open(ESSAYS_FILE) as f:
    data = json.load(f)

essays = data["essays"]
essays = essays[:min(20, len(essays))]

out = open(OUTPUT, "w")
def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log(f"Schema-enforced batch grade — {len(essays)} essays — backend={BACKEND}")
log(f"{'='*60}")

human_scores = []
raw_scores = []

for i, essay in enumerate(essays):
    eid, human, text = essay["id"], essay["score"], essay["text"]
    
    rubric = get_rubric_for_essay(text)
    if rubric is None:
        log(f"[{i+1}/{len(essays)}] {eid} (human={human}) — UNROUTED, skipping")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    prompt_text = rubric["prompt"]
    criteria = rubric["criteria"]
    
    log(f"[{i+1}/{len(essays)}] {eid} (human={human}, {len(text.split())}w)")
    t0 = time.time()
    
    # Build prompt-specific checklist
    criteria_lines = ""
    for j, c in enumerate(criteria, 1):
        criteria_lines += (
            f"{j}. **{c['label']}** — {c['question']}\n"
            f"   [ ] Not met   [/] Partial   [x] Met\n\n"
        )
    
    system_prompt = "You are an expert essay grader. Grade against the specific prompt and rubric provided. Think carefully about each criterion before producing your JSON output."

    prompt = f"""You are grading a student essay against a rubric designed for a specific writing prompt.

WRITING PROMPT:
---
{prompt_text}
---

STUDENT ESSAY:
---
{text}
---

RUBRIC — choose [x] Met, [/] Partial, or [ ] Not met for each criterion.
Provide a verbatim quote from the essay as evidence.
If [ ] Not met, write "none" as evidence.

CRITICAL RULES:
- Evidence MUST be copied VERBATIM from the essay (no paraphrasing)
- [ ] is the DEFAULT. [x] and [/] must be EARNED with substance.
- Good grammar or polite tone do NOT earn [x] if the argument is weak.
- [x] requires CONCRETE, SPECIFIC content relevant to THIS PROMPT.
- Do NOT give partial credit ([/]) to be polite.

{criteria_lines}

Output ONLY a JSON object with a "criteria" array containing exactly 7 items, one per criterion above.
Each item must have: "id" (use the exact IDs below), "check" (x, /, or space), "evidence" (verbatim quote or "none").
Use these exact IDs in order: THESIS, EVIDENCE_COUNT, EVIDENCE_QUALITY, COUNTER, ORGANIZATION, MECHANICS, DEPTH"""

    response = generate_schema(system_prompt, prompt, temperature=0.1)
    elapsed = time.time() - t0
    
    # Parse JSON — should ALWAYS succeed with schema enforcement
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        log(f"  FAILED json [{elapsed:.0f}s] — schema enforcement didn't work?")
        log(f"  Raw: {response[:200]}")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    criteria_results = parsed.get("criteria", [])
    if len(criteria_results) != 7:
        log(f"  FAILED count={len(criteria_results)} [{elapsed:.0f}s]")
        log(f"  Raw: {json.dumps(parsed)[:200]}")
        human_scores.append(human)
        raw_scores.append(0)
        continue
    
    total = 0; vcount = 0
    # Map criteria by ID (schema enforces order but be safe)
    criteria_map = {c["id"]: c for c in criteria}
    
    for j, cr in enumerate(criteria_results):
        cid = cr["id"]
        expected = criteria_map.get(cid, criteria[j % 7])
        check = cr.get("check", " ").strip()
        quote = cr.get("evidence", "").strip('"').strip()
        score = 2 if check == "x" else 1 if check == "/" else 0
        valid = validate_evidence(text, quote, expected["evidence_type"])
        if valid: vcount += 1
        total += score
        box = {"x": "[x]", "/": "[/]", " ": "[ ]"}.get(check, "?")
        vmark = "v" if valid else "X"
        log(f'    {vmark} {cid:<22} {box} {score}  "{quote[:80]}"')
    
    log(f"  Raw: {total}/14  Valid: {vcount}/7  [{elapsed:.0f}s]")
    human_scores.append(human)
    raw_scores.append(total)

# Final stats
log(f"\n{'='*60}")
log(f"Complete: {time.strftime('%Y-%m-%d %H:%M:%S')}")

valid_idx = [j for j, r in enumerate(raw_scores) if r > 0]
valid_raw = [raw_scores[j] for j in valid_idx]
valid_human = [human_scores[j] for j in valid_idx]
failed = len(raw_scores) - len(valid_idx)

log(f"Valid: {len(valid_idx)}/{len(raw_scores)} ({failed} failed)")

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

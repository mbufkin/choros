# JSON Schema Enforcement — Complete Findings

**2026-06-21 · Choros Project · mbufkin/choros**

---

## 1. The Motivation

The original grading pipeline had a JSON formatting problem — models produced output
that `json.loads()` couldn't parse. Even with strong prompts, models would:

- Add trailing commas in arrays
- Forget closing braces on deeply nested objects
- Insert markdown fences (```json) around the output
- Produce valid-looking JSON with wrong structure (missing keys)

**Hypothesis:** If we use llama.cpp's built-in `json_schema` field — which converts JSON
Schema to GBNF grammars and enforces them at the token level — we could eliminate JSON
parse failures entirely. The model *cannot* output invalid JSON because every token is
constrained by the grammar.

**Research backing:** llama.cpp ships with a native `json_schema` → GBNF converter
(exposed in the server via `/v1/completions`). The approach is production-grade —
no external libraries (Outlines, JSONFormer, LMQL) required.

---

## 2. Architecture: How JSON Schema Enforcement Works

```
User prompt + Rubric + Essay
          ↓
   /v1/completions
   { "prompt": "...",
     "json_schema": { ... },
     "temperature": 0.1,
     "max_tokens": 2048 }
          ↓
llama.cpp converts JSON Schema → GBNF grammar
          ↓
Every token output is constrained by the grammar
Model CANNOT produce invalid JSON
          ↓
   Guaranteed-valid JSON output
```

**The schema** covers all 7 ASAP rubrics — same structure: 7 criteria objects, each with
`id` (enum of 7 values), `check` (x/✓/✗), and `evidence` (string).

---

## 3. The Three Endpoints Tested

| Endpoint | What we tried | Result |
|----------|--------------|--------|
| `/v1/chat/completions` + `response_format` + `stream: true` | Gemma4:26b on Lenovo | **Empty responses.** Streaming is incompatible with `response_format` in this llama.cpp build. |
| `/v1/chat/completions` + `response_format` + `stream: false` | Gemma4:26b on Lenovo | **Empty content.** All tokens drained into `reasoning_content` field (gemma4's thinking), `content` empty, `finish_reason=length`. The model "thinks" and then has no tokens left for the actual answer. |
| `/v1/completions` + `json_schema` | Gemma4:26b, then Qwen3.6:35b | **Valid JSON, garbage content.** `json_schema` is accepthed by completions endpoint. Thinking is disabled entirely (no `reasoning_content`). Model produces schema-compliant output that is semantically useless. |

**Why completions endpoint?** `/v1/completions` has no thinking/reasoning split — all
output goes directly to `text`. We hoped this would prevent the token-drain problem.
It does — but it introduces a worse problem: no reasoning at all.

---

## 4. Results: Gemma4:26b — Completions + JSON Schema

**Run:** 20 essays from ASAP 200-sample, lenovo llama.cpp, gemma4:26b (CUDA)
**Speed:** 7-14 seconds per essay

| Metric | Value |
|--------|-------|
| Essays with valid JSON | 17/20 (3 failed — still had parse errors!) |
| Direct-mapped Kappa | **-0.016** |
| Calibrated Kappa | **0.150** |
| Quadratic Weighted Kappa | **0.114** |

### Failure mode: Criterion duplication

When gemma4 can't think, it fills the required 7-item array by **repeating the same
criterion.** A typical output:

```
Essay with human score 2:
  EVIDENCE_QUALITY × 5  [score 2, same evidence repeated 5 times]
  THESIS × 1            [score 2]
  EVIDENCE_COUNT × 1    [score 2]
  → Raw: 14/14  Valid: 5/7
```

The schema says "7 items with these enum values" — the model satisfies the constraint
by outputting 5 EVIDENCE_QUALITY objects and 2 others. It never scores COUNTER,
ORGANIZATION, MECHANICS, or DEPTH because the grammar doesn't require *unique* criteria
IDs — it only requires 7 objects with valid `id` values.

**Fix attempted:** Added `"uniqueItems": true` to the schema. Untested — but this
wouldn't fix the underlying problem (model can't choose which criteria to score
because it can't reason about the essay).

### Why Kappa is near zero

The model can't deliberate. Without thinking, grading becomes a pattern-matching
exercise — find any sentence, quote it 7 times, assign 2. The model doesn't
*distinguish* between essays because it doesn't understand what distinguishes them.
A 2-point essay and a 4-point essay get similar treatment because the model isn't
comparing them — it's just filling slots.

---

## 5. Results: Qwen3.6:35b — Completions + JSON Schema

**Run:** 20 essays from ASAP 200-sample, Lenovo llama.cpp, qwen3.6:35b (CUDA)
**Speed:** 48-83 seconds per essay (slower than gemma4 despite CUDA)

| Metric | Value |
|--------|-------|
| Essays with valid JSON | 15/20 (5 failed) |
| Direct-mapped Kappa | **0.011** |
| Calibrated Kappa | **0.103** |
| Quadratic Weighted Kappa | **-0.042** |

### Failure mode: Default-to-zero

Qwen3.6 is more honest about its inability — instead of filling with duplicates, it
outputs `? 0 "none"` when it can't decide:

```
Essay with human score 3:
  THESIS           [/] 1  "some reasonable text"
  EVIDENCE_COUNT   [x] 2  "some evidence"
  EVIDENCE_QUALITY [/] 1  "some more evidence"
  COUNTER          ? 0   "none"
  ORGANIZATION     ? 0   "none"
  MECHANICS        ? 0   "none"
  DEPTH            ? 0   "none"
  → Raw: 4/14  Valid: 3/7
```

The `?` means "check failed" — the model can produce the structure correctly (unlike
gemma4), but defaults to zero whenever it's unsure. Without reasoning, "unsure" means
everything the student didn't explicitly label as "my counter-argument."

### Comparison: gemma4 vs. qwen3.6 schema-enforced

| Behavior | Gemma4:26b | Qwen3.6:35b |
|----------|-----------|-------------|
| Criteria structure | **Broken** — duplicates | **Correct** — all 7 labels |
| Score discrimination | None — all 2s | Some — 0/1/2 spread |
| Speed | Fast (7-14s) | Slow (48-83s) |
| Valid JSON rate | 85% (17/20) | 75% (15/20) |
| Calibrated Kappa | 0.150 | 0.103 |

Neither model produces useful grading. Qwen is structurally cleaner but still can't
discriminate between essays. Gemma4 is faster but structurally broken.

---

## 6. The Chat Completions Dead End

The ideal path — chat completions with `response_format` — is blocked by a
llama.cpp version bug:

```
/v1/chat/completions
  → response_format: { type: "json_schema", json_schema: {...} }
  → stream: false
  → Result: content = "" (empty), finish_reason = "length"
  → All tokens went to reasoning_content (gemma4's thinking field)
```

**What happens:** The server counts `reasoning_content` tokens against `max_tokens`.
Gemma4 thinks for 2048 tokens about the essay, then has zero tokens left for the
actual JSON output. The response is `content: ""` with `finish_reason: "length"`.

**Why we can't just set thinking=false:** `thinking` is a chat completions feature.
The completions endpoint has no thinking at all — which is exactly what makes
completions + json_schema produce garbage content.

**Why we can't stream:** In this llama.cpp build, `response_format` + `stream: true`
returns empty responses entirely (not even `reasoning_content`). Streaming with
constrained output appears unsupported.

### Compatibility matrix

| Endpoint | Stream | json_schema | Thinking | Result |
|----------|--------|-------------|----------|--------|
| `/v1/chat/completions` | true | response_format | enabled | Empty (build bug) |
| `/v1/chat/completions` | false | response_format | enabled | Empty (token drain) |
| `/v1/completions` | N/A | json_schema | N/A | Valid JSON, no reasoning → garbage |
| `/v1/completions` | N/A | none | N/A | Valid text, no reasoning → untested |

---

## 7. What Didn't Work (and Why)

### JSON Schema via completions endpoint
**Mechanically works.** 75-85% valid JSON (the remaining failures are still a bug —
the grammar should be 100% but 3-5 essays still produce parse errors, possibly from
truncation or token limit hits mid-object).

**Semantically useless.** Without reasoning, the model can't:
- Evaluate whether evidence supports the thesis
- Detect counter-arguments woven into the text
- Assess organization quality (paragraph structure, transitions)
- Judge depth (analysis vs. summary)
- Assign scores that correlate with human judgment (Kappa 0.01-0.15)

### Chat completions + response_format
**Doesn't work at all** on this llama.cpp build. The token accounting bug
(reasoning_content counting against max_tokens) means the model thinks and then
has nothing left for output.

### The fundamental tradeoff

```
Completions endpoint
  + JSON schema → valid JSON
  — No reasoning → garbage content
  = Kappa ≤ 0.15

Chat completions endpoint
  + Reasoning → good content (known from Phase 1-3)
  — No schema enforcement → JSON parse failures
  — With response_format → empty responses (llama.cpp bug)
  = Unavailable on current build
```

---

## 8. What We Don't Know (Remaining Gaps)

### A. Does a newer llama.cpp build fix chat completions + response_format?
The token drain bug (`reasoning_content` counting against `max_tokens`) may be
fixed upstream. If `response_format` + no streaming gave us both reasoning AND
schema enforcement, we'd get valid JSON with good content. **Highest priority
to test.**

### B. Does `uniqueItems` fix gemma4's duplication?
Adding `"uniqueItems": true` to the criteria array would force gemma4 to produce
7 *different* criteria IDs. But without reasoning, it might just crash (fail to
produce 7 unique items) or produce 7 unique labels with `? 0 "none"` for each.

### C. Would a non-reasoning model work?
Qwen3.6:35b (non-reasoning architecture) produces structurally correct output but
still can't discriminate (Kappa 0.103). The problem isn't architecture — it's that
JSON schema enforcement removes the deliberation step where quality assessment
happens.

### D. Would `max_tokens: 4096` fix the chat completions token drain?
If the model gets 2048 tokens for reasoning + 2048 tokens for output, it might
produce useful JSON. But this requires a llama.cpp build where `max_tokens`
isn't the sum of reasoning + content — or where we can raise it high enough.

### E. Could we force thinking off in chat completions?
Some models support `"thinking": {"type": "disabled"}` in chat completions.
If gemma4 honors this, chat completions + response_format + no stream +
thinking disabled might work. **Untested.**

---

## 9. The Path Forward (Ranked)

### 1. Fix the llama.cpp build (highest leverage)
Upgrade llama.cpp on Lenovo to a build where:
- Chat completions + `response_format` + `stream: false` produces real content
- `reasoning_content` tokens are either capped separately or not counted against
  `max_tokens`
- Or the `/v1/completions` endpoint supports `json_schema` with reasoning

If any of these work, we get valid JSON + reasoning = useful grading.

### 2. Pipeline-safe prompt engineering (fallback)
If schema enforcement remains blocked, invest in prompt engineering that produces
parseable JSON more reliably:
- System prompt with strict JSON rules
- Few-shot examples showing exact format
- Post-processing: strip markdown fences, fix trailing commas
- Retry loop: if JSON fails, re-prompt with stricter instructions

This is the current production path. It's not elegant but it works.

### 3. Abandon schema enforcement for scoring
The Phase 1-3 experiments showed gemma4 can produce honest *feedback* (no scores)
with zero politeness override. If JSON schema for scores is fundamentally incompatible
with model reasoning, decouple:
- **Feedback:** Free-text, no schema, reasoning enabled → honest observations
- **Score extraction:** A second pass over the feedback text, extracting numeric
  scores with a simple prompt (not a complex rubric)

This splits the hard problem (what's good/bad about this essay?) from the mechanical
problem (convert observations to a 0-2 score grid). The first requires reasoning;
the second is a lookup.

### 4. Test on a cloud model (Claude/GPT-4)
Schema enforcement might work differently on models with controlled APIs where
`response_format` is a tested, production feature (not a llama.cpp edge case).
This would tell us whether the problem is our infrastructure or the approach itself.

---

## 10. Key Numbers

| Experiment | Model | Endpoint | Kappa (calibrated) | Valid JSON | Speed |
|-----------|-------|----------|-------------------|------------|-------|
| Schema-enforced | gemma4:26b | completions + json_schema | 0.150 | 85% | 7-14s |
| Schema-enforced | qwen3.6:35b | completions + json_schema | 0.103 | 75% | 48-83s |
| Schema-enforced (chat) | gemma4:26b | chat + response_format | N/A | 0% (empty) | N/A |
| **Prompt-specific (baseline)** | gemma4:26b | chat (Ollama, CPU) | **pending** | pending | 2-5h |
| Phase 1 non-comp | gemma4:26b | chat (Ollama) | 0.348 | — | — |

The baseline prompt-specific approach (no schema enforcement, just good prompts)
achieved Kappa 0.348 in Phase 1. Schema enforcement has never exceeded 0.150.
**Schema enforcement makes grading worse, not better — at least on current infrastructure.**

---

## 11. Artifacts

| File | Description |
|------|-------------|
| `choros/scoring/batch_schema_enforced.py` | Schema-enforced batch grader (completions endpoint) |
| `/tmp/batch20_schema_final.txt` | Gemma4 schema-enforced output (17/20 valid, Kappa 0.150) |
| `/tmp/batch20_qwen_schema.txt` | Qwen3.6 schema-enforced output (15/20 valid, Kappa 0.103) |
| `choros/scoring/batch_prompt_specific.py` | Original prompt-specific grader (no schema, running on Tower) |

---

*Run on Lenovo ThinkStation PX (NVIDIA GB10, 119GB RAM) with gemma4:26b and qwen3.6:35b via llama.cpp CUDA, and Bufkin Tower (Quadro RTX 4000, 64GB RAM) with gemma4:26b via Ollama CPU. June 21, 2026.*

# The Scoring Bias Experiment — Complete Journey

**2026-06-20 · Choros Project · mbufkin/choros**

---

## 1. The Problem

When an LLM grades student essays, it exhibits **scoring compression bias** — a "walk-down mechanism" where the model correctly identifies flaws in reasoning and writing, then overrides that analysis at the final score. Weak essays get bumped up. Strong essays get pulled down. Scores collapse toward a polite middle, regardless of what the model actually observed.

This is well-documented in the evaluation literature:

- **6 Ways LLM Judges Are Biased** (2026): "A structured wrong answer often beats a casual correct one." LLMs reward formatting, length, and politeness over accuracy.
- **PReMISE: Policy Rubrics as Measurement Specifications** (ICLR 2026): Rubrics need non-compensation clauses — explicit rules that prevent the model from rewarding style when substance is missing.
- **EACL 2026** (Kucia et al.): Binary scoring agents — breaking a rubric into independent yes/no questions — should prevent compromise scoring.
- **JudgmentBench** (Databricks, 2026): Pairwise comparison outperforms rubric scoring in high-judgment domains. Rubrics work for verifiable features; comparative judgment works for holistic quality.

**Our question:** Can we apply these techniques to reduce or eliminate the walk-down? And if not — what actually works?

---

## 2. The Test Set

Five modeled essays on the prompt *"Explain whether students should be required to wear uniforms"*, spanning the full 2-12 score range:

| Essay | Human Score | Level | Length |
|---|---|---|---|
| asap-belowbasic-01 | 2 | Below Basic | 1 sentence, multiple misspellings |
| asap-belowbasic-02 | 3 | Below Basic | 3 sentences, personal opinion only |
| asap-basic-03 | 6 | Basic | Structured with counter-argument, underdeveloped |
| asap-proficient-04 | 8 | Proficient | Evidence + stats + counter-argument, well-organized |
| asap-advanced-05 | 11 | Advanced | Sophisticated argument with economics, sociology, philosophy |

All models run locally on a Lenovo ThinkStation PX (NVIDIA GB10, 119GB RAM) via Ollama.

---

## 3. Phase 1 — Three Strategy Calibration

**Goal:** Test three scoring strategies against human ground truth. Measure Cohen's Kappa (agreement beyond chance) and compression ratio (model score range ÷ human score range).

### Strategies tested

| Strategy | Description | Source |
|---|---|---|
| **A) Holistic** | Single 2-12 score. Current baseline approach. | — |
| **B) Binary Agents** | Per-criterion Y/N questions → converted to 2-12 scale. Six independent checks prevent compromise. | EACL 2026 |
| **C) Non-Compensation** | Holistic scoring with PReMISE anti-compensation rules: "Don't reward good writing if the argument is weak." | ICLR 2026 |

### Gemma4:26b results

| Strategy | Kappa | Compression | What happened |
|---|---|---|---|
| Holistic | 0.318 | 1.11 | Walk-down confirmed. Weakest essay 2→3. Range preserved but offset upward. |
| Binary | 0.130 | 0.44 | **Massive compression.** Advanced essay (11) scored 5. Binary decomposition made gemma4 MORE conservative. |
| **Non-Comp** | **0.348** | 1.11 | **Winner.** Weakest essay scored correctly (2→2). Most consistent across range. Anti-comp rules helped. |

### Qwen3.6:35b results

| Strategy | Kappa | Compression | What happened |
|---|---|---|---|
| **Holistic** | **0.286** | 0.89 | **Winner for qwen.** Consistent walk-down (+1 across the board). |
| Binary | 0.091 | 0.44 | Same crush as gemma4. Binary decomposition is model-independent in its failure mode. |
| Non-Comp | 0.167 | 1.00 | **Backfired.** Weakest essay scored 5 vs human 2. Anti-comp rules made qwen MORE lenient. |

### Nemotron-cascade-2 results

| Strategy | Kappa | Compression | What happened |
|---|---|---|---|
| Holistic | 0.130 | 0.67 | Most compressed of the three. Advanced essay never breaks 9. |
| Binary | 0.130 | 1.00 | Wild scoring. Basic essay got 12, advanced got 12 — binary made nemotron erratic, not conservative. |
| Non-Comp | 0.167 | 0.56 | Anti-comp backfired again. Weakest essay 2→5. Most compressed strategy overall. |

### Three-model cross-comparison

| Strategy | gemma4:26b | qwen3.6:35b | nemotron-c2 |
|---|---|---|---|
| Holistic | 0.318 | 0.286 | 0.130 |
| Binary | 0.130 | 0.091 | 0.130 |
| Non-Comp | **0.348** ★ | 0.167 | 0.167 |

**Key findings from Phase 1:**

1. **Strategy effectiveness is model-dependent.** Non-comp helped gemma4, backfired on qwen and nemotron. What fixes one model breaks another.

2. **Binary agents fail on ALL models.** The EACL 2026 prediction — that independent Y/N questions prevent compromise — does not hold. Binary decomposition either crushes scores to the floor (gemma4, qwen) or makes them erratic (nemotron). The 0.44 compression ratio appears model-independent.

3. **Non-compensation is fragile.** Only gemma4 responded correctly to the anti-compensation rules. Qwen and nemotron interpreted "don't reward good writing" as "be more lenient overall" — the opposite of the intended effect.

4. **Even the best result (0.348) is only "fair" agreement.** For classroom use, you'd want Kappa > 0.60. No strategy got close.

---

## 4. Phase 2 — Remove the Score Entirely

**Hypothesis:** The bias lives in the scoring mechanism. If we remove the number entirely and ask for qualitative feedback, does the model give honest, useful notes?

### Feedback Audit

Gemma4:26b was asked to give teacher-style feedback on each essay — no scores, no rubrics, no grades. Just feedback.

**Prompt:** *"You are a classroom teacher providing feedback on a student essay... Write the feedback you would give them. Point out specific strengths and weaknesses. Be honest — don't praise if there's nothing to praise."*

### Results

| Essay | Human | Words | Feedback quality |
|---|---|---|---|
| Below Basic | 2 | 181 | "Much too short to be considered an essay... you haven't provided any reasons or evidence." Calls out specific misspellings (fare→fair, ware→wear). |
| Below Basic | 3 | 257 | "Most of your essay relies on personal feelings rather than persuasive arguments." Gives single actionable task: "Pick one point and write three sentences explaining why." |
| Basic | 6 | 238 | "Feels more like an outline than a full piece of writing." Identifies counter-argument as strength but underdeveloped. Gives per-paragraph expansion targets. |
| Proficient | 8 | 322 | Balances praise ("clear, organized") with refinement. Suggests structural change: make the dress-code idea its own paragraph. |
| Advanced | 11 | 330 | Structured as "What you did well" / "Areas for improvement." Critiques the dense introduction even on the strongest essay. |

### Finding

**Zero "great job, no notes."** Every essay got specific, quoted, actionable feedback. The model:

- Quotes exact phrases from the essays
- Identifies real weaknesses (not generic ones)
- Gives concrete next steps
- Scales feedback appropriately — more correction for weak essays, more refinement for strong ones
- Produces 181-330 words of genuine engagement per essay

**When you remove the number, gemma4 becomes a genuinely useful feedback tool.** The compression bias disappears entirely because there's no score to compress.

---

## 5. Phase 3 — Where Does the Bias Live?

**Hypothesis:** If honest feedback exists (Phase 2 proved it does), and we feed that feedback to a fresh scorer — without showing the essay — will the scorer still inflate weak scores?

### Two-Pass Experiment Design

| Mode | Input | Output |
|---|---|---|
| **A) Direct** | Rubric + essay | Score |
| **B) Blind** | Rubric + feedback only (essay hidden) | Score |
| **C) Informed** | Rubric + essay + feedback | Score |

All three modes use gemma4:26b as the scorer. The feedback comes from the Phase 2 audit.

### Results

| Mode | Kappa | Key behavior |
|---|---|---|
| **A) Direct** | **-0.042** | **Uniform +1 inflation.** Every essay bumped exactly one point. Below-basic 2→3, basic 6→7, proficient 8→9, advanced 11→12. Worse than random guessing. |
| **B) Blind** | **0.348** | Major improvement — but still inflates. The feedback said "much too short to be considered an essay," yet the scorer gave it a 4 (human: 2). The scorer *read the honest feedback and overruled it.* |
| **C) Informed** | **0.348** | Identical to blind. Showing the essay doesn't help or hurt. The scorer ignores the essay when feedback is present. |

### Finding

**The bias lives in the scoring step, not the observation step.** Gemma4 can be an honest observer (Phase 2 feedback audit proves this). But when you ask it to produce a number, the walk-down mechanism activates — even when the only input is critical feedback calling the essay inadequate.

Mode A is the smoking gun: uniform +1 inflation across all five essays, producing Kappa -0.042. The model can't give a 2. It *won't* give a 2. Even when the essay is one misspelled sentence with no evidence.

Mode B shows the bias is stubborn: honest feedback reduces it (0.348 vs -0.042) but doesn't eliminate it. The scorer still bumped the weakest essays by 2 points.

**Prompt format matters enormously.** Earlier holistic runs (Phase 1) with longer, more structured prompts produced Kappa 0.318. The same model with a shorter, rubric-table prompt (Phase 3, Mode A) produced -0.042. Same model, same essays — completely different behavior driven by prompt wording alone.

---

## 6. What We Know Now

### What works

- **Qualitative feedback without scoring.** Gemma4 gives specific, accurate, actionable teacher feedback when freed from the obligation to produce a number. Zero "great job, no notes" across five essays spanning the full quality range.

### What doesn't work

- **Binary decomposition** (EACL 2026). Fails on all three models tested. Either crushes scores to the floor or makes them erratic. The theoretical advantage of independent checks does not survive contact with real models.

- **Non-compensation rules** (PReMISE, ICLR 2026). Works on gemma4, backfires on qwen and nemotron. Strategy is model-dependent and fragile.

- **Direct rubric scoring.** Uniform inflation. The model cannot assign the lowest score even when the essay objectively merits it.

- **Blind scoring from feedback.** Reduces but doesn't eliminate bias. The scorer overrules honest feedback to inflate weak essays.

### What we don't know

- Whether a different model family (Claude, GPT-4) exhibits the same walk-down mechanism
- Whether pairwise comparison (JudgmentBench approach) would outperform rubric scoring for these essays
- Whether fine-tuning a model specifically for K-12 feedback would eliminate the politeness override
- Whether the prompt format sensitivity can be weaponized — can we design a prompt that fully eliminates the walk-down?

---

## 7. Recommendations

1. **Keep the feedback, kill the score.** The feedback audit is the most useful artifact from this experiment. Gemma4 is ready to give teacher-quality feedback today. It is not ready to assign grades.

2. **If scoring is required, use gemma4 with the non-compensation prompt from Phase 1.** Kappa 0.348 is the best we've achieved. It's not good enough for classroom use but it's a real signal above chance.

3. **Test pairwise comparison next.** JudgmentBench showed comparative judgment outperforms rubrics in high-judgment domains. Instead of "score this essay 2-12," ask: "Which of these two essays is better? By how much?" This may bypass the politeness override entirely.

4. **Investigate prompt sensitivity.** The 0.318 → -0.042 swing from prompt changes alone suggests there's a prompt that could hit Kappa 0.40+. Systematic prompt engineering is the highest-leverage next step.

5. **Don't use binary agents.** They failed on every model tested. The theoretical appeal of independent Y/N checks does not translate to real LLM behavior.

---

## 8. Artifacts

All code and results committed to `mbufkin/choros`:

| File | Description |
|---|---|
| `scoring/calibrate.py` | Three-strategy scoring pipeline with Kappa + compression metrics |
| `scoring/feedback_audit.py` | Teacher feedback without scoring |
| `scoring/twopass_experiment.py` | Two-pass experiment: where does bias live? |
| `scoring/guardrails/essays.json` | Five modeled ASAP essays with human scores |
| `scoring/guardrails/feedback_audit.json` | Full teacher feedback from gemma4 |
| `scoring/guardrails/calibration_results.json` | Latest calibration run |
| `scoring/guardrails/twopass_results.json` | Two-pass experiment results |

**Conference sources (Obsidian):** `50-Research/LLM Conference Videos/` — 25 structured notes from ICLR 2026, EACL 2026, and AI security conferences.

---

*Run on a Lenovo ThinkStation PX (NVIDIA GB10, 119GB RAM) with gemma4:26b, qwen3.6:35b-a3b, and nemotron-cascade-2 via Ollama. June 20, 2026.*

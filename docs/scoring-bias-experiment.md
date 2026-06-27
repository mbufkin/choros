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

---

<<<<<<< HEAD
## 9. Phase 4 — Cross-Model Two-Pass Evaluation

**Date:** June 26, 2026  
**Models:** Ornith 35B MoE (Pass 1, supportive) → Nemotron Nano 9B v2 (Pass 2, adversarial)  
**Status:** Proof of concept — 3 essays. Promising.

### The Problem Revisited

All prior phases proved the scoring-step bias (politeness override / walk-down) activates whenever a model has to produce a numeric score — even when fed honest critical feedback. Strategy D (checklist) worked around this but still showed model leniency on checkbox decisions.

Phase 3 (Two-pass) used the *same* model family for both passes and asked the second pass to *score the essay blindly from feedback*. That failed because the scoring-step bias is the same model's pattern — it overruled its own honest feedback.

### The Insight

Don't fight the politeness — **use it**. The first pass should be maximally supportive (where LLMs are naturally good). Then a *different model from a different family* reviews the *first pass's assessment*, not the essay. The second model is told "nothing is perfect" — it's reviewing a peer reviewer, which is a fundamentally different cognitive task than grading a student.

### Architecture

```
Essay → [Ornith 35B — Supportive Teacher] → Rich, encouraging feedback
                                              ↓
                       [Nemotron 9B — Adversarial Reviewer]
                       Reads the feedback + original essay
                       Told: "Nothing is perfect. Push back."
                       ↓
                       Score: X/50 + evidence-based reasoning
```

### Pass 1 Prompt (Ornith — Supportive)

> You are a supportive teacher reading a student essay. Write feedback: what the student is saying, what works well (quote passages), gentle suggestions. Be warm, specific, and encouraging.

### Pass 2 Prompt (Nemotron — Adversarial)

> You are a tough but fair reviewer. Read the supportive feedback below and provide a reality check. The first evaluator was being nice. You are not. Is the first evaluator being too generous? Nothing is perfect. Every essay has room to grow. Give a score 1-50 and your reasoning. Reference the first evaluator's claims and push back where needed.

### Results

| Essay | Length | Key Issue | Score |
|-------|--------|-----------|-------|
| Weak (wrong side, 2 lines) | 194 chars | Argues *for* uniforms, prompt asks *against* | **12/50** |
| Medium (balanced, pro-uniform) | 621 chars | Wrong side of prompt, no specific examples | **18/50** |
| Strong (3 reasons, structured) | 711 chars | Good structure but no concrete evidence | **25/50** |

### Key Observations

1. **No politeness override.** Nemotron pushed back on Ornith's generous feedback consistently — "The first evaluator's praise for the 'balanced approach' overlooks the fundamental mismatch between the essay's stance and the prompt."

2. **Score spread is real.** 12 vs 18 vs 25. Compare to previous phases where everything compressed to 1 or a uniform 4-5 band.

3. **Evidence-based pushback.** Nemotron quoted specific lines from Pass 1 feedback and corrected them, rather than pattern-matching a number.

4. **The "nothing is perfect" framing works.** Even the strong essay got 25/50. The model genuinely looked for gaps.

5. **Score is depressed but consistent.** 25/50 for "solid student work with clear evidence gaps" aligns with the scale description (30 = solid, 40 = excellent, 50 = exceptional).

### What's Different From Phase 3

| | Phase 3 | Phase 4 |
|---|---|---|
| Pass 1 model | Gemma4 | Ornith 35B |
| Pass 2 model | Gemma4 (same) | Nemotron 9B (different family) |
| Pass 2 task | Score essay blindly from feedback | Review first evaluator's assessment |
| Pass 2 framing | Neutral rubric | "Nothing is perfect — push back" |
| Score scale | 2-12 | 1-50 |

### Open Questions (answered by N=20 run)

All six questions from the POC were tested on 20 actual ASAP essays with ground truth scores.

**Kappa result: 0.0022 (linear).** The adversarial pushback is **uniform** — it knocks ~5-10 points off every essay regardless of quality — not selective based on merit. 17/20 essays landed in the 12-18/50 band.

### N=20 Full Results

| Metric | Value |
|--------|-------|
| **Linear Kappa** | **0.0022** |
| Score band | 10-22 /50 (narrow) |
| Essays in 12-18 band | 17/20 |

### Key Finding

The two-model architecture breaks the uniform-score ceiling but produces **noise, not signal**. The adversarial instruction "nothing is perfect" works (scores aren't all max) but the model has no rubric, no reference points, and no calibration — so it applies uniform downward pressure regardless of essay quality. See Phase 5 for the fix.

### Artifacts

| File | Description |
|---|---|
| `/tmp/phase4_pipeline.py` | Two-pass pipeline script (on Lenovo) |
| `/tmp/phase4_results.json` | Raw results (on Lenovo) |

*Run on a Lenovo ThinkStation PX (NVIDIA GB10, 119GB RAM) with Ornith 35B MoE (llama-server port 8080) and Nemotron Nano 9B v2 (llama-server port 8081). June 26, 2026.*

---

## 11. Phase 5 — Rubric Judge (June 26)

**Hypothesis:** Both models need a shared reference. If Pass 1 (Ornith) aligns feedback to rubric categories (Content, Organization, Style), and Pass 2 (Nemotron) assigns per-dimension scores (1-6) *backed by verbatim quotes*, the quote requirement forces grounding.

### Design

| Pass | Model | Role | Input | Output |
|------|-------|------|-------|--------|
| **1** | Ornith 35B MoE | Supportive teacher | Essay + ASAP rubric anchors | Feedback by dimension (Content / Organization / Style) |
| **2** | Nemotron Nano 9B v2 | Strict grader | Ornith's rubric feedback + essay | Per-dimension score 1-6 + verbatim quote per score + total /18 |

### Rubric Anchors

Each dimension uses behavioral anchors from the ASAP rubric:

| Score | Content | Organization | Style |
|-------|---------|-------------|-------|
| 1-2 | Minimal/off-topic | No structure | Basic vocab, repetitive |
| 3-4 | Some development | Some structure, weak transitions | Adequate vocab, minor errors |
| 5-6 | Strong thesis/evidence | Clear progression | Sophisticated, varied voice |

### Results (N=20)

| Metric | Value |
|--------|-------|
| **Linear Kappa** | **0.2408** |
| **Quadratic Kappa** | **0.4305** |
| Valid results | 18/20 (3 off-topic essays correctly scored 0) |
| Dimension coverage | 17/20 (3 essays had null dimensions — Nemotron refused to score off-topic work) |
| Score range | 0-20 → 0-50 scaled |

### Cross-tabulation

| Model score bucket | Count | Avg Human | Avg Model |
|---|---|---|---|
| 0-5 | 2 | 4.00 | 1.50 |
| 6-10 | 7 | 8.29 | 9.57 |
| 11-15 | 1 | 8.00 | 13.00 |
| 16-20 | 8 | 9.25 | 17.38 |

### Key findings

1. **The quote-requirement works.** Nemotron grounded scores in actual text. The 3 off-topic essays correctly scored 0 — Nemotron refused to apply the rubric to off-topic work, which is arguably *more accurate* than the human graders (who credited them anyway).

2. **Kappa 0.43 (quadratic) is the best result yet.** Up from 0.35 (Phase 1, Non-Comp on gemma4). The rubric + quote + cross-model architecture produces real signal.

3. **But scores are still compressed.** Nemotron never gave above 3/6 in any dimension, even for the 11/12 essay. The model's threshold for "4+" is unrealistically high.

4. **The breakthrough framing:** A model that sees *both* a rubric *and* is forced to quote evidence produces Kappa > 0.40. The remaining gap is calibration — the model needs exemplars at each score level to learn what 4/6 vs 5/6 vs 6/6 actually looks like in practice.

### Next steps (not pursued — redirecting to demo)

- **Exemplar calibration:** Give Nemotron scored examples at each grade level before asking it to grade
- **Score-level anchoring:** Force full 1-6 range by associating each numeric level with a specific behavioral description
- **Pairwise comparison:** JudgmentBench-style comparative judgment may bypass the compression entirely

---

## 12. Phase 6 — Calibrated Judge (June 26)

**Hypothesis:** Separate observation from scoring entirely. The model provides structured observations (dimension + verbatim quote + behavioral description) but NEVER assigns a number. A deterministic Python layer maps observation patterns to scores.

### Design

| Step | Who | What |
|------|-----|------|
| **Observation** | Nemotron Nano 9B v2 (single pass) | Read essay + exemplar anchors, produce dimension quotes and behavioral observations (no numbers) |
| **Scoring** | Python (keyword heuristics) | Pattern-match observation text against penalty/bonus markers → scaled score 1-12 |

### Results (N=20)

| Metric | Value |
|--------|-------|
| **Linear Kappa** | **-0.022** |
| **Quadratic Kappa** | **0.012** |
| Valid results | 20/20 |
| Score range | 3-6 /12 (severe compression) |

### Key Finding

The pattern architecture is **correct** — model observations were grounded, consistent, and quote-backed (e.g., "the essay fails to address the prompt about school uniforms" for off-topic essays). But the deterministic keyword heuristic was too crude. Matching words like "minimal," "lacks," "sophisticated" against a fixed penalty/bonus table doesn't capture real quality differences.

**The real bottleneck:** model observations only used the 1-3 range per dimension (compressed to 3-6/12) for all 20 essays. With only 3 discrete feature values across 17 valid essays, even ridge regression (degree 2 polynomial, 10 parameters) overfits and produces negative Kappa on cross-validation.

### What this tells us

The model's observation range is compressed because it has **no exemplar distribution**. It doesn't know what a 1/6 or 6/6 essay looks like structurally, so it anchors to the descriptor middle and stays there. Until the model sees real scored exemplars at each level, no calibration layer above can produce Kappa above ~0.43.

The remaining path is **exemplar-grounded scoring**:

1. Show the model 1-2 real essays at each score level (1, 3, 5, 7, 9, 11/12) with human-assigned dimension scores
2. Ask it to place the new essay relative to those anchors
3. Use the rubric + quote pattern from Phase 5 for grounding
4. Score is computed as distance-weighted average of nearest exemplars, not a model-assigned number

This removes both the "no exemplar distribution" and "model assigns score" bottlenecks simultaneously.

---

*Phase 6 run on a Lenovo ThinkStation PX (NVIDIA GB10, 119GB RAM, aarch64) with llama.cpp server: NVIDIA-Nemotron-Nano-9B-v2-Q4_K_M.gguf (port 8081). June 26, 2026.*

---

## 13. Phase 7 — Decision-Tree Scoring (June 27)

**Date:** June 27, 2026  
**Model:** DeepSeek V4 Flash (284B MoE, IQ2XXS, 81GB) on ds4-server (port 8082)  
**Design question:** How do we score without assignment-specific exemplars? The system needs to grade any assignment — writing, engineering, math — without pre-scored examples per prompt.

### The Problem With Exemplars

Phases 1-6 converged on the same bottleneck: the model can observe well (quote evidence, identify flaws) but cannot map observations to a numeric scale. The proposed fix — exemplar-grounded scoring (show scored essays at each level) — breaks modularity. A general-purpose grader can't have custom exemplars per assignment.

### Phase 7 Architecture

**Core insight:** The model succeeds at YES/NO questions grounded in quoted evidence. It fails at NUMBER assignment. So never ask for a number. Route through a decision tree where each node is a grounded yes/no question, and the Python layer determines the level from the path taken.

```
                    Task Alignment?
                   /               \
                 NO                 YES
              Off-Task          Completeness?
                               /              \
                             NO                YES
                          Novice           Quality Gate?
                                          /              \
                                     HAS flaws        NO flaws
                                       /                   \
                                  Flaw Type?           Correctness?
                                 /        \               /       \
                           Content    Form/Clarity      YES       NO
                              |           |              |     Developing
                          Developing  Recoverable?      Clarity?
                                     /         \          /    \
                                  YES          NO      YES     NO
                              Developing     Novice   Depth  Proficient
                                                      /   \
                                                    YES    NO
                                                Advanced  Proficient
```

**Key properties:**
- Model **never outputs a number** — only YES/NO + quotes
- Each question is grounded in a **verbatim quote** from the work
- The tree uses universal quality dimensions that apply to any domain:
  - Task alignment (did they attempt it?)
  - Completeness (did they finish it?)
  - Quality gate (are there significant flaws?)
  - Correctness (is the content accurate?)
  - Clarity (is it well organized?)
  - Depth (does it show insight?)

### Results (v2 tree, 50-point pilot on 3 essays vs DS4 V4 Flash)

| Essay | Human Score | Phase 7 Level | Phase 7 Score | Correct? |
|-------|-------------|---------------|---------------|----------|
| Below-basic (1 sentence, misspellings) | 2/12 | Novice | 2/5 | ✅ |
| Basic (several paragraphs, personal opinion) | 6/12 | Proficient | 4/5 | ❌ (should be Developing/Proficient border) |
| Advanced (research, structure, synthesis) | 11/12 | Advanced | 5/5 | ✅ |

### What Worked

1. **The weak essay correctly hit Novice** — the completeness gate caught the too-short response. No inflation.
2. **The strong essay correctly hit Advanced** — depth gate distinguished it from the medium essay. Quote evidence was real.
3. **No walk-down observed.** The model did not inflate weak scores or compress strong ones. Each YES/NO was grounded in a specific quote.
4. **Only 2-6 API calls per essay** (vs 2 per essay in Phase 5's two-pass). The tree typically terminates in 4-6 nodes.

### Remaining Issue

The medium essay (human 6/12) scored Proficient (4/5). The quality gate said "no significant flaws" and correctness said "yes" — because the content is reasonable even if simple. The model was still too generous at the **correctness node** for basic essays. This is a **prompt design issue** at the node level, not a systematic bias. Tuning the gate questions (making "significant flaw" detection more aggressive) would push it to Developing.

### Key Finding

**The decision-tree architecture eliminates the scoring-step bias.** By replacing "assign a number" with grounded yes/no questions, the politeness override never activates because:
- YES/NO questions about observable properties are **not abstract judgments**
- The quote requirement prevents hand-wavy answers
- The tree structure constrains the path — the model can't inflate a score by picking a higher number; it has to answer a specific factual question

### Next Step

Calibrate the node questions with a proper N=20 ASAP run to find the right threshold wording. The tree structure is correct — the model's behavior demonstrates no compression or inflation. The only adjustment needed is how aggressively the quality gate and correctness nodes classify borderline work.

### Artifacts

- `/home/mbufkin/.hermes/work/phase7_decision_tree.py` (v1) and `phase7_v2.py` (v2)
- Code and results at `mbufkin/choros` when merged

*Phase 7 run on a Lenovo DGX Spark (NVIDIA GB10, 119GB RAM, aarch64) with DS4 server: DeepSeek V4 Flash IQ2XXS (port 8082). June 27, 2026.*

---

### 14. Phase 7.1 — 7-Level Expansion (June 27)

Phase 7 proved the decision-tree architecture eliminated scoring bias (no compression, no inflation). The next question: **would more terminal levels improve discrimination?**

The 5-level tree (Off-Task, Novice, Developing, Proficient, Advanced) was expanded to 7 levels by splitting the depth gate into three tiers: depth_gate → depth_synthesis → depth_exemplary. This created Advanced (5/7), Distinguished (6/7), and Exemplary (7/7) as distinct levels.

**Result: No improvement.**

| Version | Levels | Linear K | Quadratic K |
|---------|--------|----------|-------------|
| 5-level | 5 | 0.358 | 0.617 |
| 7-level | 7 | 0.376 | 0.622 |

The ceiling is **node question quality, not bucket count**. Both versions route to the same place because the depth_gate question is too lenient — "does this show any analysis beyond opinion?" is satisfied by almost any multi-paragraph essay. The bottleneck is at individual node phrasing, not tree structure or terminal count.

**Confusion (7-level):**
```
H= 2 → Novice ✅
H= 6 → Developing ✅
H= 7 → 1× Distinguished, 1× Developing ✅
H= 8 → 7× Distinguished, 1× Developing ❌ (overgrade)
H= 9 → all Distinguished ❌ (should split Advanced/Distinguished)
H=10 → all Distinguished ❌
H=11 → Distinguished ❌ (should be Exemplary)
```

**Key insight:** Adding terminal nodes without fixing the gates that feed them doesn't help. The depth_gate lets H=7-8 essays through to Distinguished because they pass "any analysis" — the gate needs to ask for *specific evidence* earlier in the tree.

**Model floor confirmed:** Nemotron 3 Nano 30B A3B failed (0.02 Kappa). Nemotron Super 49B routes correctly. Decision-tree grading requires ≥49B.

### Artifacts

- `phase7_nemotron49_n20.py` — 5-level tree, N=20 run
- `phase71_nemotron49_n20.py` — 7-level expansion, N=20 run
- Results JSON at `/tmp/phase7_nemotron49_n20_results.json` and `/tmp/phase71_nemotron49_n20_results.json`
- Full documentation: [[50-Research/Phase 7 — Decision Tree Grading Architecture]]

*Phase 7.1 run on NVIDIA API with nvidia/llama-3.3-nemotron-super-49b-v1. June 27, 2026.*

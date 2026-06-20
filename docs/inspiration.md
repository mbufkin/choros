# Inspiration & References

Papers, repos, and talks that shaped the Choros scoring guardrail work.

---

## Primary Papers

### Rulers: From Rubrics to Reliable Scores (Hong et al., 2026)
**arXiv: 2601.08654** · Washington University, ASU, FSU

The paper that validated our form-fill approach. Three-stage pipeline:
1. **Rubric locking** — convert human rubric → structured bundle, hashed, reused unchanged
2. **Evidence-grounded checklist execution** — model returns 0/1/2 decisions + cited evidence + extractive quote verification. Python verifies quotes exist in source text.
3. **Post-hoc calibration** — ridge regression maps checklist signals to human score distribution (N=200 calibration set)

Key results on ASAP 2.0 (essay scoring): QWK 0.72 vs 0.48 direct holistic. Identifies three failure modes we independently hit: rubric execution drift, unverifiable score attribution, human-scale misalignment.

**What we took from it:** Evidence grounding requirement (quote the text that justifies each checkbox), 3-value decisions (0/1/2), post-hoc calibration instead of raw counting.

---

### LLM Essay Scoring Under Holistic and Analytic Rubrics: Prompt Effects and Bias (Kucia et al., 2026)
**arXiv: 2604.00259** · Warsaw University of Technology

Systematic evaluation of instruction-tuned LLMs across three essay datasets (ASAP 2.0, ELLIPSE, DREsS). Same author as the EACL 2026 binary agents talk.

Key findings:
- Holistic QWK ≈ 0.6 with strong models (Llama-3.1-70B)
- Analytic scoring much harder — LOC traits (Grammar, Conventions) show large negative bias
- Concise keyword prompts outperform long rubric-style prompts for multi-trait scoring
- Bias detectable with as few as N=5 samples on LOC traits
- Bias-correction-first deployment: estimate systematic offsets from small human-labeled sets

**What we took from it:** Cross-dataset comparison methodology, N_min for bias detection, keyword vs guidelines prompt strategy.

**Key difference:** They found models are TOO HARSH (negative bias). We found models are TOO LENIENT (walk-down, positive bias). Different model families produce different bias directions.

---

### Bridging the LLM Accessibility Divide? Performance, Fairness, and Cost of Closed vs Open LLMs for Automated Essay Scoring (Oketch et al., 2025)
**arXiv: 2503.11827** · Notre Dame

Compares open vs closed LLMs for AES. Finds that open models can approach closed-model performance for essay scoring when properly prompted.

**What we took from it:** Validation that open-weight models (our approach) are viable for this task.

---

### From Prompting to Preference Optimization: A Comparative Study of LLM-based Automated Essay Scoring (Nguyen et al., 2026)
**arXiv: 2603.06424**

Compares prompting techniques vs preference optimization for AES. Preference optimization outperforms prompting for English L2 writing assessment.

**What we took from it:** Confirmation that prompting strategy matters enormously — consistent with our Kappa -0.042 to 0.318 swing from prompt changes alone.

---

## Conference Talks (Processed into Obsidian)

All talks transcribed via Whisper on Lenovo, processed by gemma4:26b into structured notes. Full notes in `obsidian-vault/50-Research/LLM Conference Videos/`.

| Talk | Source | Key insight |
|---|---|---|
| **PReMISE: Policy Rubrics as Measurement Specifications** | ICLR 2026 | Non-compensation clauses ("don't reward style if content is wrong") |
| **6 Ways LLM Judges Are Biased** | Agentic AI & Cloud Advisory | Position, verbosity, self-preference, style bias — "a structured wrong answer beats a casual correct one" |
| **JudgmentBench** | Databricks Summit | Comparative judgment beats rubrics for high-judgment domains; rubrics for verifiable features only |
| **The Silent Failure of LLM Judges** | — | "The agent fails loudly. The judge fails sadly." Verification is harder than generation. |
| **Eliminate Judge Bias via Binary Scoring Agents** (Kucia) | EACL 2026 | Binary Y/N per criterion prevents compromise — we tested this and it FAILED on all three models |

---

## GitHub Repos

### Laeyerz Examples (Pixagan Technologies)
**github.com/pixagan/laeyerz-examples** · Apache 2.0

LLM Exam Grader with three approaches: rubric (with match types), comparative, consistency checker. GPT-5-mini via API. Architecture demo — no empirical results.

**What we took from it:** Match types for rubric criteria (EXACT/EXPLICIT/EQUIVALENT/SEMANTIC), confidence flags per criterion, consistency checker concept.

---

### Automated Essay Scoring with LLMs (yassir7743)
**github.com/yassir7743-create/Automated-Essay-Scoring-LLM**

ASAP dataset, few-shot prompting with LangChain, 4-dimension scoring (Ideas/Organization/Style/Conventions), quadratic weighted Kappa, Nemotron 30B via API.

**What we took from it:** Confirmation that ASAP dataset + Kappa is the standard approach. They use Kappa as a success metric; we treat low Kappa as the research question.

---

### LLM Hub Evaluations (BrendanJamesLynskey)
**github.com/BrendanJamesLynskey/LLM_Hub_Evaluations**

Presentation series on LLM-as-judge biases, mitigation strategies, eval frameworks. Educational resource, not experimental code.

**What we took from it:** Survey of the bias landscape — positional, verbosity, self-preference, sycophancy.

---

### Rulers Implementation (luoluomei)
**github.com/luoluomei/Rulers_0525**

Open-source implementation of the Hong et al. (2026) Rulers paper. Clean, well-documented Python codebase. Key design patterns we can adopt:

- **4 traits × 20 checklist items** with type-aware evidence rules
- **4 evidence types**: local_quote (verbatim), span_level (paragraph), global_diagnostic (document-level), weakly_groundable (human review)
- **Structured JSON output** via schema — trait scores, checklist decisions (0/1/2), confidence, evidence per trait
- **Evidence validation**: quotes verified as verbatim substrings of source sentences
- **Ridge regression calibration** with polynomial features + monotone quantile mapping
- Designed for OpenAI-compatible API; adaptable to Ollama

**What we took from it:** The evidence type taxonomy, checklist sizing (20 items), JSON schema design for structured scoring output, calibration layer architecture.

---

### ASAP-AES Benchmark (benhamner)
**github.com/benhamner/ASAP-AES**

Official evaluation metrics and benchmarks from the Hewlett Foundation's Automated Essay Scoring competition. Includes Quadratic Weighted Kappa implementation (R + Python) and a **length-only baseline** — predicts scores from character count + word count alone using a random forest.

**What we took from it:** The length baseline is a critical sanity check. If an LLM scoring system can't outperform "longer essays get higher scores," it's not evaluating content. We should add this to our benchmark suite.

---

### Human Preferences (kaigani)
**github.com/kaigani/human-preferences** · Created 2026-06-20

Local-first tool for capturing personal A/B preferences as a dataset. Export as LLM-judge rubric or DPO fine-tuning set. Built on Stanford Human Preferences (SHP) schema. Maps directly to the JudgmentBench pairwise comparison approach.

**What we took from it:** Pairwise preference collection workflow. Validates the comparative judgment direction we flagged from JudgmentBench.

---

## Our Contributions

What we did that none of these sources did:

1. **Three-strategy, three-model comparison** — nobody else compared holistic vs binary vs non-comp across multiple open-weight models on the same essays
2. **Feedback audit** — proved that qualitative feedback works when scoring doesn't
3. **Two-pass experiment** — isolated bias to the scoring step, not the observation step
4. **Form-fill experiment** — independently converged on the checklist approach later formalized by Rulers
5. **Synthetic rubric validation** — tested whether LLMs can accurately count known criteria counts
6. **All local, all open** — every experiment run on self-hosted hardware with open-weight models. No API keys, no proprietary dependencies.

---

*Last updated: 2026-06-20*

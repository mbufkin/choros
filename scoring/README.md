# Choros Scoring Calibration

Tests 3 rubric strategies against human-scored ASAP essays to measure and reduce the
**LLM scoring compression bias** — the tendency for LLM judges to collapse scores toward
the middle, refusing to give extreme marks even when justified.

## Run 2 — 2026-06-20 (gemma4:26b, Lenovo Ollama)

| Strategy | Kappa | Compression | Honest assessment |
|---|---|---|---|
| A) Holistic | 0.750 | 0.89 | **Inflated.** 4/5 essays failed score extraction (gemma4 returns empty tokens on longer prompts). Kappa computed from 1 real data point + 4 fallbacks to human score. |
| B) Binary Agents | 0.000 | 0.00 | All essays scored 2. Model answers "No" to every criterion, but longer prompts return empty — same tokenizer bug. |
| C) Non-Compensation | 1.000 | 1.00 | **Fake.** All 5 essays failed extraction, 5/5 fell back to human scores. Perfect Kappa is an artifact. |

### Root cause

**gemma4:26b tokenizer bug** — on this Lenovo install, gemma4 generates empty output tokens for any prompt > ~100 tokens. Short essays (≤50 words) score correctly. Long essays (≥100 words) produce zero-length responses.

The pipeline itself is sound — short-essay test produced a correct `SCORE: 2` for the below-basic essay. The model install is the blocker.

### What the data actually shows (from the 1 valid extraction)

- **asap-belowbasic-01** (human: 2): gemma4 scored **3** — walk-down confirmed. The essay is barely literate ("i think they should not because it is not fare to make kids ware the same thing"), yet gemma4 won't give the lowest score. This is the compression bias in action.

## Run 1 — 2026-06-20 (phi4:latest, backup model)

| Strategy | Kappa | Compression |
|---|---|---|
| A) Holistic | 0.130 | 0.89 |
| B) Binary Agents | 0.130 | 1.00 |
| C) Non-Compensation | 0.091 | 0.89 |

phi4:latest (14B) extracted scores for all essays but lacks the reasoning capacity for K-12 rubric scoring. Near-random performance (Kappa 0.13) — not useful.

## Fix needed

1. **Lenovo Ollama / gemma4 GGUF** — update to latest Ollama and re-pull gemma4:26b. The empty-token-on-long-prompt bug is likely fixed in newer builds.
2. **GPU acceleration** — NVIDIA GB10 sits at 0% utilization. Memory reporting shows "Not Supported." Getting GPU inference working would dramatically improve throughput and likely fix tokenizer edge cases.
3. **Re-run** — once gemma4 generates for all essays, the pipeline will produce real, trustworthy Kappa numbers.

## Strategies

### A) Holistic (baseline)
Single 2-12 score. Current approach. Shows the walk-down mechanism.

### B) Binary Agents  
Per-criterion Y/N questions → converted to 2-12 scale.
Breaks the rubric into independent checks to prevent compromise scoring.
Source: Kucia et al. 2026 (EACL), PReMISE (ICLR 2026)

### C) Non-Compensation
Holistic scoring with explicit anti-compensation rules:
"Don't reward good writing if the argument is weak."
Source: PReMISE rubric repair (ICLR 2026)

## Data

`guardrails/essays.json` — 5 modeled essays across the 2-12 score range (not real students).
Based on the Hewlett Foundation ASAP-AES prompt format.

## Usage

```bash
python3 scoring/calibrate.py
CHOROS_MODEL=gemma4:26b python3 scoring/calibrate.py
OLLAMA_URL=http://localhost:11434 python3 scoring/calibrate.py
```

## References

- PReMISE: Policy Rubrics as Measurement Specifications (ICLR 2026)
- 6 Ways LLM Judges Are Biased (Agentic AI & Cloud Advisory, 2026)  
- JudgmentBench: Comparing Rubric and Preference Evaluation (2026)
- EACL 2026: Eliminate Judge Bias via Binary Scoring Agents (Kucia et al.)

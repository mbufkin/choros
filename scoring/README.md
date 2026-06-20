# Choros Scoring Calibration

Tests 3 rubric strategies against human-scored ASAP essays to measure and reduce the
**LLM scoring compression bias** — the tendency for LLM judges to collapse scores toward
the middle, refusing to give extreme marks even when justified.

## Run 1 — 2026-06-20

| Strategy | Kappa | Compression | Notes |
|---|---|---|---|
| A) Holistic (baseline) | 0.130 | 0.89 | phi4:latest — inadequate capacity |
| B) Binary Agents | 0.130 | 1.00 | phi4:latest — inflated all scores |
| C) Non-Compensation | 0.091 | 0.89 | phi4:latest — worse than baseline |

**Status: BLOCKED** — phi4:latest is a 14B model, insufficient for K-12 rubric scoring.
The intended model (gemma4:26b, 17GB) and backups (qwen3.6:35b, 23GB) are not generating
on the Lenovo ThinkStation PX. Suspected causes: corrupted context after crash / memory
issue. All Gemma and Qwen models return empty responses.

### What works
- Pipeline mechanically operational: loads essays, calls 3 strategies in parallel style,
  computes Cohen's Kappa + compression ratio
- Extraction is flexible (case-insensitive, fallback patterns)
- Binary agent scoring with 6 criteria (CLAIM, EVIDENCE, STRUCTURE, COUNTER, LANGUAGE, DEPTH)

### What's needed
- Fix Lenovo model loading (gemma4:26b or qwen3.6:35b-a3b)
- Re-run with Kappa target > 0.60
- Then test against STAAR Algebra 1 items

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
# Default (phi4:latest on Lenovo)
python3 scoring/calibrate.py

# With specific model
CHOROS_MODEL=gemma4:26b python3 scoring/calibrate.py

# Against different Ollama
OLLAMA_URL=http://localhost:11434 CHOROS_MODEL=qwen3.6:35b-a3b python3 scoring/calibrate.py
```

## References

- PReMISE: Policy Rubrics as Measurement Specifications (ICLR 2026)
- 6 Ways LLM Judges Are Biased (Agentic AI & Cloud Advisory, 2026)
- JudgmentBench: Comparing Rubric and Preference Evaluation (2026)
- EACL 2026: Eliminate Judge Bias via Binary Scoring Agents (Kucia et al.)

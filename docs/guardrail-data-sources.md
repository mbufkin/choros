# Guardrail Data Sources — Choros

> These are the external datasets that provide ground truth for Choros's
> scoring, feedback, and misconception detection guardrails.
> Actual data files live in `.choros-data/teacher/buckets/guardrails/`
> and are NOT committed (district + student data).

## 1. ASAP-AES — Automated Essay Scoring

| Property | Value |
|---|---|
| **Source** | Hewlett Foundation Automated Student Assessment Prize |
| **Original size** | ~13,000 essays, 8 prompts, grades 7-10 |
| **Test set size** | 5 essays (curated) |
| **Score range** | 2-12 (holistic, sum of 2 raters) |
| **Essay types** | Argumentative, source-dependent, narrative |
| **What it builds** | Essay scoring calibration, rubric alignment |
| **File** | `asap-aes-test-set.tsv` |

### Test set composition

| ID | Score | Level | What it tests |
|---|---|---|---|
| test-005 | 2 | Below Basic | Poor spelling, no structure, short |
| test-001 | 3 | Below Basic | Simple claims, no support, brief |
| test-002 | 6 | Basic | Balanced view, some reasoning, short |
| test-003 | 8 | Proficient | Structured argument, evidence, counterargument |
| test-004 | 11 | Advanced | Full argument, evidence, nuance, style |

### How to scale up
Full dataset available on Kaggle: `kaggle competitions download -c asap-aes`
File: `training_set_rel3.tsv` — 12,978 rows

## 2. STAAR Algebra 1 — Released Test Items

| Property | Value |
|---|---|
| **Source** | Texas Education Agency (TEA) STAAR EOC |
| **Test set size** | 7 items |
| **Format** | Multiple choice (A-D) with distractor rationales |
| **TEKS standards** | A.2.C, A.3.C, A.5.A, A.5.C, A.7.A, A.8.A |
| **What it builds** | Math scoring, misconception detection, TEKS alignment |
| **File** | `staar-alg1-test-items.json` |

### Item coverage

| ID | TEKS | Topic | Difficulty |
|---|---|---|---|
| staar-alg1-001 | A.5.A | One-step equations | Easy |
| staar-alg1-002 | A.5.A | Two-step equations | Medium |
| staar-alg1-003 | A.2.C | Slope-intercept form | Medium |
| staar-alg1-004 | A.3.C | Slope from two points | Medium |
| staar-alg1-005 | A.5.C | Elimination method | Hard |
| staar-alg1-006 | A.8.A | Factoring trinomials | Hard |
| staar-alg1-007 | A.7.A | Quadratic applications | Hard |

### How to scale up
Full STAAR released tests available at: https://tea.texas.gov/data-reports/staar/staar-released-test-questions
Online practice tests at: https://txpt.cambiumtds.com/student/

## 3. RACE / CommonLit — Reading Comprehension

| Property | Value |
|---|---|
| **Source** | RACE dataset (ReAding Comprehension from Examinations) |
| **Original size** | ~28,000 questions, middle/high school |
| **Status** | Not yet staged — identified as available |
| **What it would build** | Reading comprehension scoring, distractor analysis |
| **Access** | https://www.cs.cmu.edu/~glai1/data/race/ |

## How these connect to Choros

```
Guardrail Data          Choros Feature
─────────────          ───────────────
ASAP-AES essays   →    Essay scoring engine
STAAR items       →    Math answer validator
RACE questions    →    Reading comprehension scoring

Each dataset provides:
┌─ Ground truth (correct answers / human scores)
├─ Distractor rationales (why wrong answers are wrong)
└─ Standard alignment (TEKS, grade level)
```

## Next step

Run the 5 ASAP essays + 7 STAAR items through crystallization as a
"guardrail calibration" pass. The model should:

1. Score each essay and compare to human scores
2. Answer each STAAR item and explain distractors
3. Flag where its reasoning diverges from the ground truth

This gives us a calibration baseline before any real student data enters the system.

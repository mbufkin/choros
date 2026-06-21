# Choros — Roadmap

## Now (POC — Tier 2 Baseline)

Build the full pipeline on a single 32B–35B model (Lenovo PGX). Prove the architecture.

- [ ] **Phase 1: Pre-School Setup** — document ingestion, calendar parsing, stateful teacher JSON file
- [ ] **Phase 2: Crystallization** — raw docs → structured curriculum map with checkpoints
- [ ] **Phase 3: Execution** — roster setup, pre-assessment, lesson generation, student pages, quiz/scoring
- [ ] Audit log implementation (every teacher action recorded)
- [ ] Session-based pacing with calendar-aware recalculation
- [ ] Class length awareness (45min vs 90min lesson generation)
- [ ] Excel/CSV fallback path for schools without per-student web access

### Scoring & Feedback Guardrails

LLM-as-judge calibration — measure and eliminate scoring compression bias before any student data enters the system. See `docs/scoring-bias-experiment.md` for full narrative.

- [x] Three-strategy calibration pipeline (holistic / binary agents / non-compensation)
- [x] Cross-model comparison (gemma4:26b, qwen3.6:35b, nemotron-cascade-2)
- [x] Cohen's Kappa + compression ratio metrics
- [x] Feedback audit — remove scoring, measure feedback quality
- [x] Two-pass experiment — prove bias lives in the scorer, not the observer
- [x] Form-fill experiment — model fills rubric checklist, Python computes score (independently converged on Rulers approach)
- [x] Synthetic rubric validation — test against known criterion counts
- [x] Academic landscape survey — papers, repos, conference talks cataloged (`docs/inspiration.md`)
- [x] Full journey documentation (`docs/scoring-bias-experiment.md`)
- [x] **Rulers-style evidence grounding** — model checks [x]/[/]/[ ] + provides verbatim quote. Python verifies quote exists in source. Tested across gemma4, phi4, qwen. (`calibrate.py` Strategy D)
- [x] **3-value checklist decisions** — [x] met (2), [/] partial (1), [ ] not met (0). Model fills form, Python reads boxes and counts.
- [x] **Post-hoc calibration layer** — ridge regression (poly deg 2) maps raw checklist counts → human score distribution. Best result: qwen3.6:35b ridge Kappa 0.545.
- [x] **Cross-model form-fill benchmark** — gemma4 (0.091), phi4 (0.318), qwen (0.545) ridge Kappa. Phi4 10x faster than gemma4.
- [ ] **Match types for rubric criteria** — EXACT / EXPLICIT / EQUIVALENT / SEMANTIC (from Laeyerz). Tells the model HOW strictly to match each rubric point.
- [ ] **Confidence flags per criterion** — Low-confidence decisions flagged for teacher review.
- [ ] **Consistency checker** — third grader axis. Does the student's answer hold together internally?
- [ ] **Pairwise comparison experiment** — JudgmentBench showed comparative beats rubrics for high-judgment domains.
- [ ] **Prompt sensitivity audit** — map what prompt wording changes affect bias (we saw -0.042 to 0.318).
- [ ] **STAAR item guardrail pass** — score 7 STAAR Algebra 1 items against ground truth.

## Next (Post-POC)

- Multi-classroom support (multiple teachers, multiple class periods)
- Cross-class student identity (join by student number/email)
- Content domain expansion beyond algebra (science, ELA, history)
- Teacher style learning — system adapts to individual teacher patterns
- MOY exam generation with item-level curriculum validation
- Export formats: printable worksheets (PDF), Google Forms quiz export

## Later (Production Scale)

- Tier 3 model support (70B+ for full crystallization and MOY generation)
- Google Drive integration (pull student work, push feedback)
- Authentication and roster management (no URL-based access)
- TEKS standards alignment for Texas
- District-level deployment (per-school instances with shared curriculum)
- SQLite/Postgres data layer
- Teacher collaboration — shared lesson libraries, peer review of generated content

## Not Yet (Deferred)

- PowerSchool, Google Classroom, Canvas LMS integration
- State-by-state standards mapping beyond Texas
- Real-time collaborative lessons
- Parent portal / guardian view
- Mobile native app (web-only, responsive)
- AI-driven student grouping or intervention recommendations beyond remediation

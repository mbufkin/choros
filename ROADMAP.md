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
- [x] Full journey documentation (`docs/scoring-bias-experiment.md`)
- [ ] **Match types for rubric criteria** — EXACT / EXPLICIT / EQUIVALENT / SEMANTIC (from Laeyerz). Tells the model HOW strictly to match each rubric point, not just WHAT to look for.
- [ ] **Confidence flags per criterion** — Low-confidence rubric points get flagged for teacher review. Human-in-the-loop hook.
- [ ] **Consistency checker** — third grader axis. Does the student's answer hold together internally? Are the steps logically consistent? Complements rubric + comparative.
- [ ] **Pairwise comparison experiment** — JudgmentBench showed comparative judgment beats rubrics for high-judgment domains. Run gemma4 in pairwise mode against our 5 essays + STAAR items.
- [ ] **Prompt sensitivity audit** — we saw Kappa swing from -0.042 to 0.318 on prompt changes alone. Systematically map what wording changes affect bias.
- [ ] **Cross-family model test** — does a different model family (Claude via API, or a non-Gemma local model) exhibit the same walk-down mechanism?
- [ ] **STAAR item guardrail pass** — score 7 STAAR Algebra 1 items against ground truth, flag divergences (per BASELINE.md)

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

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

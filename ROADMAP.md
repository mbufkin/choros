# Choros — Roadmap

## Now (Active POC)

Building the school classroom proof-of-concept: 1 teacher, 5 students, basic algebra.

- [ ] Multi-student data architecture
- [ ] Teacher dashboard with 3-bucket upload
- [ ] Crystallization engine — curriculum mapping from uploaded docs
- [ ] Lesson generation engine — algebra domain
- [ ] 5 individual student pages
- [ ] Deterministic grading + misconception pipeline
- [ ] Remediation auto-generation for next lesson cycle

## Next (Post-POC)

Once the POC pipeline is proven end-to-end:

- Multi-classroom support (multiple teachers, multiple class periods)
- Content domain expansion (science, ELA, history — validated per-domain)
- Student performance dashboards with longitudinal tracking
- Teacher style learning — system adapts to individual teacher patterns over time
- Export formats: printable worksheets (PDF), Google Forms quiz export

## Later (Production Scale)

- Google Drive integration (pull student work, push feedback)
- Authentication and roster management (no more URL-based access)
- TEKS standards alignment for Texas (first state)
- District-level deployment model (per-school instances with shared curriculum)
- SQLite/Postgres data layer (replace filesystem when scale demands)
- Teacher collaboration — shared lesson libraries, peer review of generated content

## Not Yet (Deferred)

- PowerSchool, Google Classroom, Canvas LMS integration
- State-by-state standards mapping beyond Texas
- Real-time collaborative lessons
- Parent portal / guardian view
- Mobile native app (web-only, responsive)
- AI-driven student grouping or intervention recommendations beyond remediation generation

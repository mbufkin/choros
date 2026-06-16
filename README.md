# Choros

χορός (*choros*) — Ancient Greek for a group that learns and performs together. A chorus isn't a crowd — it's trained, coordinated, better together. The teacher conducts; the students perform; the model sees patterns across the whole ensemble.

**A cohort AI teacher.** Upload curriculum documents, crystallize them into a structured map, generate lessons, deliver to students, get cross-student misconception analysis — all running on private hardware with no data leaving the network.

## What it does

1. **Teacher uploads** curriculum documents (textbook chapters, district scope-and-sequence, past worksheets)
2. **Crystallization pass** overnight — builds a structured curriculum map, identifies gaps
3. **Lesson generation** — produces ready-to-use lessons with pre-assessments, instruction, practice, and distractor rationale
4. **Students learn** on individual pages — lessons, quizzes, deterministic scoring, LLM feedback on wrong answers
5. **Teacher sees patterns** — which concepts are breaking down across the cohort, what misconceptions are repeating

## The Core Constraint

The model cannot go outside the documentation. Every lesson, question, and feedback response is grounded in the uploaded source documents. The AI doesn't invent curriculum — it segments, remixes, and delivers existing curriculum. The documentation is the single source of truth.

## Run it

```bash
# Point at the Lenovo
cp .env.example .env
# Edit .env if needed (defaults to Lenovo over Tailscale)

# Start
python3 server.py
# Teacher dashboard: http://localhost:8753/teacher
# Student pages:    http://localhost:8753/student/01/ through /05/
```

## Architecture

Split from [Phren](https://github.com/mbufkin/phren) — same zero-build architecture (HTML + vanilla JS + Python stdlib proxy). Phren handles single-learner self-study; Choros handles teacher-cohort instruction.

## Documentation

| Doc | Purpose |
|-----|---------|
| [PRODUCT.md](PRODUCT.md) | Product intent, phases, core principles, non-goals |
| [DESIGN.md](DESIGN.md) | Visual identity, color tokens, interaction model, system principles |
| [DECISIONS.md](DECISIONS.md) | Design decisions: decided, deferred, open questions |
| [MODELS.md](MODELS.md) | Hardware tiers: what each model size can do |
| [AGENTS.md](AGENTS.md) | Operating manual for coding agents |
| [ROADMAP.md](ROADMAP.md) | Now / Next / Later / Not Yet |

## The Trust Boundary

- **AI generates lessons** FROM uploaded documents — never from its own knowledge
- **AI analyzes misconceptions** — cross-student pattern detection
- **AI never scores mastery** — that's deterministic math, auditable and transparent
- **AI never makes pedagogical decisions** — the teacher approves, adjusts, or skips

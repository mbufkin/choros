# Choros — Design Decisions

Living document. Decisions made, decisions deferred, open questions.

## Decided

### No Minimum Document Set
Whatever the teacher uploads is what we work with. If they upload a syllabus that says "Algebra," the system produces output grounded in "Algebra" — nothing more. We cannot go outside the source. The system documents exactly what information it had and what it didn't have. This is a feature, not a limitation: when someone questions the output, the answer is visible.

### Documentation as Visibility
The system shows exactly what information it has AND what it doesn't have. Full transparency on the input side. This is a hidden superpower — when someone asks "why did the system do X," the answer is traceable to exactly which documents were provided and what was missing.

### Uncovered Standards Must Not Fail Silently
When a checkpoint is skipped or a standard isn't covered, the system flags it. Clear documentation during crystallization of what's covered and what's not. The teacher makes the decision to skip — the system records that the standard wasn't addressed.

### Class Type Documented at Crystallization
During the crystallization period, the system documents the type of class: 45-minute daily, 90-minute block, A/B schedule, 4x4 block. No confusion later about how lessons should be paced or structured. This is part of the calendar model.

### Model Is Completely Interchangeable
The harness constrains the model — not the other way around. The same prompts, the same guardrails, the same source-grounding works regardless of model size. Test with 32B local on Lenovo AND Claude full API. Document the differences. Not everyone can afford frontier models, but the system works for everyone.

### Checkpoint Dates Come from District Documentation
Ideally: Year at a Glance, Quarter at a Glance, Week at a Glance provided by the district. If not provided, the system produces one from syllabus + calendar because checkpoint pacing is basic pedagogy. If the generated checkpoints aren't good enough, fallback to documented adjustment — note what was used, flag for teacher review.

### Teacher Documentation Is the Hardest Problem
Teachers struggle to document even legally required items (industry-based certifications tied to school ratings). The system cannot solve this — it can only document what it receives and make the gaps visible. This is a district-level reality, not a product limitation.

### Model Is NOT Completely Interchangeable (Updated 2026-06-27)
The Phase 7 decision-tree experiment proved this assumption wrong at the 30B scale. Nemotron 3 Nano 30B A3B could not reliably route through the tree (4/20 essays misrouted as "Off-Task," 13/20 defaulted to "Novice"). Nemotron Super 49B *can* route correctly (0/20 misrouted). The floor for decision-tree grading is ~49B. Models below this threshold lack the reasoning capacity to evaluate quality dimensions consistently. This is now a documented constraint — the tree architecture works, but requires a model that can reason about abstract quality criteria.

### Phase 7 — Decision Tree Grading (2026-06-27)
Scoring bias lives in the scoring step, not the observation step. Every prior phase (1-6) asked models to assign a number and got systematic compression or inflation (Kappa 0.000-0.240). Phase 7 replaces number assignment with a yes/no decision tree grounded in quoted evidence.

**Architecture:** 8-node binary tree. Each node asks one quality question (task alignment → completeness → quality gate → correctness/clarity → depth). Model never outputs a score — the score is derived deterministically from the path taken.

**Results (Nemotron Super 49B, N=20 ASAP):**
- 5-level tree: Linear 0.358 / Quadratic 0.617
- 7-level expansion: Linear 0.376 / Quadratic 0.622 (no improvement — ceiling is node question quality, not bucket count)

**What works:** No compression. No inflation. Proper routing through all gates. Off-Task essays correctly identified (0 of 20 misrouted on 49B).

**What's stuck:** 0.36/0.62 ceiling. The depth gate is too lenient — essays with modest substance pass through to high scores. Fix requires node question calibration, not architecture changes.

**Model floor:** ~49B required. 30B models can't reliably evaluate quality dimensions.

Full documentation: [[50-Research/Phase 7 — Decision Tree Grading Architecture]]

## Deferred

### Pacing Adjustments (Lagging / Ahead)
The system will document that pacing can drift and will address how to handle it at a later date. Known problem, not yet solved. The audit log will record when pacing changes, but the mechanism for recalculation (auto-adjust vs. teacher-approve) is not yet decided.

### Mid-Year Transfer Students
When a student transfers in mid-year, the system will likely run an assessment to determine where they are relative to the class and suggest catch-up steps. The exact mechanism is deferred. Document it as a known scenario.

### Noise Threshold (Alert vs. Absorb)
The system needs a threshold for what triggers a teacher notification vs. what is silently absorbed. Too many alerts and teachers ignore the system. Not enough and they don't trust it. This will be discovered through testing, not decided in advance.

## Open Questions

- Who owns checkpoint placement — model proposes, teacher approves? What happens to lessons generated for a moved checkpoint?
- ICS vs. PDF vs. manual calendar entry?
- Cross-class student identity fallback when student number/email aren't consistent?
- Per-student vs. whole-class pre-assessment?
- MOY results visibility — just teacher, or department head? Privacy boundary?
- Teacher file size by June — can the model still load it into context?
- Frontier vs. local model split for lesson generation — batch job or real-time?
- Stateful teacher file: archived or carried forward to next year?

# Choros — Model Tiers

Choros degrades gracefully across hardware. Not every district has a data center. The system works at every tier — it just does more with more compute.

## Tier 1 — 8B–14B (Any Laptop)

**What it can do:**
- Lesson playback and quiz scoring (deterministic — no model needed for this part)
- Misconception tagging on student answers (structured output, low complexity)
- Basic gap report: "3 of 5 students missed questions tagged to standard 4.2"

**What it cannot do:**
- Crystallization from raw documents
- Lesson generation
- MOY exam creation
- Cross-cohort misconception clustering

**Use case:** Teacher provides their own lessons and MOY. Choros handles scoring, misconception tagging, and gap reports. The teacher enters structured data; the system finds the patterns.

---

## Tier 2 — 32B–35B (Lenovo ThinkStation PGX or Equivalent)

**Everything in Tier 1, plus:**
- Lesson generation from crystallized curriculum (structured, bounded by checkpoints)
- Pre-assessment and quiz generation with distractor rationale
- Remediation suggestions for individual students
- Session pacing calculation against calendar

**May struggle with:**
- Full crystallization from raw, unstructured documents
- MOY exam generation with full validation
- Dense textbook processing in a single pass

**Use case:** The target baseline. One machine handles a single school or small district. Teacher uploads syllabus + textbook → lessons generated → quizzes scored → gaps flagged. Crystallization and MOY generation may need to be chunked or run as overnight batch passes.

---

## Tier 3 — 70B+ (Multi-GPU or Cloud)

**Everything in Tier 2, plus:**
- Full crystallization pass — raw documents → structured curriculum map
- MOY exam generation with item-level validation against curriculum
- Cross-cohort misconception clustering across classrooms
- Year-end summary reports with longitudinal growth data
- State standards alignment verification

**Use case:** The Maserati. Larger single machine or multiple PGX units. One machine for daily lesson ops, one for overnight batch passes (crystallization, MOY generation). Transformative for districts that can afford it.

---

## Build Strategy

**Prove it on Tier 2 first.** Build for 32B local hardware as the baseline constraint. If the pipeline works at this tier, it works on better hardware with minimal changes — more tokens, better models, faster passes. If it doesn't work at 32B, no amount of scaling fixes the architecture.

**Tier 1 is the fallback, not the target.** It's the safety net for districts that can't afford hardware. It still provides value. It still respects the core principles. But it's not where the product shines.

**Tier 3 is the upgrade path, not the dependency.** Nobody needs a 70B model to get started. But when they see what Tier 2 does, the case for Tier 3 writes itself.

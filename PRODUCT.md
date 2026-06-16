# Choros — Product

## Product Intent

Choros is a **cohort AI teacher** that helps classroom teachers generate high-quality instructional materials from their own source documents, deliver them to students, and get actionable insight into what students are struggling with — all running on private hardware with no data leaving the network.

A teacher uploads their curriculum documents. The system crystallizes them into a structured map. It generates lessons from that map. Students complete them on individual pages. The teacher sees which concepts are breaking down across the cohort — not just scores, but specific misconception patterns.

## Target Users

**Classroom teachers (grades 6–12)**
- New teachers who barely understand the content and are surviving day-to-day
- Mid-career teachers who know their content but spend hours adapting curriculum into usable materials
- Veteran teachers who have deep expertise but face rigid district requirements

## The Core Constraint: Documentation as Single Source of Truth

The model cannot go outside the documentation. Every lesson, every question, every feedback response must be grounded in the uploaded source documents. The AI doesn't invent curriculum — it segments, remixes, and delivers existing curriculum.

This is not a limitation. It's the safety mechanism that prevents drift. When the documentation is complete, the model has nowhere to drift *to*.

## Jobs to Be Done

1. **"Turn my curriculum into something I can actually use tomorrow."** Teacher uploads textbook chapters, district scope-and-sequence, and their own past worksheets. System produces ready-to-use lessons in their style.

2. **"Show me what my students actually don't understand."** Not just scores — which specific concepts are breaking down, and why (which wrong answer pattern → which misconception).

3. **"Don't make me learn new software."** The system adapts to existing teacher workflows — upload documents, click a few buttons, get results. No chat, no prompt engineering, no AI literacy required.

4. **"Keep my students' data private."** Everything runs on local hardware. No cloud, no API keys shared with students, no data leaving the building.

## MVP Scope (POC)

- 1 teacher, 5 students, basic algebra
- 3-bucket upload (curriculum / district / teacher)
- Overnight crystallization pass → curriculum map + gap report
- Weekly lesson generation (pre-assessment + new content + practice)
- 5 individual student pages
- Deterministic quiz scoring + LLM misconception analysis
- Auto-generated remediation for next lesson cycle
- All local, no external integrations

## Non-Goals

- Replacing curriculum — Choros segments and delivers existing curriculum, doesn't create new scope-and-sequence
- Replacing teachers — the teacher makes pedagogical decisions; Choros provides tools and data
- Real-time teacher-model chat — interactions are buttons, decisions, approvals; no back-and-forth
- LMS integration (PowerSchool, Google Classroom) — deferred beyond POC
- State standards alignment (TEKS) — deferred beyond POC
- District-scale deployment (50,000+ students) — architecture is POC-scale by design
- Single-learner self-study — that's Phren's domain

## Relationship to Phren

| Concern | Phren | Choros |
|---------|-------|--------|
| User | Individual learner | Teacher + cohort |
| Content source | Any document | Curriculum documents |
| Data model | Single timeline | Cross-student aggregation |
| AI role | Personal coach | Force multiplier |
| Output | Interactive course | Lessons + cohort analytics |
| Scale | 1 student | 1 teacher, N students |

## Success Criteria (POC)

- Teacher uploads 3 document buckets → receives actionable curriculum map within one overnight pass
- System generates 5 algebra lessons with pre-assessments, instruction, and practice with distractor rationale
- 5 students complete lessons on individual pages and receive misconception-specific feedback on wrong answers
- Aggregate gap report identifies common misconceptions across students
- Remediation content is auto-generated and addresses the identified gaps
- Zero data leaves the local network

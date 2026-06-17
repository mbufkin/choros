# Baseline Data — Crystallization Run #1

> **These files are staged locally but NOT committed to git.**
> They contain real DISD data and curriculum documents owned by Dallas ISD.
> This document serves as the public record of what the baseline contains
> and how to reproduce it.

## Data staged (`.choros-data/teacher/buckets/`)

### district/ — District Calendar & Policies

| File | Source | Description |
|------|--------|-------------|
| `calendar-25-26.json` | DISD approved calendar (dallasisd.org) | Full 2025-26 school year: grading periods, holidays, PD days, 177 instructional days. Public information, but staged locally for crystallization. |

### curriculum/ — Course Scope & Sequence

| File | Source | Description |
|------|--------|-------------|
| `algebra1-scope-and-sequence.txt` | TEKS-informed, DISD CTE dept, Choros domain model (`domains/algebra.py`) | Full-year Algebra 1 curriculum: 9 units, 34 instructional weeks, 170+ topics. STAAR EOC-aligned. Each week has 5 daily topics with descriptions. Includes assessment structure and pacing notes. |

### teacher/ — Teacher Preferences & Context

| File | Status | Description |
|------|--------|-------------|
| *(none yet)* | TBD | Teacher preferences (style, pacing preferences, known trouble spots) will be populated from real teacher input after first crystallization run. |

## How to reproduce

1. Calendar: Download from https://www.dallasisd.org/calendar → structure as JSON
2. Curriculum: Built from `domains/algebra.py` TOPIC_PROGRESSION + TEKS standards → expanded into full scope-and-sequence with weekly detail
3. Teacher bucket: Empty for now — will be populated after first crystallization with real teacher feedback

## What crystallization should produce

With these two buckets (district + curriculum), the crystallization engine should produce:
- A full year-at-a-glance curriculum map
- 9 units spanning 34 weeks with 2 flex weeks
- Pacing aligned to the DISD calendar (6 six-week grading periods)
- Gaps flagged where the curriculum and district calendar conflict
- Checkpoint suggestions aligned to grading period boundaries

## First run target

Run crystallization against this baseline, then put the resulting report in front of:
1. Emily (pediatrician — understands learning variability)
2. A real DISD CTE teacher (domain expert who can spot curriculum gaps)

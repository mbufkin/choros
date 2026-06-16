# Choros — Design

## Visual Identity

### Project Logo

Symbol mark: Greek letter **χ (chi)** — copper, stylized with flared serif arms converging at center, small diamond accent below, convergence dots suggesting individual paths meeting at the crossing point.

Source: `../project-logos/choros-symbol.html`
Production PNG: `../project-logos/choros-symbol-1280x640.png`

### Design DNA

Dark, academic, minimal. The teacher dashboard should feel like a well-organized gradebook — high density without clutter, data-forward, everything actionable in one or two clicks. The student view mirrors Phren's clean lesson experience.

### Color Tokens

```
Background:    #0f172a (slate-900) → main surface
Background alt: #1e293b (slate-800) → cards, panels
Surface:        #334155 (slate-700) → input fields, elevated surfaces
Border:         rgba(255,255,255,0.05) → subtle dividers

Brand primary:  #c97d60 (copper) → buttons, links, active states, logo
Brand hover:    #d4957a (copper-400) → hover
Brand muted:    #a85d40 (copper-700) → pressed, inactive

Text primary:   #e2e8f0 (slate-200) → body
Text secondary: #94a3b8 (slate-400) → labels, captions
Text muted:     #64748b (slate-500) → disabled, placeholder

Success:        #22c55e (green-500) → correct answers, passing scores
Warning:        #f59e0b (amber-500) → partial, needs review
Error:          #ef4444 (red-500) → wrong answers, gaps

Accent gold:    #c8a84e → special highlights (matches symbol mark gold crest)
```

### Typography

```
Family: Inter (Google Fonts, loaded via CDN)
Weights: 400 (body), 500 (labels), 600 (headings), 700 (display), 800-900 (hero)

Body:       text-base (16px) leading-relaxed
Captions:   text-sm (14px)
Headings:   text-xl → text-3xl font-bold tracking-tight
Hero:       text-4xl → text-6xl font-extrabold tracking-tight
Mono:       font-mono for scores, data, file paths
```

### Spacing Scale

```
xs: 4px (0.25rem)   — icon padding
sm: 8px (0.5rem)    — inline gaps
md: 16px (1rem)     — card padding, section gaps
lg: 24px (1.5rem)   — screen padding, major sections
xl: 32px (2rem)     — page margins
2xl: 48px (3rem)    — hero sections
```

## Interaction Model

### Teacher Interactions: Buttons Only

Teachers never type free-form text to the model. Every interaction is a deterministic choice:

| Context | Options |
|---------|---------|
| Crystallization report review | Approve / Request More / Flag Issue / Upload Additional |
| Lesson bundle review | Accept / Adjust Pacing / Skip |
| Remediation review | Include in Next Lesson / Skip |
| Student progress view | Read-only (no teacher action required) |

**Rationale:** Prevents the "blank text box" paralysis that kills teacher adoption. Reduces compute load (no back-and-forth LLM calls). Makes teacher decisions auditable and reversible.

### Student Interactions: Consume → Respond → Submit

Students follow a linear flow through each lesson:
1. **Pre-check** — quick assessment to verify prerequisite knowledge
2. **Learn** — read instruction, worked examples
3. **Practice** — answer questions with multiple-choice distractors
4. **Submit** — see deterministic scores immediately, LLM feedback on wrong answers

### Navigation

```
Teacher:
  /teacher → Dashboard (upload buckets, crystallization status, student overview)

Student:
  /student/01/ → Lesson list → Active lesson → Results
  /student/02/ → (same, independent progress)
  ...
  /student/05/
```

### Animation

- Screen transitions: fade-in (400ms, translateY 8px)
- Progress fill: cubic-bezier ease transition (400ms)
- Loading: CSS spin animation on brand spinner SVG
- No page reloads — all navigation via screen router

### Responsive

- Max width: `max-w-6xl` (72rem / 1152px) centered
- Mobile: single-column, reduced padding
- Desktop: two-column grids where appropriate (dashboard + detail panel)
- Dark mode only — no light mode toggle (academic focus, eye comfort)

## System Principles

### Audit Log

Every teacher action that modifies system state is recorded in the stateful teacher JSON file. This is non-negotiable.

| Action | Recorded |
|--------|----------|
| Crystallization approved | Timestamp, document set, checkpoint map |
| Lesson bundle accepted | Timestamp, lesson IDs, any adjustments |
| Pacing adjusted | Timestamp, old dates, new dates, reason |
| Remediation skipped for student | Timestamp, student ID, item skipped |
| Quiz generated | Timestamp, parameters (count, topic, type) |

The audit log is the legal and professional record. If something goes wrong, the system proves what decision was made and when. This protects both the teacher and the system.

### Support Without Judgment

Choros never sorts teachers into categories. No labels. No tiers. No "remedial" flags. Good teachers receive sharper insight because the data supports it. Struggling teachers receive stronger scaffolding because the system provides more structure. The teacher experience adapts, but the system never pronounces judgment on the teacher.

### Degrade Gracefully

The system works across hardware tiers. A 120B model on multi-GPU hardware runs the full pipeline. A 32B model on a single workstation runs core features. A laptop with no local model handles scoring and gap reports from teacher-provided data. The UI is the same. The principles are the same. The capabilities differ silently.

## Anti-Patterns (Do Not)

- ❌ Light mode or theme toggle — dark only
- ❌ Chat bubbles or conversational UI for teacher interactions
- ❌ "AI wrote this" disclaimers — trust is built through correctness, not warnings
- ❌ Skeleton loaders or excessive animation — keep it fast and direct
- ❌ Modal dialogs — use inline panels and screen transitions
- ❌ npm, bundlers, frameworks — zero-build classic scripts only
- ❌ Model generating outside source documents — drift is the enemy

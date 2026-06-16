# Choros — Agent Operating Manual

For Hermes, Codex CLI, OpenCode, Claude Code, and any other coding agents working on this repo.

## Read This First

Before touching any file, read:
1. `PRODUCT.md` — what we're building and why. Non-goals are as important as goals.
2. `DESIGN.md` — color tokens, interaction model, do/don'ts. Respect the dark theme.

## The Prime Directive

**Zero build step. Classic `<script>` tags. No npm, no bundler, no ES modules, no framework.**

Every `.js` file is loaded by a `<script>` tag in the HTML. They share one global namespace. This is a feature, not a bug. Do not "modernize" it.

If you add a dependency, it must be:
- A CDN `<script>` tag (Tailwind, Inter font)
- A Python stdlib module (the server uses zero pip packages)
- That's it. No exceptions.

## The Core Constraint

**The model cannot generate outside the uploaded source documents.** Every lesson, question, and feedback response must be grounded in the teacher's curriculum documents. The AI doesn't invent — it segments, remixes, and delivers. The documentation is the single source of truth.

## File Conventions

### HTML: one page per role
- **teacher.html** — teacher dashboard (upload buckets, crystallization status, student overview, gap reports)
- **student.html** — student page (lesson list, active lesson, results)

### Python: stdlib only
- **server.py** — HTTP server + LLM proxy + teacher/student API
- **workspace.py** — filesystem persistence (MultiWorkspace, per-student tracking)
- **crystallize.py** — overnight curriculum mapping pass
- **gen_lessons.py** — lesson generation from crystallized curriculum
- **domains/*.py** — subject-specific helpers (algebra.py, etc.)

### JavaScript: no build, no modules
- **teacher.js** — dashboard logic, upload handling, report rendering
- **student.js** — lesson playback, quiz interaction, results display

### Data: filesystem as database

```
.choros-data/                   ← all teacher/student state
  teacher/                      ← teacher state, uploads, reports
    buckets/                    ← uploaded source documents
    crystallization/            ← curriculum map + gap report
    lessons/                    ← generated lesson bundles
  students/<id>/                ← per-student progress, feedback
    learning-records/           ← completed lesson records
```

JSON files are human-readable and git-ignored. Create directories on first write.

## LLM Integration Rules

1. **Never leak the API key.** The client calls `/api/generate` — the server reads `.env` and proxies.
2. **Guardrail the model with source material.** Every LLM prompt includes the uploaded documents. The model generates FROM those documents, never from its own knowledge.
3. **Deterministic scoring is separate from LLM feedback.** Right/wrong is math. "Why" is LLM. Never let the LLM assign a score.
4. **Teacher batch jobs are async.** Crystallization and lesson generation are offline passes. The teacher triggers them, gets a job ID, polls for completion.

## When Adding a Feature

1. Check `PRODUCT.md` — is it in scope?
2. Check `DESIGN.md` — does it follow interaction model (buttons not chat for teachers)?
3. If the answer is no to either, update the doc first, then build.

## Commit Style

```
type: what changed

feat: add teacher upload endpoint
fix: state corruption on student replay
docs: add PRODUCT.md with cohort model
refactor: extract Workspace to workspace.py
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

# Getting Structured Output from a 26B Model — What Actually Worked

**June 21, 2026 · gemma4:26b on Lenovo CUDA**

## The Goal

Feed student essays to a local model and get back *usable, specific, correlated* feedback — something a teacher could hand to a student or a curriculum designer could learn from. No API calls, no 400B models. Just the hardware in the closet.

## What We Tried

### Attempt 1: Schema-Enforced JSON (Way A)

Prompt the model with a rubric and a JSON schema. Ask for structured scoring output — thesis, evidence count, evidence quality, counter-argument, organization, mechanics, depth. Each criterion gets a `[x]` / `[/]` / `[ ]` check plus an evidence quote.

**Result: Complete failure.** Across 5 essays, gemma4:26b produced **zero** substantive quotes. Every evidence field returned `"none"`. The model could fill out the JSON structure, but it couldn't populate it with actual observations. It was checking boxes, not reading essays.

| Essay | Human Score | Substantive Quotes |
|-------|------------|-------------------|
| Below Basic-01 | 2 | 0 |
| Below Basic-02 | 3 | 0 |
| Basic-03 | 6 | 0 |
| Proficient-04 | 8 | 0 |
| Advanced-05 | 11 | 0 |

### Attempt 2: Two-Pass (Way B)

**Pass 1:** Ask the model to write blunt, teacher-style feedback in free text. Quote specific sentences. Say what's missing. No scores, no rubrics, no JSON.

**Pass 2:** Feed that feedback back into the model and ask it to extract structured scores into JSON.

#### Pass 1 Result: Works
The blunt feedback is genuinely good. Across 5 essays, gemma4:26b produced an average of **5.2 substantial, quoted observations** per essay. The feedback points to specific sentences, names what's missing, and doesn't pull punches on weak writing.

#### Pass 2 Result: Brick Wall
5/5 JSON extraction attempts **failed to parse**. The model consistently regurgitated the system prompt instead of producing a JSON object. Classic small-model structured-output collapse: when asked to switch from free-text generation to constrained output, it falls back to describing what it's supposed to do rather than doing it.

```
PARSE FAILED: Expecting value: line 1 column 1 (char 0)
Raw: * Input: Teacher feedback text.
      * Task: Extract scores into a specific JSON format.
      * Rules: Use ONLY explicit statements...
```

## Why This Happens

gemma4:26b is a 26B model — capable of strong free-text reasoning but brittle on structured generation. Two specific failure modes:

1. **JSON schema enforcement bleeds instruction-following:** The model's training on "follow the format" overpowers its training on "read the essay." It fills in the structure correctly but can't simultaneously attend to the essay content.

2. **Context-switch collapse:** Moving from Pass 1 (creative, generative) to Pass 2 (constrained, extractive) within the same pipeline triggers a mode shift the model can't reliably execute. It "forgets" it's supposed to output JSON and instead explains the task.

Larger models (70B+) handle this fine. But we're committed to local inference on the hardware we have.

## What Actually Works

**Skip structured extraction entirely.** The blunt free-text feedback IS the output.

The two-column PDF layout — essay on the left, feedback on the right — gives a teacher everything they need without forcing the model into a format it can't produce. Correlation is spatial, not programmatic: each essay and its feedback share a page.

### The Prompt That Works

```
You are a classroom teacher providing feedback on a student essay.

Read the student's essay below and write the feedback you would give them.

Rules:
- Write in plain English, like you're talking to the student
- Point out specific strengths (quote the essay if helpful)
- Point out specific weaknesses or things to improve
- Be honest — don't praise if there's nothing to praise
- If the essay is weak, say what's missing and how to fix it
- No scores, no grades, no rubrics — just feedback
```

### Performance (Lenovo CUDA)

| Metric | Value |
|--------|-------|
| Avg words per feedback | 266 |
| Avg time per essay | ~20s |
| Substantive quotes per essay | 5.2 |
| Parse failures | 0 (no parsing needed) |

## The Principle

**Don't make a 26B model do a 70B model's job.** gemma4:26b is a strong reader and a blunt critic. It's not a structured data extractor. Play to its strengths: let it talk like a teacher, not like a JSON API.

If structured scoring is needed downstream, run it on a larger model — or accept that the free-text feedback is the richer artifact anyway. A teacher reading "Your conclusion doesn't follow from your evidence — here's the sentence where you lost the thread" gets more than a `MECHANICS: [x]` checkbox ever could.

## Next Steps

- Scale to full ASAP essay set (200+ essays)
- Test the same pipeline on qwen3.6:35b (may handle JSON extraction, but feedback quality may differ)
- Consider hybrid: blunt feedback from gemma4:26b, structured extraction from a single API call to a larger model (cheap — the feedback text is only ~250 words)

---

*Generated with: choros/scoring/tsa_feedback_pdf.py · Model: gemma4:26b (unsloth GGUF, Lenovo CUDA llama.cpp)*

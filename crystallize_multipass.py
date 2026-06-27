#!/usr/bin/env python3
"""
Multi-pass crystallization — breaks the full crystallization prompt into
6 sequential calls. Each pass has a focused task and simple output schema.
Designed for 35B models that can't handle the full prompt in one shot.

Pass 1: Document inventory — identify what's provided
Pass 2: Unit extraction — list every unit with standards
Pass 3: Checkpoint mapping — find all assessments and milestones
Pass 4: Gap analysis — what's missing or underspecified
Pass 5: Coverage summary — count standards coverage
Pass 6: Pacing calendar — build the week-by-week schedule
"""
import json, time, urllib.request, os, sys
from pathlib import Path
from typing import Any

LLAMACPP = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")
DATA_DIR = Path(__file__).resolve().parent / ".phren-data" / "teacher"
OUTPUT_PATH = Path(__file__).resolve().parent / ".phren-data" / "teacher" / "crystallization_report.json"


def load_docs() -> list[dict]:
    """Load all documents from the three buckets."""
    docs = []
    for bucket in ["curriculum", "district", "teacher"]:
        bpath = DATA_DIR / bucket
        if not bpath.exists():
            continue
        for fname in sorted(os.listdir(bpath)):
            with open(bpath / fname) as f:
                docs.append({"bucket": bucket, "name": fname, "text": f.read()})
    return docs


def call_model(prompt: str, schema: dict, max_tokens: int = 4096, timeout: int = 300) -> dict | None:
    """Call llama.cpp with json_schema enforcement on raw completions."""
    payload = json.dumps({
        "prompt": prompt,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "output", "schema": schema},
        },
    }).encode()

    req = urllib.request.Request(
        f"{LLAMACPP}/v1/completions", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

    content = data["choices"][0].get("text", "")
    
    # Strip thinking tags if leaked
    if '<think>' in content:
        idx = content.find('</think>')
        if idx > 0:
            content = content[idx + 8:].strip()

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        print(f"  JSON parse failed. Raw: {content[:200]}...")
        return None


def fmt_docs(docs: list[dict]) -> str:
    """Format documents for inclusion in prompts."""
    out = ""
    for d in docs:
        out += f"### [{d['bucket'].upper()}] {d['name']}\n{d['text']}\n\n"
    return out


# ── PASS 1: Document Inventory ──
PASS1_PROMPT = """You are analyzing educational documents. Your ONLY job: identify what each document is.

For each document provided, determine:
- What type of document is it? (syllabus, pacing_guide, textbook_toc, district_standard, teacher_note, calendar, assessment_schedule)
- What subject and grade level?
- What time span does it cover?
- Is it clear, partial, or vague?

Do NOT extract units, standards, or curriculum content. Do NOT analyze gaps.
ONLY identify what each document IS.

DOCUMENTS:
{docs}

Output ONLY the JSON object."""

PASS1_SCHEMA = {
    "type": "object",
    "properties": {
        "documents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "subject": {"type": "string"},
                    "grade_level": {"type": "string"},
                    "time_span": {"type": "string"},
                    "clarity": {"type": "string"},
                },
                "required": ["name", "type", "subject", "grade_level", "time_span", "clarity"],
            }
        }
    },
    "required": ["documents"],
}

# ── PASS 2: Unit Extraction ──
PASS2_PROMPT = """You have already identified these documents:
{inventory}

Now extract EVERY instructional unit from the documents. A unit is a named block of instruction with a defined topic.

For each unit:
- Name (exact wording from source)
- Sequence position (1st, 2nd, 3rd...)
- Duration in weeks (as stated in source)
- Standards or objectives listed for that unit (verbatim)
- Which document it came from

If a unit is implied but not explicitly named, list what you CAN find and flag it.
Do NOT invent unit names, standards, or durations.

DOCUMENTS:
{docs}

Output ONLY the JSON object."""

PASS2_SCHEMA = {
    "type": "object",
    "properties": {
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "unit": {"type": "string"},
                    "sequence": {"type": "integer"},
                    "duration_weeks": {"type": "number"},
                    "standards": {"type": "array", "items": {"type": "string"}},
                    "source_doc": {"type": "string"},
                    "explicit": {"type": "boolean"},
                },
                "required": ["unit", "sequence", "duration_weeks", "standards", "source_doc"],
            }
        }
    },
    "required": ["units"],
}

# ── PASS 3: Checkpoint Mapping ──
PASS3_PROMPT = """Units extracted so far:
{units_summary}

Now identify every assessment, exam, quiz, review, or milestone mentioned in the documents.

For each checkpoint:
- Description (what is being assessed)
- Date or week (as stated in source — if relative like "Week 6", state it as-is)
- Which unit it assesses
- Source document

If a unit has no associated checkpoint, flag it.
Do NOT invent checkpoints or dates.

DOCUMENTS:
{docs}

Output ONLY the JSON object."""

PASS3_SCHEMA = {
    "type": "object",
    "properties": {
        "checkpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "date_or_week": {"type": "string"},
                    "assesses_unit": {"type": "integer"},
                    "source_doc": {"type": "string"},
                },
                "required": ["description", "date_or_week", "assesses_unit", "source_doc"],
            }
        },
        "units_without_checkpoints": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["checkpoints", "units_without_checkpoints"],
}

# ── PASS 4: Gap Analysis ──
PASS4_PROMPT = """You have extracted:
Units: {units_summary}
Checkpoints: {checkpoints_summary}

Now identify gaps — what is missing, underspecified, or contradictory across these documents.

Flag:
- Standards mentioned but not assigned to any unit
- Units lacking standards or objectives
- Topics implied by unit names but not detailed
- Missing assessment points
- Time gaps (units don't fill available calendar)
- Prerequisites mentioned but not taught earlier
- Contradictions between documents

For each gap: describe what's missing, rate severity (critical/moderate/minor),
and state which document comparison revealed it.

Do NOT invent content to fill gaps — just identify them.

DOCUMENTS:
{docs}

Output ONLY the JSON object."""

PASS4_SCHEMA = {
    "type": "object",
    "properties": {
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "severity": {"type": "string"},
                    "inferred_from": {"type": "string"},
                },
                "required": ["description", "severity", "inferred_from"],
            }
        }
    },
    "required": ["gaps"],
}

# ── PASS 5: Coverage Summary ──
PASS5_PROMPT = """Based on the extracted units:
{units_summary}

Count the standards coverage:
- Total number of unique standards across all documents
- Number of standards explicitly covered by at least one unit
- Number of standards mentioned but not mapped to instruction
- Number with partial coverage

Be precise. Use ONLY the standards listed in the units above.

Output ONLY the JSON object."""

PASS5_SCHEMA = {
    "type": "object",
    "properties": {
        "total_standards": {"type": "integer"},
        "covered": {"type": "integer"},
        "uncovered": {"type": "integer"},
        "partial": {"type": "integer"},
        "notes": {"type": "string"},
    },
    "required": ["total_standards", "covered", "uncovered", "partial"],
}

# ── PASS 6: Pacing Calendar ──
PASS6_PROMPT = """Units extracted:
{units_summary}

Checkpoints identified:
{checkpoints_summary}

Build a week-by-week pacing calendar using ONLY dates found in the documents.
Use the earliest date found as the start, the latest as the end.
If dates are specified relative to units (e.g. "Weeks 1-3"), convert using the calendar information.
Record the calendar type if mentioned (45-min daily, 90-min block, A/B schedule).

Do NOT invent dates. If dates are missing, state "not specified in documents."

DOCUMENTS:
{docs}

Output ONLY the JSON object."""

PASS6_SCHEMA = {
    "type": "object",
    "properties": {
        "mapped_weeks": {"type": "integer"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "calendar_type": {"type": "string"},
        "source_doc": {"type": "string"},
    },
    "required": ["mapped_weeks", "start_date", "end_date", "calendar_type"],
}


def main():
    docs = load_docs()
    if not docs:
        print("No documents found.")
        sys.exit(1)

    doc_text = fmt_docs(docs)
    print(f"Documents: {len(docs)} ({sum(len(d['text']) for d in docs):,} chars total)\n")

    report: dict[str, Any] = {}
    timings: dict[str, float] = {}

    # ── PASS 1: Inventory ──
    print("=" * 60)
    print("PASS 1: Document Inventory")
    t0 = time.time()
    r1 = call_model(PASS1_PROMPT.format(docs=doc_text), PASS1_SCHEMA)
    t1 = time.time() - t0
    timings["pass1"] = t1

    if r1:
        inv = r1.get("documents", [])
        report["document_inventory"] = inv
        print(f"  ✓ {len(inv)} documents identified [{t1:.0f}s]")
        for d in inv:
            print(f"    [{d.get('type','?')}] {d.get('name','?')} — {d.get('clarity','?')}")
    else:
        print(f"  ✗ Failed [{t1:.0f}s]")
        sys.exit(1)

    # ── PASS 2: Units ──
    print(f"\n{'=' * 60}")
    print("PASS 2: Unit Extraction")
    inv_summary = json.dumps(r1, indent=2)
    t0 = time.time()
    r2 = call_model(
        PASS2_PROMPT.format(inventory=inv_summary, docs=doc_text),
        PASS2_SCHEMA, max_tokens=4096
    )
    t2 = time.time() - t0
    timings["pass2"] = t2

    if r2:
        units = r2.get("units", [])
        report["syllabus"] = units
        print(f"  ✓ {len(units)} units extracted [{t2:.0f}s]")
        for u in units:
            st = u.get("standards", [])
            src = "✓" if u.get("explicit") else "?"
            print(f"    {src} Unit {u.get('sequence','?')}: {u.get('unit','?')} ({u.get('duration_weeks','?')}w) — {len(st)} standards [{u.get('source_doc','?')}]")
    else:
        print(f"  ✗ Failed [{t2:.0f}s]")
        sys.exit(1)

    # ── PASS 3: Checkpoints ──
    print(f"\n{'=' * 60}")
    print("PASS 3: Checkpoint Mapping")
    units_summary = json.dumps([{"seq": u["sequence"], "unit": u["unit"], "weeks": u.get("duration_weeks")} for u in units], indent=2)
    t0 = time.time()
    r3 = call_model(
        PASS3_PROMPT.format(units_summary=units_summary, docs=doc_text),
        PASS3_SCHEMA, max_tokens=4096
    )
    t3 = time.time() - t0
    timings["pass3"] = t3

    if r3:
        cps = r3.get("checkpoints", [])
        missing = r3.get("units_without_checkpoints", [])
        report["checkpoints"] = cps
        report["units_without_checkpoints"] = missing
        print(f"  ✓ {len(cps)} checkpoints found [{t3:.0f}s]")
        for cp in cps:
            print(f"    Unit {cp.get('assesses_unit','?')}: {cp.get('description','?')[:80]} — {cp.get('date_or_week','?')}")
        if missing:
            print(f"  ⚠ Units without checkpoints: {missing}")
    else:
        print(f"  ✗ Failed [{t3:.0f}s]")
        sys.exit(1)

    # ── PASS 4: Gaps ──
    print(f"\n{'=' * 60}")
    print("PASS 4: Gap Analysis")
    checkpoints_summary = json.dumps(cps, indent=2) if r3 else "[]"
    t0 = time.time()
    r4 = call_model(
        PASS4_PROMPT.format(units_summary=units_summary, checkpoints_summary=checkpoints_summary, docs=doc_text),
        PASS4_SCHEMA, max_tokens=4096
    )
    t4 = time.time() - t0
    timings["pass4"] = t4

    if r4:
        gaps = r4.get("gaps", [])
        report["gaps"] = gaps
        print(f"  ✓ {len(gaps)} gaps identified [{t4:.0f}s]")
        for g in gaps[:5]:
            print(f"    [{g.get('severity','?')}] {g.get('description','')[:120]}")
    else:
        print(f"  ✗ Failed [{t4:.0f}s]")
        sys.exit(1)

    # ── PASS 5: Coverage ──
    print(f"\n{'=' * 60}")
    print("PASS 5: Coverage Summary")
    t0 = time.time()
    r5 = call_model(
        PASS5_PROMPT.format(units_summary=units_summary),
        PASS5_SCHEMA, max_tokens=2048
    )
    t5 = time.time() - t0
    timings["pass5"] = t5

    if r5:
        report["coverage"] = r5
        print(f"  ✓ {r5.get('covered',0)}/{r5.get('total_standards',0)} covered [{t5:.0f}s]")
    else:
        print(f"  ✗ Failed [{t5:.0f}s]")

    # ── PASS 6: Pacing ──
    print(f"\n{'=' * 60}")
    print("PASS 6: Pacing Calendar")
    t0 = time.time()
    r6 = call_model(
        PASS6_PROMPT.format(units_summary=units_summary, checkpoints_summary=checkpoints_summary, docs=doc_text),
        PASS6_SCHEMA, max_tokens=2048
    )
    t6 = time.time() - t0
    timings["pass6"] = t6

    if r6:
        report["pacing"] = r6
        print(f"  ✓ {r6.get('mapped_weeks','?')} weeks [{t6:.0f}s]")
    else:
        print(f"  ✗ Failed [{t6:.0f}s]")

    # ── Save ──
    report["_meta"] = {
        "model": "qwen3.6:35b",
        "backend": "llamacpp-cuda",
        "method": "multi-pass (6 sequential calls)",
        "timings": timings,
        "total_time_s": round(sum(timings.values()), 1),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✓ Full crystallization complete in {sum(timings.values()):.0f}s")
    print(f"  Units: {len(report.get('syllabus',[]))}")
    print(f"  Checkpoints: {len(report.get('checkpoints',[]))}")
    print(f"  Gaps: {len(report.get('gaps',[]))}")
    print(f"  Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

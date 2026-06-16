#!/usr/bin/env python3
"""
gen-lessons.py — lesson generation engine for Phren school mode.

Reads the crystallization report from the teacher workspace, calls the
configured LLM to generate 5 lessons for one week of algebra instruction,
validates the output, and saves each lesson as a JSON file.

Can be used standalone (python3 gen-lessons.py) or imported as a module
(from gen_lessons import run_lesson_generation).

Stdlib only. Depends on workspace.py and domains/algebra.py.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

from workspace import TeacherWorkspace

# ---- Backend configuration (same env vars as server.py) ----


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'\"")
            os.environ.setdefault(key, value)


_load_dotenv()

BACKEND = {
    "base_url": os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
    "model": os.environ.get("LLM_MODEL", "qwen2.5-coder:32b"),
    "api_key": os.environ.get("LLM_API_KEY", ""),
}
LLM_TIMEOUT_S = int(os.environ.get("LLM_TIMEOUT_S", "600"))


def load_prompt(name="gen-lessons.txt") -> str:
    prompt_path = Path("prompts") / name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


# ---- Core function ----


def run_lesson_generation(
    workspace: TeacherWorkspace | None = None,
    backend: dict | None = None,
    week: int = 1,
    prompt_name: str = "gen-lessons.txt",
    validate: bool = True,
) -> dict:
    """Generate 5 lessons for one week from the crystallization report.

    Args:
        workspace: TeacherWorkspace with crystallization report.
        backend: Dict with base_url, model, api_key keys.
        week: Week number to generate (1-indexed).
        prompt_name: Prompt file in prompts/ directory.
        validate: If True, validate each lesson and report issues.

    Returns:
        dict with keys: ok, lessons, model, ms, issues (if validate=True).
    """
    if workspace is None:
        workspace = TeacherWorkspace()
    if backend is None:
        backend = BACKEND

    # ---- 1. Read the crystallization report ----
    report = workspace.get_report()
    if report is None:
        return {
            "ok": False,
            "error": "No crystallization report found. Run crystallize.py first.",
        }

    # ---- 2. Build the prompt ----
    system_prompt = load_prompt(prompt_name)

    # Build a concise summary of the syllabus for the prompt
    syllabus_summary = []
    for unit in report.get("syllabus", []):
        u = unit.get("unit", "?")
        title = unit.get("title", "Untitled")
        topics = unit.get("topics", [])
        sources = unit.get("sourceRefs", [])
        syllabus_summary.append(
            f"Unit {u}: {title}\n  Topics: {', '.join(topics)}\n  Source: {'; '.join(sources)}"
        )

    syllabus_text = "\n".join(syllabus_summary) if syllabus_summary else "No syllabus found."

    # Get source document text for grounding
    all_docs = workspace.get_all_bucket_texts()
    doc_text = ""
    for doc in all_docs:
        text = doc["text"]
        if len(text) > 3000:
            text = text[:3000] + "\n\n[... truncated ...]"
        doc_text += f"\n### [{doc['bucket'].upper()}] {doc['name']}\n{text}\n"

    user_prompt = (
        f"Generate 5 lessons for Week {week} of algebra instruction.\n\n"
        "CURRICULUM MAP:\n"
        f"{syllabus_text}\n\n"
        "SOURCE DOCUMENTS (teach only from these):\n"
        f"{doc_text}\n\n"
        "Produce exactly 5 lessons as a JSON object. Follow the output format exactly."
    )

    # ---- 3. Call the LLM ----
    payload = {
        "model": backend["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    url = backend["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if backend.get("api_key"):
        headers["Authorization"] = "Bearer " + backend["api_key"]

    started = time.time()

    try:
        http_req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(http_req, timeout=LLM_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        return {"ok": False, "error": f"Backend {e.code}", "detail": detail}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Cannot reach model backend: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # ---- 4. Extract and parse the response ----
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "error": "Unexpected backend response",
            "detail": str(data)[:500],
        }

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "LLM response was not valid JSON",
            "raw": content[:500],
        }

    lessons = result.get("lessons", [])
    if not lessons:
        return {
            "ok": False,
            "error": "No lessons found in LLM response",
            "raw": content[:500],
        }

    # ---- 5. Save lessons to workspace ----
    saved = []
    for lesson in lessons:
        day = lesson.get("day", len(saved) + 1)
        lesson["domain"] = "algebra"
        lesson["week"] = week
        path = workspace.store_lesson(week, day, lesson)
        saved.append({"day": day, "title": lesson.get("title", "?"), "path": str(path)})

    elapsed_ms = int((time.time() - started) * 1000)

    result = {
        "ok": True,
        "lessons": saved,
        "model": backend["model"],
        "ms": elapsed_ms,
        "week": week,
    }

    # ---- 6. Validate (optional) ----
    if validate:
        from domains.algebra import validate_lesson

        all_issues = []
        for lesson in lessons:
            issues = validate_lesson(lesson)
            if issues:
                all_issues.append(
                    {"day": lesson.get("day", "?"), "title": lesson.get("title", "?"), "issues": issues}
                )
        if all_issues:
            result["issues"] = all_issues
            # Don't fail — report issues but still save. Teacher reviews.

    return result


# ---- Standalone entry point ----


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Phren Lesson Generation Engine — generate algebra lessons from crystallized curriculum."
    )
    parser.add_argument(
        "--data-dir",
        default=".phren-data/teacher",
        help="Path to teacher workspace root (default: .phren-data/teacher)",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=1,
        help="Week number to generate (default: 1)",
    )
    parser.add_argument(
        "--prompt",
        default="gen-lessons.txt",
        help="Prompt template in prompts/ directory (default: gen-lessons.txt)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip lesson validation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt size and exit without calling LLM",
    )
    parser.add_argument(
        "--output-dir",
        help="Also write lesson JSON files to this directory",
    )
    args = parser.parse_args()

    workspace = TeacherWorkspace(args.data_dir)
    report = workspace.get_report()

    if report is None:
        print("Error: No crystallization report found.", file=sys.stderr)
        print("Run crystallize.py first.", file=sys.stderr)
        raise SystemExit(1)

    total_units = len(report.get("syllabus", []))
    total_topics = sum(len(u.get("topics", [])) for u in report.get("syllabus", []))
    print(f"Crystallization report loaded: {total_units} unit(s), {total_topics} topic(s)")
    print(f"Generating Week {args.week} lessons...")

    if args.dry_run:
        system_prompt = load_prompt(args.prompt)
        all_docs = workspace.get_all_bucket_texts()
        total_chars = sum(len(d["text"]) for d in all_docs)
        print(f"System prompt: {len(system_prompt):,} chars")
        print(f"Source material: {total_chars:,} chars across {len(all_docs)} docs")
        print("Dry run — no LLM call made.")
        return

    print(f"Calling {BACKEND['model']} @ {BACKEND['base_url']} ...")
    print("This may take 60–180 seconds for 5 lessons.\n")

    result = run_lesson_generation(
        workspace=workspace,
        week=args.week,
        prompt_name=args.prompt,
        validate=not args.no_validate,
    )

    if result["ok"]:
        print(f"✓ Generated {len(result['lessons'])} lessons in {result['ms'] / 1000:.1f}s")
        print(f"  Model: {result['model']}")
        print(f"  Week: {result['week']}")
        for l in result["lessons"]:
            print(f"    Day {l['day']}: {l['title']}")

        if result.get("issues"):
            print(f"\n⚠️  Validation found {len(result['issues'])} lesson(s) with issues:")
            for issue_group in result["issues"]:
                print(f"  Day {issue_group['day']} — {issue_group['title']}:")
                for issue in issue_group["issues"]:
                    print(f"    • {issue}")

        if args.output_dir:
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            for week_num in workspace.list_weeks():
                for day in workspace.list_days(week_num):
                    lesson = workspace.get_lesson(week_num, day)
                    if lesson:
                        out_path = out / f"week-{week_num:02d}-day-{day:02d}.json"
                        out_path.write_text(json.dumps(lesson, indent=2))
            print(f"\nExported to: {out}/")
    else:
        print(f"✗ Lesson generation failed: {result['error']}")
        if "detail" in result:
            print(f"  Detail: {result['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

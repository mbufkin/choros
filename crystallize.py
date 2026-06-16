#!/usr/bin/env python3
"""
crystallize.py — curriculum mapping engine for Phren school mode.

Reads all documents from the teacher's three buckets (curriculum, district,
teacher), calls the configured LLM with a crystallization prompt, validates the
JSON response, and saves the report.

Can be used standalone (python3 crystallize.py) or imported as a module
(from crystallize import run_crystallization).

Stdlib only. Workspace dependency, but no server dependency.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

from workspace import TeacherWorkspace

# ---- Backend configuration (same env vars as server.py) ----


def _load_dotenv(path=".env"):
    """Minimal .env loader (stdlib only)."""
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

# ---- Prompt loading ----


def load_prompt(name="crystallize.txt") -> str:
    """Load a prompt template from the prompts/ directory."""
    prompt_path = Path("prompts") / name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


# ---- Core function ----


def run_crystallization(
    workspace: TeacherWorkspace | None = None,
    backend: dict | None = None,
    prompt_name: str = "crystallize.txt",
    max_chars_per_doc: int = 8000,
) -> dict:
    """Run the crystallization engine.

    Args:
        workspace: TeacherWorkspace with buckets already populated.
                   Defaults to TeacherWorkspace().
        backend: Dict with base_url, model, api_key keys.
                 Defaults to BACKEND (from env).
        prompt_name: Prompt file in prompts/ directory.
        max_chars_per_doc: Truncate each document to this many chars.

    Returns:
        dict with keys: ok, report, model, ms, doc_count
        On failure: ok=False with error and detail keys.
    """
    if workspace is None:
        workspace = TeacherWorkspace()
    if backend is None:
        backend = BACKEND

    # ---- 1. Read all documents ----
    all_docs = workspace.get_all_bucket_texts()
    if not all_docs:
        return {
            "ok": False,
            "error": "No documents found in any bucket. Upload materials first.",
        }

    # ---- 2. Build the prompt ----
    system_prompt = load_prompt(prompt_name)

    doc_summaries = []
    for doc in all_docs:
        tag = f"[{doc['bucket'].upper()}] {doc['name']}"
        text = doc["text"]
        if len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc] + "\n\n[... truncated for length ...]"
        doc_summaries.append(f"### {tag}\n{text}")

    combined_docs = "\n\n".join(doc_summaries)

    user_prompt = (
        "Analyze the following educational documents and produce a curriculum map.\n\n"
        "DOCUMENTS:\n"
        f"{combined_docs}\n\n"
        "Generate the curriculum map JSON now. Only use information found in these documents."
    )

    # ---- 3. Call the LLM ----
    payload = {
        "model": backend["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
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
        return {
            "ok": False,
            "error": f"Backend {e.code}",
            "detail": detail,
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": f"Cannot reach model backend: {e.reason}",
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }

    # ---- 4. Extract the content ----
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "error": "Unexpected backend response",
            "detail": str(data)[:500],
        }

    # ---- 5. Parse and validate JSON ----
    try:
        report = json.loads(content)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "LLM response was not valid JSON",
            "raw": content[:500],
        }

    required = ["syllabus", "gaps", "coverage", "pacing"]
    missing = [k for k in required if k not in report]
    if missing:
        return {
            "ok": False,
            "error": f"Report missing required fields: {', '.join(missing)}",
            "report": report,
        }

    # ---- 6. Save the report ----
    workspace.set_report(report)

    elapsed_ms = int((time.time() - started) * 1000)
    return {
        "ok": True,
        "report": report,
        "model": backend["model"],
        "ms": elapsed_ms,
        "doc_count": len(all_docs),
    }


# ---- Standalone entry point ----


def main():
    """Run crystallization from the command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Phren Crystallization Engine — map curriculum from uploaded documents."
    )
    parser.add_argument(
        "--data-dir",
        default=".phren-data/teacher",
        help="Path to teacher workspace root (default: .phren-data/teacher)",
    )
    parser.add_argument(
        "--prompt",
        default="crystallize.txt",
        help="Prompt template in prompts/ directory (default: crystallize.txt)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=8000,
        help="Max chars per document in the prompt (default: 8000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt size and exit without calling LLM",
    )
    parser.add_argument(
        "--output",
        help="Also write the report JSON to this file path",
    )
    args = parser.parse_args()

    workspace = TeacherWorkspace(args.data_dir)
    all_docs = workspace.get_all_bucket_texts()

    if not all_docs:
        print("Error: No documents found in any bucket.", file=__import__("sys").stderr)
        print("Upload files via the teacher page or place them in:", file=__import__("sys").stderr)
        for bucket in TeacherWorkspace.BUCKET_NAMES:
            print(f"  {workspace.bucket_path(bucket)}/", file=__import__("sys").stderr)
        raise SystemExit(1)

    print(f"Found {len(all_docs)} document(s) across {len(set(d['bucket'] for d in all_docs))} bucket(s).")
    total_chars = sum(len(d["text"]) for d in all_docs)
    print(f"Total source characters: {total_chars:,}")

    if args.dry_run:
        system_prompt = load_prompt(args.prompt)
        print(f"System prompt: {len(system_prompt):,} chars")
        # Estimate user prompt size
        est_user = 0
        for doc in all_docs:
            est_user += min(len(doc["text"]), args.max_chars) + 100
        print(f"Estimated user prompt: ~{est_user:,} chars")
        print("Dry run — no LLM call made.")
        return

    print(f"Calling {BACKEND['model']} @ {BACKEND['base_url']} ...")
    print("This may take 30–120 seconds.\n")

    result = run_crystallization(
        workspace=workspace,
        prompt_name=args.prompt,
        max_chars_per_doc=args.max_chars,
    )

    if result["ok"]:
        report = result["report"]
        print(f"✓ Crystallization complete in {result['ms'] / 1000:.1f}s")
        print(f"  Model: {result['model']}")
        print(f"  Documents processed: {result['doc_count']}")
        print(f"  Units mapped: {len(report.get('syllabus', []))}")
        print(f"  Topics covered: {report.get('coverage', {}).get('covered', '?')}")
        print(f"  Gaps identified: {len(report.get('gaps', []))}")
        print(f"  Weeks mapped: {report.get('pacing', {}).get('mappedWeeks', '?')}")
        print(f"\nReport saved to: {workspace.report_path}")

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(report, indent=2))
            print(f"Also written to: {output_path}")
    else:
        print(f"✗ Crystallization failed: {result['error']}")
        if "detail" in result:
            print(f"  Detail: {result['detail']}")
        if "raw" in result:
            print(f"  Raw response: {result['raw'][:200]}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

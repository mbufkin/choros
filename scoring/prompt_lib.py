"""Choros Prompt Library — canonical source for all experiment prompts.

Usage:
    from choros.scoring.prompt_lib import get_prompt, get_schema, list_prompts

    # Get a locked prompt
    prompt = get_prompt("feedback-blunt-teacher", essay=text)

    # Get the JSON schema for grammar enforcement
    schema = get_schema("schema-enforced-json")

    # List all available prompts
    for p in list_prompts():
        print(f"{p['id']} v{p['version']}: {p['description']}")

Principle: No experiment uses an inline string. All prompts loaded from prompts.json.
Changing a prompt requires bumping the version field and re-baselining.
"""

import json
from pathlib import Path
from typing import Any

_PROMPTS_PATH = Path(__file__).resolve().parent / "prompts.json"
_library = None


def _load() -> dict:
    global _library
    if _library is None:
        with open(_PROMPTS_PATH) as f:
            _library = json.load(f)
    return _library


def get_prompt(prompt_id: str, **kwargs: Any) -> str:
    """Load a locked prompt by ID and fill its parameters.

    Args:
        prompt_id: e.g. 'feedback-blunt-teacher', 'scoring-direct'
        **kwargs: parameter values matching the prompt's parameters dict

    Returns:
        Filled prompt string ready for model input

    Raises:
        KeyError: if prompt_id not found
        ValueError: if required parameters are missing
    """
    lib = _load()
    if prompt_id not in lib["prompts"]:
        available = ", ".join(lib["prompts"].keys())
        raise KeyError(f"Unknown prompt '{prompt_id}'. Available: {available}")

    prompt = lib["prompts"][prompt_id]
    template = prompt.get("template")

    if template is None:
        raise ValueError(f"Prompt '{prompt_id}' has no template (it may be a schema-only entry)")

    # Apply defaults for missing kwargs
    params = prompt.get("parameters", {})
    defaults = prompt.get("defaults", {})
    for key, val in defaults.items():
        if key not in kwargs:
            kwargs[key] = val

    # Check required params
    missing = [p for p in params if p not in kwargs]
    if missing:
        raise ValueError(
            f"Missing required parameters for '{prompt_id}' v{prompt['version']}: {missing}\n"
            f"Parameters: {list(params.keys())}"
        )

    return template.format(**kwargs)


def get_schema(schema_id: str) -> dict | None:
    """Get a JSON schema definition (for llama.cpp grammar enforcement).

    Args:
        schema_id: e.g. 'schema-enforced-json'

    Returns:
        JSON schema dict, or None if no schema defined for this ID
    """
    lib = _load()
    entry = lib["prompts"].get(schema_id, {})
    return entry.get("json_schema")


def get_prompt_meta(prompt_id: str) -> dict:
    """Get metadata for a prompt (version, description, source, parameters)."""
    lib = _load()
    if prompt_id not in lib["prompts"]:
        raise KeyError(f"Unknown prompt '{prompt_id}'")
    return lib["prompts"][prompt_id]


def get_criteria(prompt_id: str) -> list[dict] | None:
    """Get criteria list for a prompt (if it has one)."""
    meta = get_prompt_meta(prompt_id)
    return meta.get("criteria")


def list_prompts() -> list[dict]:
    """Return all available prompts with id, version, description."""
    lib = _load()
    return [
        {
            "id": pid,
            "version": p.get("version", "?"),
            "description": p.get("description", ""),
            "source": p.get("source", ""),
            "has_template": "template" in p,
            "has_schema": "json_schema" in p,
            "parameters": list(p.get("parameters", {}).keys()),
        }
        for pid, p in lib["prompts"].items()
    ]


# Convenience: the uniform debate rubric as a reusable module-level constant
# (loaded from rubric-uniform-holistic)
def get_rubric() -> str:
    """Return the standard uniform debate scoring rubric (2-12 scale)."""
    return get_prompt("rubric-uniform-holistic")

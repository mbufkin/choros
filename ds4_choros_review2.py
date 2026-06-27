#!/usr/bin/env python3
"""Continue reviewing remaining choros files against DS4."""
import json, os, time, subprocess

DS4_URL = "http://100.85.15.59:8082/v1/completions"
CHOROS = "/home/mbufkin/choros"
OUT = "/tmp/ds4_choros_review"

CONTEXT = """
CRITICAL CONTEXT (read these constraints before making suggestions):
- Zero build step. Classic <script> tags. No npm, no bundler, no ES modules, no framework.
- Python stdlib only — zero pip packages on the server.
- The model cannot generate outside the uploaded source documents.
- Filesystem as database — JSON files, no SQL.
- Teacher batch jobs (crystallization, lesson generation) are async.
- Deterministic scoring is separate from LLM feedback.
- Dark theme UI — see DESIGN.md for color tokens.
- Target hardware: Lenovo DGX Spark (GB10, unified 128GB memory, aarch64).
- Current model: DeepSeek V4 Flash at IQ2XXS via DS4 server (the model you are).
""".strip()

TASK = """
Review this file thoroughly. Identify:
1. BUGS — logic errors, edge cases, security issues
2. ROBUSTNESS — missing error handling, silent failures, resource leaks
3. ARCHITECTURE — poor separation of concerns, tight coupling
4. PERFORMANCE — unnecessary work, blocking operations
5. CLARITY — confusing names, missing comments
6. CONSTRAINT VIOLATIONS — anything breaking zero-dep / stdlib-only rules

Be specific. Reference exact line numbers. Rate each finding HIGH/MEDIUM/LOW.
Do NOT praise. Find problems.
""".strip()

# Remaining files
FILES = [
    ("domains/algebra.py", "Algebra domain helpers"),
    ("teacher.html", "Teacher dashboard HTML"),
    ("student.html", "Student page HTML"),
    ("PRODUCT.md", "What Choros is building — goals and non-goals"),
    ("DESIGN.md", "UI design tokens and interaction model"),
    ("AGENTS.md", "Agent operating manual"),
    ("DECISIONS.md", "Architecture decisions log"),
    ("MODELS.md", "Model tier strategy"),
    ("BASELINE.md", "Data source baseline"),
]

def review_file(filename, description):
    full_path = os.path.join(CHOROS, filename)
    if not os.path.exists(full_path):
        return f"[SKIP] {filename:30s} — not found"
    
    with open(full_path) as f:
        content = f.read()
    
    if len(content) > 6000:
        content = content[:6000] + f"\n\n[... truncated from {len(content)} chars]"
    
    prompt = f"""You are a senior software engineer reviewing the Choros project.

FILE: {filename}
DESCRIPTION: {description}

```
{content}
```

{CONTEXT}

{TASK}

Output format:
## File: {filename}
### [SEVERITY] Issue title — line N
Description of the issue.
"""
    
    payload = json.dumps({"prompt": prompt, "max_tokens": 1024, "temperature": 0.3})
    
    t0 = time.time()
    try:
        curl_args = [
            "curl", "-s", "--max-time", "120",
            "-X", "POST", DS4_URL,
            "-H", "Content-Type: application/json",
            "-d", payload,
        ]
        resp = subprocess.run(curl_args, capture_output=True, text=True, timeout=130)
        elapsed = time.time() - t0
        if resp.returncode != 0:
            return f"[FAIL] {filename:30s} — curl exited {resp.returncode}"
        data = json.loads(resp.stdout)
        text = data.get("choices", [{}])[0].get("text", "")
        
        out_path = os.path.join(OUT, filename.replace("/", "_") + ".review.md")
        with open(out_path, "w") as f:
            f.write(f"# Review: {filename}\n*{description}*\n*Response time: {elapsed:.0f}s, {len(text)} chars*\n\n{text}")
        
        return f"[OK]   {filename:30s} {elapsed:3.0f}s  {len(text):4d} chars"
    except Exception as e:
        return f"[FAIL] {filename:30s} — {e}"

print(f"Remaining {len(FILES)} files...\n")
for name, desc in FILES:
    result = review_file(name, desc)
    print(f"  {result}")
    time.sleep(2)

print(f"\nDone. Total reviews: {len(os.listdir(OUT))}")

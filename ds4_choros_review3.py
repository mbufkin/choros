#!/usr/bin/env python3
"""Last 3 remaining doc files."""
import json, os, time, subprocess

DS4_URL = "http://100.85.15.59:8082/v1/completions"
CHOROS = "/home/mbufkin/choros"
OUT = "/tmp/ds4_choros_review"

CONTEXT = """
CRITICAL CONTEXT: Zero build step, Python stdlib only, filesystem as DB, async batch jobs, deterministic scoring separate from LLM, dark theme. Target: DGX Spark (aarch64, 128GB unified), current model is DeepSeek V4 Flash at IQ2XXS.
""".strip()

TASK = "Review this document thoroughly. Identify issues: gaps, contradictions, missing details, scope creep risks, unrealistic assumptions. Be critical. Reference sections. Rate findings HIGH/MEDIUM/LOW."

FILES = [
    ("DECISIONS.md", "Architecture decisions log"),
    ("MODELS.md", "Model tier strategy"),
    ("BASELINE.md", "Data source baseline"),
]

for name, desc in FILES:
    content = open(os.path.join(CHOROS, name)).read()
    if len(content) > 6000:
        content = content[:6000] + f"\n[... truncated]"
    
    prompt = f"Review this Choros project doc.\n\nFILE: {name}\n\n```\n{content}\n```\n\n{CONTEXT}\n\n{TASK}"
    payload = json.dumps({"prompt": prompt, "max_tokens": 1024, "temperature": 0.3})
    
    t0 = time.time()
    try:
        resp = subprocess.run(["curl", "-s", "--max-time", "120", "-X", "POST", DS4_URL,
            "-H", "Content-Type: application/json", "-d", payload],
            capture_output=True, text=True, timeout=130)
        el = time.time() - t0
        data = json.loads(resp.stdout)
        text = data.get("choices", [{}])[0].get("text", "")
        out_path = os.path.join(OUT, name.replace("/", "_") + ".review.md")
        with open(out_path, "w") as f:
            f.write(f"# Review: {name}\n*{desc}*\n*Response: {el:.0f}s, {len(text)} chars*\n\n{text}")
        print(f"[OK]   {name:25s} {el:3.0f}s  {len(text):4d} chars")
    except Exception as e:
        print(f"[FAIL] {name:25s} — {e}")
    time.sleep(2)

print(f"\nDone. Total reviews: {len(os.listdir(OUT))}")

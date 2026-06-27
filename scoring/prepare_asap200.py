#!/usr/bin/env python3
"""Convert real ASAP-AES training set into pipeline-compatible format.

Picks 200 essays from essay_set=1 (persuasive writing, score range 2-12),
normalizes scores to 1-6, and outputs in the format expected by run_baseline.py.

Output: /tmp/asap200.json
"""
import csv, json, random, sys, re, os

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/training_set_rel3.tsv"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/asap200.json"
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 42
N_ESSAYS = 200

# ASAP set 1: persuasive writing prompt
# The original prompt asked students to explain whether they support
# mandatory school uniforms, supporting with reasons/examples.
ESSAY_SET = 1
ORIG_MIN, ORIG_MAX = 2, 12  # domain1_score range for set 1
TARGET_MIN, TARGET_MAX = 1, 6

def normalize_score(orig_score: int) -> int:
    """Normalize 2-12 to 1-6 scale."""
    if orig_score < ORIG_MIN:
        return TARGET_MIN
    if orig_score > ORIG_MAX:
        return TARGET_MAX
    # Linear mapping
    ratio = (orig_score - ORIG_MIN) / (ORIG_MAX - ORIG_MIN)
    normalized = round(TARGET_MIN + ratio * (TARGET_MAX - TARGET_MIN))
    return max(TARGET_MIN, min(TARGET_MAX, normalized))

# Quick topic keywords for set 1 (school uniforms / dress code)
TOPIC_KEYWORDS = [
    "uniform", "dress code", "clothing", "wear", "school",
]

def detect_topic(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in TOPIC_KEYWORDS):
        return "school_uniforms"
    return "unknown"

def main():
    random.seed(SEED)

    # Read ASAP TSV
    essays = []
    with open(INPUT, newline='', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if int(row['essay_set']) != ESSAY_SET:
                continue
            essays.append(row)

    print(f"Total essay_set={ESSAY_SET} essays available: {len(essays)}")

    # Sample 200 with seed
    sampled = random.sample(essays, min(N_ESSAYS, len(essays)))

    # Convert
    result_essays = []
    for s in sampled:
        eid = f"asap-{s['essay_id']}"
        orig_score = int(s['domain1_score'])
        norm_score = normalize_score(orig_score)
        text = s['essay']
        wc = len(text.split())

        result_essays.append({
            "id": eid,
            "score": norm_score,
            "orig_score": orig_score,
            "topic": detect_topic(text),
            "text": text,
        })

    # Score distribution
    from collections import Counter
    dist = Counter(e["score"] for e in result_essays)

    output = {
        "source": f"ASAP-AES (Hewlett Foundation) — essay_set={ESSAY_SET} (persuasive writing)",
        "score_range": f"{ORIG_MIN}-{ORIG_MAX} (original), {TARGET_MIN}-{TARGET_MAX} (normalized)",
        "n_essays": len(result_essays),
        "seed": SEED,
        "score_distribution": {str(k): v for k, v in sorted(dist.items())},
        "prompt": "Write an essay explaining whether students should be required to wear school uniforms. Support your position with reasons and examples.",
        "essays": result_essays,
    }

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(result_essays)} essays → {OUTPUT}")
    print(f"Score distribution (normalized): {dict(sorted(dist.items()))}")
    print(f"Human scores range: {min(s['orig_score'] for s in result_essays)}-{max(s['orig_score'] for s in result_essays)}")

if __name__ == "__main__":
    main()

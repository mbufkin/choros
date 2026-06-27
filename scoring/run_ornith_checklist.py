#!/usr/bin/env python3
"""Run Evidence-Grounded Checklist (Strategy D) on ASAP vs Ornith 35B.

Uses calibrate.py's score_evidence_checklist function against our
200 ASAP essay set. Only runs Strategy D — skips A/B/C.

Usage:
  CHOROS_BACKEND=llamacpp python3 run_ornith_checklist.py [start_idx] [count]
"""
import json, sys, os, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibrate import score_evidence_checklist, cohens_kappa, calibrate_ridge

LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")
ESSAYS_PATH = "/tmp/asap200.json"
START_IDX = int(sys.argv[1]) if len(sys.argv) > 1 else 0
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 200
OUTPUT = sys.argv[3] if len(sys.argv) > 3 else "/home/mbufkin/choros/scoring/guardrails/ornith_checklist_results.json"

print(f"Evidence-Grounded Checklist — Ornith 35B MoE on G10")
print(f"Essays: {ESSAYS_PATH} [{START_IDX}:{START_IDX+COUNT}]")
print(f"Backend: {LLAMACPP_URL}\n")

with open(ESSAYS_PATH) as f:
    data = json.load(f)

all_essays = data["essays"]
essays = all_essays[START_IDX:START_IDX+COUNT]
human_scores = [e["score"] for e in essays]

results = []
raw_scores = []

for i, essay in enumerate(essays):
    eid = essay["id"]
    human = essay["score"]
    text = essay["text"]
    wc = len(text.split())

    print(f"[{START_IDX+i+1}/{len(all_essays)}] {eid} (human={human}, {wc}w)...", end=" ", flush=True)
    t0 = time.time()

    result = score_evidence_checklist(text)
    elapsed = time.time() - t0

    if result is not None:
        raw = result["raw_score"]
        mapped = result["mapped_score"]
        valid = result["valid_count"]
        total = result["total_count"]
        delta = mapped - human
        sign = "+" if delta > 0 else ""
        print(f"raw={raw} mapped={mapped} ({sign}{delta}) evidence={valid}/{total} [{elapsed:.0f}s]")

        results.append({
            "id": eid, "human": human, "model": mapped,
            "raw_score": raw, "delta": delta,
            "evidence_valid": valid, "evidence_total": total,
            "decisions": result["decisions"],
            "elapsed_s": round(elapsed, 1),
        })
        raw_scores.append(raw)
    else:
        print(f"PARSE FAILED [{elapsed:.0f}s]")
        results.append({"id": eid, "human": human, "model": None, "error": True})
        raw_scores.append(0)

# Compute kappa
model_scores = [r["model"] if r.get("model") else human_scores[i] for i, r in enumerate(results)]
kappa = cohens_kappa(human_scores, model_scores)

# Calibration
calibration = calibrate_ridge(raw_scores, human_scores) if len(raw_scores) >= 2 else None
calibrated_kappa = None
if calibration:
    calibrated_scores = [round(max(2, min(12, s))) for s in calibration["fitted_scores_raw"]]
    calibrated_kappa = cohens_kappa(human_scores, calibrated_scores)

# Summary
from collections import Counter
human_dist = Counter(human_scores)
model_dist = Counter(model_scores)
human_range = max(human_scores) - min(human_scores)
model_range_num = max(model_scores) - min(model_scores)

print(f"\n{'='*60}")
print(f"RESULTS — Ornith 35B Evidence-Grounded Checklist")
print(f"{'='*60}")
print(f"N: {len(results)}")
print(f"Kappa: {kappa:.3f}")
print(f"Agreement: {sum(1 for h,m in zip(human_scores,model_scores) if h==m)/len(human_scores):.1%}")
print(f"Human range: {min(human_scores)}-{max(human_scores)} (span {human_range})")
print(f"Model range: {min(model_scores)}-{max(model_scores)} (span {model_range_num})")
print(f"Compression: {model_range_num/human_range:.2f}" if human_range > 0 else "N/A")
print(f"\nHuman dist: {dict(sorted(human_dist.items()))}")
print(f"Model dist: {dict(sorted(model_dist.items()))}")
if calibrated_kappa:
    print(f"\nCalibrated Kappa: {calibrated_kappa:.3f}")
    print(f"Calibration formula: {calibration['formula']}")

# Save
output = {
    "model": "Ornith-1.0-35B-MoE (Q4_K_M)",
    "backend": "llamacpp-cuda",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "n_essays": len(results),
    "kappa": round(kappa, 3),
    "calibrated_kappa": round(calibrated_kappa, 3) if calibrated_kappa else None,
    "human_distribution": {str(k): v for k, v in sorted(human_dist.items())},
    "model_distribution": {str(k): v for k, v in sorted(model_dist.items())},
    "results": results,
}
if calibration:
    output["calibration"] = calibration

with open(OUTPUT, 'w') as f:
    json.dump(output, f, indent=2)
print(f"\nSaved: {OUTPUT}")

"""Compare completed 1600-setup original and accelerated Figure 2 runs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/"results/figure2_full"
OPT = ROOT/"results/figure2_full_optimized"
for folder in (BASE, OPT):
    metadata = json.loads((folder/"metadata_final.json").read_text())
    if metadata["status"] != "completed" or metadata["setups"] != 1600:
        raise RuntimeError(f"Incomplete Figure 2 run: {folder}")


def read(folder):
    rows = []
    for name in ("attempts.jsonl", "parallel_attempts.jsonl"):
        rows += [json.loads(line) for line in (folder/name).read_text().splitlines() if line]
    by_attempt = {(x["setup_id"], x["attempt"]): x for x in rows}
    latest = {x["setup_id"]: x for x in rows}
    return rows, by_attempt, latest


br, ba, bl = read(BASE)
orows, oa, ol = read(OPT)
if len(bl) != 1600 or len(ol) != 1600:
    raise RuntimeError("Missing setup records")
mismatches = []
for setup_id in range(1, 1601):
    a, b = bl[setup_id], ol[setup_id]
    for key in ("rate","csi","attempt","solved","feasible_per_ap",
                "feasible_sum","outer_iterations"):
        if a[key] != b[key]:
            mismatches.append({"setup_id":setup_id,"field":key,
                               "baseline":a[key],"optimized":b[key]})
max_dual_diff = 0.0
max_power_gap_diff = 0.0
for key in ba.keys() & oa.keys():
    a, b = ba[key], oa[key]
    if a["final_dual_mw"] is not None and b["final_dual_mw"] is not None:
        max_dual_diff = max(max_dual_diff,
                            abs(a["final_dual_mw"]-b["final_dual_mw"]))
    if a["final_max_ap_violation_mw"] is not None and b["final_max_ap_violation_mw"] is not None:
        max_power_gap_diff = max(
            max_power_gap_diff,
            abs(a["final_max_ap_violation_mw"]-b["final_max_ap_violation_mw"]))
result = {
    "baseline_attempts":len(br),"optimized_attempts":len(orows),
    "shared_attempts":len(ba.keys()&oa.keys()),
    "setup_mismatches":mismatches,
    "max_abs_final_dual_difference_mw":max_dual_diff,
    "max_abs_final_power_violation_difference_mw":max_power_gap_diff,
    "baseline_solved":sum(x["solved"] for x in bl.values()),
    "optimized_solved":sum(x["solved"] for x in ol.values()),
}
(ROOT/"results/figure2_full/comparison.json").write_text(
    json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!="setup_mismatches"},indent=2))
print("setup mismatches:",len(mismatches))

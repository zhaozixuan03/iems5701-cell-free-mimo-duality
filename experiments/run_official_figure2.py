"""Execute the unmodified author Figure 2 script with lossless run logging.

The wrappers only observe Problem methods and save the Matplotlib plot.
Without --optimized they do not change the random stream, solver parameters,
or decisions. --optimized substitutes the algebraically equivalent solver.
"""
import csv
import json
import os
import platform
import runpy
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream"
USE_OPTIMIZED = "--optimized" in sys.argv
OUT = ROOT / "results" / (
    "figure2_full_optimized" if USE_OPTIMIZED else "figure2_full")
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(UPSTREAM))
import main_problem
if USE_OPTIMIZED:
    sys.path.insert(0, str(ROOT))
    from optimized_problem import OptimizedProblem
    main_problem.Problem = OptimizedProblem

counter = 0
records = []
original_init = main_problem.Problem.__init__
original_constraints = main_problem.Problem.set_constraints
original_solve = main_problem.Problem.solve
original_show = plt.show
started = time.time()


def tracked_init(self, *args, **kwargs):
    global counter
    counter += 1
    self.record_id = counter
    original_init(self, *args, **kwargs)


def tracked_constraints(self, sinr_target, p_max, q, csi):
    self.record_rate = float(np.log2(sinr_target[0] + 1))
    self.record_csi = csi
    self.record_attempt = 0
    original_constraints(self, sinr_target, p_max, q, csi)


def tracked_solve(self, *args, **kwargs):
    self.record_attempt += 1
    t0 = time.perf_counter()
    error = None
    try:
        return original_solve(self, *args, **kwargs)
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        record = {
            "setup_id": self.record_id,
            "rate": self.record_rate,
            "csi": self.record_csi,
            "attempt": self.record_attempt,
            "kappa": kwargs.get("kappa"),
            "seconds": time.perf_counter() - t0,
            "outer_iterations": len(self.dual_obj),
            "solved": bool(self.solved),
            "feasible_per_ap": bool(self.feasible),
            "feasible_sum": bool(self.feasible_sum),
            "final_dual_mw": float(self.dual_obj[-1]) if self.dual_obj else None,
            "final_max_ap_violation_mw": (
                float(np.max(self.powers[-1] - self.P_max)) if self.powers else None
            ),
            "error": error,
        }
        records.append(record)
        with (OUT / "attempts.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")


def saved_show(*args, **kwargs):
    plt.gcf().savefig(OUT / "figure2_official.png", dpi=180, bbox_inches="tight")
    return None


main_problem.Problem.__init__ = tracked_init
main_problem.Problem.set_constraints = tracked_constraints
main_problem.Problem.solve = tracked_solve
plt.show = saved_show
(OUT / "attempts.jsonl").write_text("")
status = "completed"
error = None
try:
    runpy.run_path(str(UPSTREAM / "local_vs_centralized_rate.py"), run_name="__main__")
except BaseException as exc:
    status = "failed"
    error = repr(exc)
    raise
finally:
    latest = {r["setup_id"]: r for r in records}
    grouped = defaultdict(list)
    for r in latest.values():
        grouped[(r["rate"], r["csi"])].append(r)
    fields = ["rate", "csi", "setups", "solved", "per_ap_feasible",
              "sum_feasible", "per_ap_probability_among_solved",
              "sum_probability_among_solved"]
    with (OUT / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for (rate, csi), group in sorted(grouped.items()):
            solved = sum(r["solved"] for r in group)
            per_ap = sum(r["feasible_per_ap"] for r in group if r["solved"])
            sum_feas = sum(r["feasible_sum"] for r in group if r["solved"])
            writer.writerow({
                "rate": rate, "csi": csi, "setups": len(group),
                "solved": solved, "per_ap_feasible": per_ap,
                "sum_feasible": sum_feas,
                "per_ap_probability_among_solved": per_ap / solved if solved else "",
                "sum_probability_among_solved": sum_feas / solved if solved else "",
            })
    (OUT / "metadata.json").write_text(json.dumps({
        "status": status, "error": error, "started_unix": started,
        "finished_unix": time.time(), "setups_started": counter,
        "attempts": len(records), "official_script": "upstream/local_vs_centralized_rate.py",
        "solver": "OptimizedProblem" if USE_OPTIMIZED else "Problem",
        "official_git_commit": "5a968b40fa43e7d18b62641bb46073f57442f227",
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    }, indent=2))

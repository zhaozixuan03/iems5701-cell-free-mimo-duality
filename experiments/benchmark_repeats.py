"""Repeated paired timing of the author's Figure 3 dimensions.

Alternates method order across repeats. Each method sees the same seeded
setup. Repeats estimate machine timing noise; seeds sample different setups.
"""
import argparse
import csv
import json
import os
import platform
import statistics
import sys
from pathlib import Path

import matplotlib
import numpy as np
import scipy
from run_figure3 import Problem, OptimizedProblem, execute

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, nargs="+", default=[4, 5, 6, 7, 8])
    p.add_argument("--repeats", type=int, default=5)
    p.add_argument("--output", type=Path, default=ROOT/"results/figure3_repeats")
    cfg = p.parse_args()
    cfg.L, cfg.K, cfg.N, cfg.Q = 16, 16, 4, 4
    cfg.n_sim, cfg.size, cfg.p_max = 100, 1000, 1000
    cfg.rate, cfg.kappa = 3.5, 10
    cfg.tol_fp, cfg.tol_psg, cfg.max_outer = 1e-5, 0.1, 20
    cfg.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in cfg.seeds:
        for repeat in range(cfg.repeats):
            order = (Problem, OptimizedProblem) if repeat % 2 == 0 else (
                OptimizedProblem, Problem)
            pair = {}
            for cls in order:
                run = execute(cls, seed, cfg)
                if run["error"]:
                    raise RuntimeError((seed, repeat, run["error"]))
                pair[cls.__name__] = run
                print(seed, repeat, cls.__name__, run["solve_s"], flush=True)
            a, b = pair["Problem"], pair["OptimizedProblem"]
            assert a["outer_iterations"] == b["outer_iterations"]
            assert a["inner_iterations"] == b["inner_iterations"]
            objective_diff = max(abs(x-y) for x, y in zip(
                a["dual_objective"], b["dual_objective"]))
            power_diff = max(abs(x-y) for x, y in zip(
                a["per_ap_power_mw"], b["per_ap_power_mw"]))
            assert objective_diff < 1e-7
            assert power_diff < 1e-7
            rows.append({
                "seed": seed, "repeat": repeat,
                "first_method": order[0].__name__,
                "baseline_s": a["solve_s"], "optimized_s": b["solve_s"],
                "speed_ratio": a["solve_s"] / b["solve_s"],
                "outer_iterations": a["outer_iterations"],
                "inner_iterations": a["inner_iterations"],
                "max_abs_objective_difference_mw": objective_diff,
                "max_abs_final_ap_power_difference_mw": power_diff,
                "baseline_final_power_violation_mw": a["final_power_violation_mw"],
                "baseline_final_sinr_gap_reported": a["final_sinr_gap_reported"],
            })
            (cfg.output/"timings.json").write_text(json.dumps(rows, indent=2))
    with (cfg.output/"timings.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    seed_medians = {
        str(seed): statistics.median(
            r["speed_ratio"] for r in rows if r["seed"] == seed)
        for seed in cfg.seeds
    }
    (cfg.output/"summary.json").write_text(json.dumps({
        "seeds": cfg.seeds, "repeats": cfg.repeats,
        "per_seed_median_speed_ratio": seed_medians,
        "median_of_seed_medians": statistics.median(seed_medians.values()),
        "min_pair_ratio": min(r["speed_ratio"] for r in rows),
        "max_pair_ratio": max(r["speed_ratio"] for r in rows),
    }, indent=2))
    (cfg.output/"metadata.json").write_text(json.dumps({
        "seeds": cfg.seeds, "repeats": cfg.repeats,
        "L": cfg.L, "K": cfg.K, "N": cfg.N, "Q": cfg.Q,
        "n_sim": cfg.n_sim, "size": cfg.size, "p_max": cfg.p_max,
        "rate": cfg.rate, "kappa": cfg.kappa,
        "tol_fp": cfg.tol_fp, "tol_psg": cfg.tol_psg,
        "max_outer": cfg.max_outer,
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    }, indent=2))


if __name__ == "__main__":
    main()

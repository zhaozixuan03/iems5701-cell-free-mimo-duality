"""Paired ablation of reusing local-CSI responses within one iteration.

Both variants use the same vectorized solver. The control clears only the
cross-step response cache, reproducing the immediately previous implementation.
"""
import argparse
import csv
import json
import os
import platform
import statistics
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from optimized_problem import OptimizedProblem
from run_figure3 import execute


class UncachedOptimizedProblem(OptimizedProblem):
    def compute_channel_coefficients(self, p, sig, parameters):
        self._response_cache = None
        return super().compute_channel_coefficients(p, sig, parameters)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[4, 5, 6, 7, 8])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/figure3_response_reuse")
    cfg = parser.parse_args()
    cfg.L, cfg.K, cfg.N, cfg.Q = 16, 16, 4, 4
    cfg.n_sim, cfg.size, cfg.p_max = 100, 1000, 1000
    cfg.rate, cfg.kappa = 3.5, 10
    cfg.tol_fp, cfg.tol_psg, cfg.max_outer = 1e-5, 0.1, 20
    cfg.output.mkdir(parents=True, exist_ok=True)
    rows = []
    raw = cfg.output / "runs.jsonl"
    raw.write_text("")
    for seed in cfg.seeds:
        for repeat in range(cfg.repeats):
            order = ((UncachedOptimizedProblem, OptimizedProblem)
                     if repeat % 2 == 0 else
                     (OptimizedProblem, UncachedOptimizedProblem))
            pair = {}
            for cls in order:
                run = execute(cls, seed, cfg)
                if run["error"]:
                    raise RuntimeError((seed, repeat, run["error"]))
                pair[cls.__name__] = run
                with raw.open("a") as stream:
                    stream.write(json.dumps({"repeat": repeat, **run}) + "\n")
                print(seed, repeat, cls.__name__, run["solve_s"], flush=True)
            before = pair["UncachedOptimizedProblem"]
            after = pair["OptimizedProblem"]
            objective_diff = max(abs(a-b) for a,b in zip(
                before["dual_objective"], after["dual_objective"]))
            power_diff = max(abs(a-b) for a,b in zip(
                before["per_ap_power_mw"], after["per_ap_power_mw"]))
            assert before["outer_iterations"] == after["outer_iterations"]
            assert before["inner_iterations"] == after["inner_iterations"]
            assert before["solved"] == after["solved"]
            assert before["feasible_flag"] == after["feasible_flag"]
            assert objective_diff < 1e-7
            assert power_diff < 1e-7
            rows.append({
                "seed": seed, "repeat": repeat,
                "first_method": order[0].__name__,
                "uncached_s": before["solve_s"],
                "reused_s": after["solve_s"],
                "speed_ratio": before["solve_s"] / after["solve_s"],
                "outer_iterations": before["outer_iterations"],
                "inner_iterations": before["inner_iterations"],
                "solved": before["solved"],
                "feasible": before["feasible_flag"],
                "max_abs_objective_difference_mw": objective_diff,
                "max_abs_final_ap_power_difference_mw": power_diff,
                "uncached_final_power_violation_mw": before["final_power_violation_mw"],
                "reused_final_power_violation_mw": after["final_power_violation_mw"],
                "uncached_final_sinr_gap_reported": before["final_sinr_gap_reported"],
                "reused_final_sinr_gap_reported": after["final_sinr_gap_reported"],
            })
            (cfg.output / "timings.json").write_text(json.dumps(rows, indent=2))
    with (cfg.output / "timings.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    seed_medians = {
        str(seed): statistics.median(r["speed_ratio"] for r in rows
                                     if r["seed"] == seed)
        for seed in cfg.seeds
    }
    (cfg.output / "summary.json").write_text(json.dumps({
        "seeds": cfg.seeds, "repeats": cfg.repeats,
        "per_seed_median_speed_ratio": seed_medians,
        "median_of_seed_medians": statistics.median(seed_medians.values()),
        "min_pair_ratio": min(r["speed_ratio"] for r in rows),
        "max_pair_ratio": max(r["speed_ratio"] for r in rows),
        "uncached_total_s": sum(r["uncached_s"] for r in rows),
        "reused_total_s": sum(r["reused_s"] for r in rows),
        "max_objective_diff_mw": max(r["max_abs_objective_difference_mw"] for r in rows),
        "max_power_diff_mw": max(r["max_abs_final_ap_power_difference_mw"] for r in rows),
    }, indent=2))
    (cfg.output / "metadata.json").write_text(json.dumps({
        "design": "paired same-seed ablation, alternating method order",
        "control": "same vectorized solver with response cache cleared before coefficient computation",
        "seeds": cfg.seeds, "repeats": cfg.repeats,
        "L": cfg.L, "K": cfg.K, "N": cfg.N, "Q": cfg.Q,
        "n_sim": cfg.n_sim, "size": cfg.size, "p_max": cfg.p_max,
        "rate": cfg.rate, "kappa": cfg.kappa,
        "tol_fp": cfg.tol_fp, "tol_psg": cfg.tol_psg,
        "max_outer": cfg.max_outer,
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    }, indent=2))


if __name__ == "__main__":
    main()

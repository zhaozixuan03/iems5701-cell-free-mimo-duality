"""Paired, reduced-scale Figure 3 convergence and runtime experiment."""
import argparse
import contextlib
import csv
import io
import json
import os
import platform
import re
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from upstream.main_problem import Problem
from optimized_problem import OptimizedProblem


def execute(cls, seed, cfg):
    np.random.seed(seed)
    t0 = time.perf_counter()
    problem = cls(cfg.L, cfg.K, cfg.N, cfg.size, N_sim=cfg.n_sim)
    problem.set_constraints((2**cfg.rate-1)*np.ones(cfg.K),
                            cfg.p_max*np.ones(cfg.L), cfg.Q, "local")
    setup_s = time.perf_counter() - t0
    calls = 0
    original = problem.optimize_beamforming_parameters
    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)
    problem.optimize_beamforming_parameters = counted
    captured = io.StringIO()
    t0 = time.perf_counter()
    error = None
    try:
        with contextlib.redirect_stdout(captured):
            problem.solve(toll_fp=cfg.tol_fp, toll_psg=cfg.tol_psg,
                          iter_max_psg=cfg.max_outer, kappa=cfg.kappa,
                          feas_only=False)
    except Exception as exc:
        error = repr(exc)
    solve_s = time.perf_counter() - t0
    log = captured.getvalue()
    traces = []
    for line in log.splitlines():
        match = re.search(r"Dual: ([^ ]+) \| surrogate dual gap: ([^ ]+) \| max power gap: ([^ ]+) \| max SINR gap: ([^ ]+)", line)
        if match:
            traces.append(dict(zip(("dual", "surrogate_gap", "power_gap", "sinr_gap"),
                                   map(float, match.groups()))))
    final_powers = np.asarray(problem.powers[-1]).tolist() if problem.powers else None
    result = {
        "seed": seed, "method": cls.__name__, "setup_s": setup_s,
        "solve_s": solve_s, "outer_iterations": len(problem.dual_obj),
        "inner_iterations": calls, "solved": bool(problem.solved),
        "feasible_flag": bool(problem.feasible), "error": error,
        "dual_objective": list(map(float, problem.dual_obj)),
        "per_ap_power_mw": final_powers,
        "final_power_violation_mw": (max(final_powers)-cfg.p_max if final_powers else None),
        "final_surrogate_gap_mw": (sum(final_powers)-problem.dual_obj[-1] if final_powers else None),
        "final_sinr_gap_reported": (traces[-1]["sinr_gap"] if traces else None),
        "trace": traces, "stdout": log,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[4, 5, 6, 7, 8])
    parser.add_argument("--L", type=int, default=4)
    parser.add_argument("--K", type=int, default=6)
    parser.add_argument("--N", type=int, default=2)
    parser.add_argument("--Q", type=int, default=2)
    parser.add_argument("--n-sim", type=int, default=10)
    parser.add_argument("--size", type=float, default=300)
    parser.add_argument("--p-max", type=float, default=1000)
    parser.add_argument("--rate", type=float, default=3.5)
    parser.add_argument("--kappa", type=float, default=10)
    parser.add_argument("--tol-fp", type=float, default=1e-5)
    parser.add_argument("--tol-psg", type=float, default=100)
    parser.add_argument("--max-outer", type=int, default=20)
    parser.add_argument("--output", type=Path, default=ROOT/"results"/"figure3_scaled")
    cfg = parser.parse_args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    records = []
    for seed in cfg.seeds:
        for cls in (Problem, OptimizedProblem):
            record = execute(cls, seed, cfg)
            records.append(record)
            print(seed, cls.__name__, record["solve_s"],
                  record["outer_iterations"], record["inner_iterations"],
                  record["error"], flush=True)
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(cfg).items()}
    metadata = {"config": config, "python": sys.version, "platform": platform.platform(),
                "numpy": np.__version__, "scipy": scipy.__version__,
                "matplotlib": matplotlib.__version__,
                "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS")}
    (cfg.output/"metadata.json").write_text(json.dumps(metadata, indent=2))
    (cfg.output/"runs.json").write_text(json.dumps(records, indent=2, allow_nan=False))
    fields = ["seed","method","setup_s","solve_s","outer_iterations","inner_iterations",
              "solved","feasible_flag","error","final_power_violation_mw",
              "final_surrogate_gap_mw","final_sinr_gap_reported"]
    with (cfg.output/"summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows({k: x[k] for k in fields} for x in records)
    fig, ax = plt.subplots(figsize=(7, 4))
    for record in records:
        y = record["dual_objective"]
        if y and all(v > 0 for v in y):
            ax.plot(range(1,len(y)+1), 10*np.log10(y),
                    label=f'{record["method"]} seed {record["seed"]}')
    ax.set(xlabel="Outer iteration", ylabel="Dual objective (dBm)",
           title="Scaled Figure 3 experiment")
    ax.grid(True)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(cfg.output/"dual_objective.png", dpi=160)
    print("Saved",cfg.output)


if __name__ == "__main__":
    main()

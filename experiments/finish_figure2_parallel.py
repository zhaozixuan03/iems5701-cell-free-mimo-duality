"""Finish exact author Figure 2 setups in parallel after a partial serial run.

Each setup receives the NumPy RNG state that the author's sequential script
would have immediately before constructing that Problem. The official
Problem/solve methods, tolerances, retry schedule and classification rule are
used. This changes scheduling only, not the simulated setups or solver.
"""
import argparse
import contextlib
import csv
import io
import json
import multiprocessing
import os
import platform
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
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

RATES = np.linspace(2, 4, 8)


def records(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def complete(record):
    return record["error"] is None and (
        record["solved"] or record["attempt"] == 4)


def run_one(task):
    setup_id, rng_state, rate, csi, optimized = task
    np.random.set_state(rng_state)
    cls = OptimizedProblem if optimized else Problem
    problem = cls(16, 16, 4, 1000, N_sim=100)
    problem.set_constraints((2**rate - 1)*np.ones(16),
                            1000*np.ones(16), 4, csi)
    lines = []
    attempts = []
    for attempt in range(1, 5):
        kappa = 10 * 3**(attempt-1)
        stream = io.StringIO()
        start = time.perf_counter()
        error = None
        try:
            with contextlib.redirect_stdout(stream):
                problem.solve(toll_fp=1e-3, toll_psg=1, kappa=kappa,
                              feas_only=True)
        except Exception as exc:
            error = repr(exc)
        duration = time.perf_counter() - start
        lines.append(f"setup_id={setup_id} rate={rate} csi={csi} attempt={attempt}\n"
                     + stream.getvalue())
        attempts.append({
            "setup_id": setup_id, "rate": rate, "csi": csi,
            "attempt": attempt, "kappa": kappa, "seconds": duration,
            "outer_iterations": len(problem.dual_obj),
            "solved": bool(problem.solved),
            "feasible_per_ap": bool(problem.feasible),
            "feasible_sum": bool(problem.feasible_sum),
            "final_dual_mw": float(problem.dual_obj[-1]) if problem.dual_obj else None,
            "final_max_ap_violation_mw": (
                float(np.max(problem.powers[-1]-problem.P_max))
                if problem.powers else None),
            "error": error,
        })
        if problem.solved or error:
            break
    return setup_id, attempts, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimized", action="store_true")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--verify-first", type=int, default=0,
                        help="Rerun this many existing setups as a parity check")
    cfg = parser.parse_args()
    folder = ROOT/"results"/(
        "figure2_full_optimized" if cfg.optimized else "figure2_full")
    serial = records(folder/"attempts.jsonl")
    parallel_file = folder/"parallel_attempts.jsonl"
    parallel = records(parallel_file)
    latest = {r["setup_id"]: r for r in serial + parallel}
    complete_ids = {i for i, r in latest.items() if complete(r)}
    targets = set(range(1, 1601)) - complete_ids
    # The serial process may have been interrupted during its last setup.
    if serial:
        targets.add(max(r["setup_id"] for r in serial))
    if cfg.verify_first:
        targets.update(range(1, cfg.verify_first+1))
    tasks = []
    started = time.time()
    for ri, rate in enumerate(RATES):
        for ci, csi in enumerate(("local", "centr")):
            np.random.seed(0)
            for n in range(100):
                setup_id = ri*200 + ci*100 + n + 1
                state = np.random.get_state()
                # Advance exactly as the author's script does before next setup.
                Problem(16, 16, 4, 1000, N_sim=100)
                if setup_id in targets:
                    tasks.append((setup_id, state, float(rate), csi, cfg.optimized))
    print(f"{len(tasks)} setup tasks, {len(complete_ids)} already complete",
          flush=True)
    (folder/"parallel_logs").mkdir(exist_ok=True)
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=cfg.workers, mp_context=context) as pool:
        futures = {pool.submit(run_one, task): task[0] for task in tasks}
        done = 0
        for future in as_completed(futures):
            setup_id, new_records, log = future.result()
            (folder/"parallel_logs"/f"setup_{setup_id:04d}.log").write_text(log)
            with parallel_file.open("a") as stream:
                for record in new_records:
                    stream.write(json.dumps(record)+"\n")
            done += 1
            if done % 10 == 0 or done == len(tasks):
                print(f"completed {done}/{len(tasks)}", flush=True)
    all_records = serial + records(parallel_file)
    latest = {r["setup_id"]: r for r in all_records}
    if len(latest) != 1600 or not all(complete(r) for r in latest.values()):
        raise RuntimeError("Not all 1600 setups reached the author retry decision")
    grouped = defaultdict(list)
    for r in latest.values():
        grouped[(r["rate"],r["csi"])].append(r)
    fields = ["rate","csi","setups","solved","per_ap_feasible",
              "sum_feasible","per_ap_probability_among_solved",
              "sum_probability_among_solved"]
    rows = []
    for (rate,csi), group in sorted(grouped.items()):
        solved = sum(r["solved"] for r in group)
        per_ap = sum(r["feasible_per_ap"] for r in group if r["solved"])
        sum_feasible = sum(r["feasible_sum"] for r in group if r["solved"])
        rows.append({
            "rate":rate,"csi":csi,"setups":len(group),"solved":solved,
            "per_ap_feasible":per_ap,"sum_feasible":sum_feasible,
            "per_ap_probability_among_solved":per_ap/solved if solved else "",
            "sum_probability_among_solved":sum_feasible/solved if solved else "",
        })
    with (folder/"summary.csv").open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fields)
        writer.writeheader()
        writer.writerows(rows)
    fig,ax = plt.subplots(figsize=(7,4))
    for csi,color,marker in (("local","b","o"),("centr","r","d")):
        q=sorted((r for r in rows if r["csi"]==csi),key=lambda r:r["rate"])
        x=[r["rate"] for r in q]
        ax.plot(x,[r["per_ap_probability_among_solved"] for r in q],
                f"-{color}{marker}",label=f"{csi} per-AP")
        ax.plot(x,[r["sum_probability_among_solved"] for r in q],
                f"--{color}{marker}",label=f"{csi} sum power")
    ax.set(xlabel="Minimum rate [bit/s/Hz]",ylabel="Probability of feasibility",
           ylim=(-0.05,1.05))
    ax.grid(True)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(folder/"figure2_full.png",dpi=180)
    (folder/"metadata_final.json").write_text(json.dumps({
        "status":"completed","method":"OptimizedProblem" if cfg.optimized else "Problem",
        "setups":len(latest),"serial_attempts":len(serial),
        "parallel_attempts":len(records(parallel_file)),
        "parallel_started_unix":started,"finished_unix":time.time(),
        "workers":cfg.workers,
        "rng_policy":"np.random.seed(0) independently for each rate and CSI; consecutive 100 Problem constructions",
        "rates":list(map(float,RATES)),"N_setups":100,"N_sim":100,
        "L":16,"K":16,"N":4,"Q":4,"size":1000,"P_max_mw":1000,
        "attempts_max":4,"kappa_sequence":[10,30,90,270],
        "tol_fp":1e-3,"tol_psg":1,"iter_max_psg":100,"feas_only":True,
        "python":sys.version,"platform":platform.platform(),
        "numpy":np.__version__,"scipy":scipy.__version__,
        "matplotlib":matplotlib.__version__,
        "openblas_num_threads":os.environ.get("OPENBLAS_NUM_THREADS"),
    },indent=2))
    print("Completed all 1600 setups",flush=True)


if __name__ == "__main__":
    main()

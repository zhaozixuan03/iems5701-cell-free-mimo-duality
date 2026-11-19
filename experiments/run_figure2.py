"""Reduced Monte Carlo reproduction of the author's Figure 2 workflow."""
import argparse
import contextlib
import csv
import io
import json
import os
import platform
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    p.add_argument("--rates", type=float, nargs="+", default=[2, 3, 4])
    p.add_argument("--n-sim", type=int, default=20)
    p.add_argument("--max-outer", type=int, default=20)
    p.add_argument("--attempts", type=int, default=2)
    p.add_argument("--output", type=Path, default=ROOT/"results"/"figure2_scaled")
    cfg = p.parse_args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    records = []
    for rate in cfg.rates:
        for seed in cfg.seeds:
            for csi in ("local", "centr"):
                np.random.seed(seed)
                problem = Problem(16,16,4,1000,N_sim=cfg.n_sim)
                problem.set_constraints((2**rate-1)*np.ones(16),
                                        1000*np.ones(16),4,csi)
                attempts = []
                for attempt in range(cfg.attempts):
                    log = io.StringIO()
                    start = time.perf_counter()
                    error = None
                    try:
                        with contextlib.redirect_stdout(log):
                            problem.solve(toll_fp=1e-3,toll_psg=1,
                                          iter_max_psg=cfg.max_outer,
                                          kappa=10*3**attempt,feas_only=True)
                    except Exception as exc:
                        error = repr(exc)
                    attempts.append({"attempt":attempt+1,"kappa":10*3**attempt,
                                     "seconds":time.perf_counter()-start,
                                     "outer_iterations":len(problem.dual_obj),
                                     "solved":bool(problem.solved),"error":error,
                                     "stdout":log.getvalue()})
                    if problem.solved or error:
                        break
                record = {"rate":rate,"seed":seed,"csi":csi,
                          "solved":bool(problem.solved),
                          "feasible_per_ap":bool(problem.feasible),
                          "feasible_sum":bool(problem.feasible_sum),
                          "attempts":attempts}
                records.append(record)
                print(rate,seed,csi,record["solved"],
                      record["feasible_per_ap"],flush=True)
    (cfg.output/"runs.json").write_text(json.dumps(records,indent=2))
    (cfg.output/"config.json").write_text(json.dumps(vars(cfg),indent=2,default=str))
    (cfg.output/"environment.json").write_text(json.dumps({
        "python":sys.version,"platform":platform.platform(),
        "numpy":np.__version__,"scipy":scipy.__version__,
        "matplotlib":matplotlib.__version__,
        "openblas_num_threads":os.environ.get("OPENBLAS_NUM_THREADS"),
    },indent=2))
    fields = ["rate","seed","csi","solved","feasible_per_ap","feasible_sum"]
    with (cfg.output/"summary.csv").open("w",newline="") as f:
        w = csv.DictWriter(f,fields)
        w.writeheader()
        w.writerows({k:r[k] for k in fields} for r in records)
    fig,ax = plt.subplots(figsize=(7,4))
    for csi in ("local","centr"):
        for key,style in (("feasible_per_ap","-o"),("feasible_sum","--o")):
            ys = []
            for rate in cfg.rates:
                subset = [r for r in records if r["rate"]==rate and r["csi"]==csi and r["solved"]]
                ys.append(np.mean([r[key] for r in subset]) if subset else np.nan)
            ax.plot(cfg.rates,ys,style,label=f"{csi} {key}")
    ax.set(xlabel="Minimum rate (bit/s/Hz)",ylabel="Feasibility fraction among solved",
           ylim=(-0.05,1.05),title="Reduced Figure 2 experiment")
    ax.grid(True)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(cfg.output/"feasibility.png",dpi=160)


if __name__ == "__main__":
    main()

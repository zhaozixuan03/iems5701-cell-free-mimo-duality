"""Paired physical-layer comparison of strongest-Q and load-aware AP clusters."""
import argparse
import contextlib
import io
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from optimized_problem import OptimizedProblem
from load_aware_problem import LoadAwareProblem


def run(problem,cfg):
    attempts=[]
    for i in range(cfg.attempts):
        log=io.StringIO();start=time.perf_counter();error=None
        try:
            with contextlib.redirect_stdout(log):
                problem.solve(toll_fp=getattr(cfg,'tol_fp',1e-3),
                              toll_psg=getattr(cfg,'tol_psg',1),iter_max_psg=cfg.max_outer,
                              kappa=10*3**i,feas_only=True)
        except Exception as exc:
            error=repr(exc)
        attempts.append({'kappa':10*3**i,'seconds':time.perf_counter()-start,
                         'outer_iterations':len(problem.dual_obj),
                         'solved':bool(problem.solved),'feasible':bool(problem.feasible),
                         'error':error,'stdout':log.getvalue()})
        if problem.solved or error:break
    return {'method':type(problem).__name__,
            'solved':bool(problem.solved),'feasible_per_ap':bool(problem.feasible),
            'feasible_sum':bool(problem.feasible_sum),
            'final_power_gap_mw':float(np.max(problem.powers[-1]-problem.P_max))
                if problem.powers else None,
            'final_dual_mw':float(problem.dual_obj[-1]) if problem.dual_obj else None,
            'attempts':attempts,
            'total_solve_s':sum(x['seconds'] for x in attempts)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,nargs='+',default=list(range(12)))
    p.add_argument('--rates',type=float,nargs='+',default=[3.0,3.5,4.0])
    p.add_argument('--n-sim',type=int,default=20)
    p.add_argument('--Q',type=int,default=4)
    p.add_argument('--max-outer',type=int,default=30)
    p.add_argument('--attempts',type=int,default=2)
    p.add_argument('--output',type=Path,default=Path('results/clustering_pilot'))
    cfg=p.parse_args()
    cfg.output.mkdir(parents=True,exist_ok=True)
    metadata={'config':{k:str(v) if isinstance(v,Path) else v for k,v in vars(cfg).items()},
              'python':sys.version,'platform':platform.platform(),
              'numpy':np.__version__,'scipy':scipy.__version__,
              'openblas_num_threads':os.getenv('OPENBLAS_NUM_THREADS'),
              'policy':'Gamma/(1+load), weak users first; same Q, CSI, power, solver'}
    (cfg.output/'metadata.json').write_text(json.dumps(metadata,indent=2))
    with (cfg.output/'runs.jsonl').open('w') as out:
        for rate in cfg.rates:
            for seed in cfg.seeds:
                problems=[]
                for cls in (OptimizedProblem,LoadAwareProblem):
                    np.random.seed(seed)
                    problem=cls(16,16,4,1000,N_sim=cfg.n_sim)
                    problem.set_constraints((2**rate-1)*np.ones(16),1000*np.ones(16),cfg.Q,'local')
                    problems.append(problem)
                assert np.array_equal(problems[0].Gamma,problems[1].Gamma)
                assert np.array_equal(problems[0].H_list[0][0],problems[1].H_list[0][0])
                changed=sum(set(problems[0].UE_clusters[k])!=set(problems[1].UE_clusters[k])
                            for k in range(16))
                record={'rate':rate,'seed':seed,'changed_user_clusters':changed,
                        'baseline_load':list(map(len,problems[0].AP_clusters)),
                        'proposed_load':problems[1].ap_load.tolist(),'runs':[]}
                methods=problems if seed%2==0 else problems[::-1]
                for problem in methods:
                    x=run(problem,cfg);record['runs'].append(x)
                    print(rate,seed,x['method'],x['solved'],x['feasible_per_ap'],
                          round(x['total_solve_s'],3),flush=True)
                out.write(json.dumps(record,allow_nan=False)+'\n');out.flush()


if __name__=='__main__':main()

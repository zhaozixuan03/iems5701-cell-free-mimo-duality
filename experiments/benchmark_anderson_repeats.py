"""Repeated paired timing on three nontrivial scenarios."""
import argparse
import csv
import json
import statistics
from pathlib import Path

from benchmark_anderson import AndersonProblem, OptimizedProblem, execute


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seeds',nargs='+',type=int,default=[51,72,75])
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--output',type=Path,default=Path('results/anderson_repeats'))
    cfg=parser.parse_args()
    cfg.L,cfg.K,cfg.N,cfg.Q=16,16,4,4
    cfg.size,cfg.n_sim,cfg.p_max,cfg.rate=1000,100,1000,3.5
    cfg.tol_fp,cfg.tol_psg,cfg.max_outer,cfg.kappa=1e-5,0.1,120,17
    cfg.output.mkdir(parents=True,exist_ok=True)
    (cfg.output/'config.json').write_text(json.dumps({k:str(v) if isinstance(v,Path) else v
        for k,v in vars(cfg).items()},indent=2))
    rows=[]
    with (cfg.output/'runs.jsonl').open('w') as out:
        for rep in range(cfg.repeats):
            for seed in cfg.seeds:
                classes=(OptimizedProblem,AndersonProblem) if (seed+rep)%2==0 else (AndersonProblem,OptimizedProblem)
                pair={}
                for cls in classes:
                    x=execute(cls,seed,cfg);x['repeat']=rep;pair[cls.__name__]=x
                    out.write(json.dumps(x,allow_nan=False)+'\n');out.flush()
                a,b=(pair[n] for n in ('OptimizedProblem','AndersonProblem'))
                row={'seed':seed,'repeat':rep,'first':classes[0].__name__,
                     'baseline_s':a['solve_s'],'anderson_s':b['solve_s'],
                     'ratio':a['solve_s']/b['solve_s'],
                     'baseline_inner':a['inner_iterations'],'anderson_inner':b['inner_iterations'],
                     'baseline_outer':a['outer_iterations'],'anderson_outer':b['outer_iterations'],
                     'baseline_feasible':a['feasible_flag'],'anderson_feasible':b['feasible_flag'],
                     'baseline_error':a['error'],'anderson_error':b['error']}
                rows.append(row)
                print(seed,rep,row['ratio'],row['baseline_inner'],row['anderson_inner'],flush=True)
    with (cfg.output/'timings.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    medians={str(seed):statistics.median(r['ratio'] for r in rows if r['seed']==seed)
             for seed in cfg.seeds}
    summary={'per_seed_median_speed_ratio':medians,
             'median_of_seed_medians':statistics.median(medians.values()),
             'pairs':len(rows)}
    (cfg.output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(summary)


if __name__=='__main__':main()

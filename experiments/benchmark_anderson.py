"""Pair the cached baseline with safeguarded inner Anderson acceleration."""
import argparse
import csv
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.run_figure3 import execute
from anderson_problem import AndersonProblem
from optimized_problem import OptimizedProblem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(46, 76)))
    parser.add_argument('--output', type=Path, default=Path('results/anderson_new_seeds'))
    parser.add_argument('--max-outer', type=int, default=120)
    parser.add_argument('--kappa', type=float, default=17)
    cfg = parser.parse_args()
    cfg.L, cfg.K, cfg.N, cfg.Q = 16, 16, 4, 4
    cfg.size, cfg.n_sim, cfg.p_max, cfg.rate = 1000, 100, 1000, 3.5
    cfg.tol_fp, cfg.tol_psg = 1e-5, 0.1
    cfg.output.mkdir(parents=True, exist_ok=True)
    metadata = {'config': {k: str(v.relative_to(ROOT)) if isinstance(v, Path)
                and v.is_absolute() and v.is_relative_to(ROOT) else str(v) if isinstance(v, Path)
                else v for k, v in vars(cfg).items()},
                'python': sys.version, 'platform': platform.platform(),
                'numpy': np.__version__, 'scipy': scipy.__version__,
                'openblas_num_threads': os.getenv('OPENBLAS_NUM_THREADS'),
                'comparison': 'cached optimized baseline versus safeguarded Anderson inner power update'}
    (cfg.output/'metadata.json').write_text(json.dumps(metadata, indent=2))
    rows = []
    with (cfg.output/'runs.jsonl').open('w') as out:
        for seed in cfg.seeds:
            methods = (OptimizedProblem, AndersonProblem) if seed % 2 == 0 else (AndersonProblem, OptimizedProblem)
            for cls in methods:
                record = execute(cls, seed, cfg)
                power_gaps = record['power_gap_trace_mw']
                dual_gaps = record['surrogate_gap_trace_mw']
                record['first_strict_iteration'] = next((i+1 for i,(a,b) in
                    enumerate(zip(power_gaps,dual_gaps)) if a <= cfg.tol_psg
                    and abs(b) <= cfg.tol_psg), None)
                out.write(json.dumps(record, allow_nan=False)+'\n'); out.flush()
                rows.append({k:record[k] for k in ('seed','method','solve_s','outer_iterations',
                    'inner_iterations','solved','feasible_flag','error','final_power_violation_mw',
                    'final_surrogate_gap_mw','final_sinr_gap_reported','first_strict_iteration',
                    'anderson_stats')})
                print(seed,cls.__name__,record['solve_s'],record['outer_iterations'],
                      record['inner_iterations'],record['feasible_flag'],
                      record['first_strict_iteration'],record['error'],flush=True)
    with (cfg.output/'summary.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)


if __name__ == '__main__':
    main()

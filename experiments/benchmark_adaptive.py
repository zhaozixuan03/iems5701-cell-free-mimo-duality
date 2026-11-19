"""Paired, fixed-budget comparison of the feedback step and fixed sqrt step."""
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
from adaptive_problem import AdaptiveProblem
from optimized_problem import OptimizedProblem


def first_hit(values, threshold):
    return next((i + 1 for i, v in enumerate(values) if v <= threshold), None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(16, 46)))
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'adaptive_holdout')
    parser.add_argument('--max-outer', type=int, default=120)
    parser.add_argument('--kappa', type=float, default=17)
    cfg = parser.parse_args()
    cfg.L, cfg.K, cfg.N, cfg.Q = 16, 16, 4, 4
    cfg.size, cfg.n_sim, cfg.p_max, cfg.rate = 1000, 100, 1000, 3.5
    cfg.tol_fp, cfg.tol_psg = 1e-5, 0.1
    cfg.output.mkdir(parents=True, exist_ok=True)
    metadata = {'config': {k: (str(v.relative_to(ROOT)) if v.is_absolute() and v.is_relative_to(ROOT)
                               else str(v)) if isinstance(v, Path) else v
                           for k, v in vars(cfg).items()},
                'python': sys.version, 'platform': platform.platform(),
                'numpy': np.__version__, 'scipy': scipy.__version__,
                'openblas_num_threads': os.getenv('OPENBLAS_NUM_THREADS'),
                'method': 'fixed kappa/sqrt(t) versus AP-violation feedback; identical model and stop rule'}
    (cfg.output/'metadata.json').write_text(json.dumps(metadata, indent=2))
    rows = []
    with (cfg.output/'runs.jsonl').open('w') as out:
        for seed in cfg.seeds:
            methods = (OptimizedProblem, AdaptiveProblem) if seed % 2 == 0 else (AdaptiveProblem, OptimizedProblem)
            for cls in methods:
                record = execute(cls, seed, cfg)
                gaps = record['power_gap_trace_mw']
                dual_gaps = record['surrogate_gap_trace_mw']
                record['first_power_feasible_iteration'] = first_hit(gaps, cfg.tol_psg)
                record['first_strict_iteration'] = next((i+1 for i, (a,b) in enumerate(zip(gaps,dual_gaps))
                    if a <= cfg.tol_psg and abs(b) <= cfg.tol_psg), None)
                out.write(json.dumps(record, allow_nan=False) + '\n'); out.flush()
                rows.append({k: record[k] for k in ('seed','method','solve_s','outer_iterations',
                    'inner_iterations','solved','feasible_flag','error','final_power_violation_mw',
                    'final_surrogate_gap_mw','first_power_feasible_iteration','first_strict_iteration')})
                print(seed, cls.__name__, record['solve_s'], record['outer_iterations'],
                      record['feasible_flag'], record['first_power_feasible_iteration'],
                      record['first_strict_iteration'], record['error'], flush=True)
    with (cfg.output/'summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)


if __name__ == '__main__':
    main()

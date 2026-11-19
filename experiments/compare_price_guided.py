"""Paired AP association test with independent pilot and evaluation fading.

The rule is fixed before the holdout: score Gamma / pilot dual price. Prices
come only from the strongest-Q pilot run. Evaluation uses new fading draws.
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.compare_clustering import run
from optimized_problem import OptimizedProblem
from price_guided_problem import PriceGuidedProblem


def make_problem(cls, seed, n_sim, rate, prices=None, evaluation=False):
    np.random.seed(seed)
    args = (16, 16, 4, 1000)
    kw = {'N_sim': n_sim}
    if prices is not None:
        kw['prices'] = prices
    problem = cls(*args, **kw)
    if evaluation:
        # Keep the same network geometry but draw fresh fading independently
        # of the pilot. Both evaluation methods receive identical channels.
        np.random.seed(100000 + seed)
        problem.draw_channel_realizations(n_sim)
    problem.set_constraints((2**rate - 1) * np.ones(16),
                            1000 * np.ones(16), 4, 'local')
    return problem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(106, 136)))
    parser.add_argument('--rate', type=float, default=3.5)
    parser.add_argument('--pilot-n-sim', type=int, default=20)
    parser.add_argument('--eval-n-sim', type=int, default=80)
    parser.add_argument('--max-outer', type=int, default=40)
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--output', type=Path, default=Path('results/price_guided_holdout'))
    cfg = parser.parse_args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    metadata = {'config': {k: str(v) if isinstance(v, Path) else v
                           for k, v in vars(cfg).items()},
                'python': sys.version, 'platform': platform.platform(),
                'numpy': np.__version__, 'scipy': scipy.__version__,
                'openblas_num_threads': os.getenv('OPENBLAS_NUM_THREADS'),
                'selection': 'Q=4 strongest Gamma/dual_price; no candidate search',
                'fading': 'same geometry, fresh independent pilot/evaluation draws'}
    (cfg.output / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    with (cfg.output / 'runs.jsonl').open('w') as out:
        for seed in cfg.seeds:
            pilot = make_problem(OptimizedProblem, seed, cfg.pilot_n_sim, cfg.rate)
            pilot_run = run(pilot, cfg)
            prices = np.maximum(np.asarray(pilot.sig_opt, dtype=float), 1)
            base = make_problem(OptimizedProblem, seed, cfg.eval_n_sim,
                                cfg.rate, evaluation=True)
            proposed = make_problem(PriceGuidedProblem, seed, cfg.eval_n_sim,
                                    cfg.rate, prices=prices, evaluation=True)
            assert np.array_equal(base.Gamma, proposed.Gamma)
            assert np.array_equal(base.Gamma, pilot.Gamma)
            assert np.array_equal(base.H_list[0][0], proposed.H_list[0][0])
            assert not np.array_equal(base.H_list[0][0], pilot.H_list[0][0])
            changed = sum(set(base.UE_clusters[k]) != set(proposed.UE_clusters[k])
                          for k in range(base.K))
            methods = (base, proposed) if seed % 2 == 0 else (proposed, base)
            runs = [run(p, cfg) for p in methods]
            record = {'seed': seed, 'rate': cfg.rate, 'pilot_prices': prices.tolist(),
                      'pilot_run': pilot_run, 'changed_user_clusters': changed,
                      'baseline_clusters': base.UE_clusters.tolist(),
                      'proposed_clusters': proposed.UE_clusters.tolist(),
                      'runs': runs}
            out.write(json.dumps(record, allow_nan=False) + '\n')
            out.flush()
            statuses = {r['method']: ('feasible' if r['feasible_per_ap'] else
                        'infeasible_certificate' if r['solved'] else 'unresolved')
                        for r in runs}
            print(seed, changed, statuses, flush=True)


if __name__ == '__main__':
    main()

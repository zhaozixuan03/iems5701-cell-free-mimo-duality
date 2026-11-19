"""Paired simulation: equal total CSI links, variable versus fixed per-user Q."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.compare_clustering import run
from optimized_problem import OptimizedProblem
from variable_q_problem import VariableQProblem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', nargs='+', type=int, default=list(range(136, 166)))
    parser.add_argument('--rates', nargs='+', type=float, default=[3.5])
    parser.add_argument('--n-sim', type=int, default=100)
    parser.add_argument('--max-outer', type=int, default=40)
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--tol-fp', type=float, default=1e-3)
    parser.add_argument('--tol-psg', type=float, default=1)
    parser.add_argument('--output', type=Path, default=Path('results/variable_q_holdout'))
    cfg = parser.parse_args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    (cfg.output / 'metadata.json').write_text(json.dumps({
        'config': {k: str(v) if isinstance(v, Path) else v for k, v in vars(cfg).items()},
        'python': sys.version, 'platform': platform.platform(),
        'numpy': np.__version__, 'scipy': scipy.__version__,
        'openblas_num_threads': os.getenv('OPENBLAS_NUM_THREADS'),
        'prespecified_rule': '4 weakest Q=6, middle 8 Q=4, 4 strongest Q=2 by sum of top-4 Gamma; 64 total CSI links',
        'comparison': 'same topology, fading, rate, total links and optimizer; per-user Q differs'
    }, indent=2))
    with (cfg.output / 'runs.jsonl').open('w') as out:
        for rate in cfg.rates:
            for seed in cfg.seeds:
                problems = []
                for cls in (OptimizedProblem, VariableQProblem):
                    np.random.seed(seed)
                    problem = cls(16, 16, 4, 1000, N_sim=cfg.n_sim)
                    problem.set_constraints((2**rate - 1)*np.ones(16),
                                            1000*np.ones(16), 4, 'local')
                    problems.append(problem)
                base, proposed = problems
                assert np.array_equal(base.Gamma, proposed.Gamma)
                assert np.array_equal(base.H_list[0][0], proposed.H_list[0][0])
                assert sum(map(len, base.UE_clusters)) == sum(map(len, proposed.UE_clusters)) == 64
                methods = problems if seed % 2 == 0 else problems[::-1]
                runs = [run(p, cfg) for p in methods]
                record = {'seed': seed, 'rate': rate,
                          'q_by_user': proposed.q_by_user.tolist(),
                          'baseline_clusters': base.UE_clusters.tolist(),
                          'proposed_clusters': [c.tolist() for c in proposed.UE_clusters],
                          'runs': runs}
                out.write(json.dumps(record, allow_nan=False)+'\n')
                out.flush()
                print(rate, seed, {r['method']: (r['solved'], r['feasible_per_ap'])
                                   for r in runs}, flush=True)


if __name__ == '__main__':
    main()

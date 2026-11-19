"""Paired effect sizes and uncertainty for the prespecified 30-seed holdout."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path, nargs='?',
                        default=Path('results/anderson_new_seeds'))
    cfg = parser.parse_args()
    rows = [json.loads(line) for line in (cfg.folder / 'runs.jsonl').read_text().splitlines()]
    paired = {}
    for row in rows:
        paired.setdefault(row['seed'], {})[row['method']] = row
    seeds = sorted(paired)
    assert all(set(paired[s]) == {'OptimizedProblem', 'AndersonProblem'} for s in seeds)
    base = [paired[s]['OptimizedProblem'] for s in seeds]
    acc = [paired[s]['AndersonProblem'] for s in seeds]
    assert all(a['feasible_flag'] == b['feasible_flag'] for a, b in zip(base, acc))
    inner_b = np.array([r['inner_iterations'] for r in base], dtype=float)
    inner_a = np.array([r['inner_iterations'] for r in acc], dtype=float)
    time_b = np.array([r['solve_s'] for r in base], dtype=float)
    time_a = np.array([r['solve_s'] for r in acc], dtype=float)
    rng = np.random.default_rng(5701)
    picks = rng.integers(0, len(seeds), size=(10000, len(seeds)))
    def reduction(b, a):
        samples = 1 - a[picks].sum(axis=1) / b[picks].sum(axis=1)
        return {'point': float(1 - a.sum() / b.sum()),
                'bootstrap_95_percentile': [float(x) for x in np.quantile(samples, [.025, .975])]}
    success = np.array([r['feasible_flag'] for r in base], dtype=bool)
    wins = int(np.sum((inner_a < inner_b) & success))
    losses = int(np.sum((inner_a > inner_b) & success))
    ties = int(np.sum((inner_a == inner_b) & success))
    # One-sided exact paired sign test, conditional on non-tied successful cases.
    from math import comb
    n = wins + losses
    p_sign = sum(comb(n, k) for k in range(wins, n+1)) / (2**n) if n else None
    result = {'seeds': seeds, 'success_count_each': int(success.sum()),
              'inner_reduction': reduction(inner_b, inner_a),
              'time_reduction': reduction(time_b, time_a),
              'successful_inner_win_tie_loss': [wins, ties, losses],
              'one_sided_sign_p_successful_nonties': p_sign,
              'note': 'Seed bootstrap describes variation over these sampled networks; runtime also has measurement noise. The sign test excludes ties and unsuccessful networks.'}
    (cfg.folder / 'paired_effect.json').write_text(json.dumps(result, indent=2))
    fig, ax = plt.subplots(1, 2, figsize=(9, 4))
    for mask, label, color in [(success, 'Both feasible', '#007b83'),
                               (~success, 'Both not feasible', '#c87931')]:
        ax[0].scatter(inner_b[mask], inner_a[mask], label=label, color=color)
        ax[1].scatter(time_b[mask], time_a[mask], label=label, color=color)
    for a, b, label in zip(ax, [(inner_b, inner_a), (time_b, time_a)],
                           ['Inner iterations', 'Solve time (s)']):
        hi = max(float(np.max(b[0])), float(np.max(b[1]))) * 1.05
        a.plot([0, hi], [0, hi], color='gray', linestyle='--', linewidth=1)
        a.set(xlim=(0, hi), ylim=(0, hi), xlabel='Cached baseline ' + label,
              ylabel='Anderson ' + label)
        a.grid(alpha=.2)
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(cfg.folder / 'paired_effect.png', dpi=170)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

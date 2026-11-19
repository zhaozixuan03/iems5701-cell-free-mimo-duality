"""Summarize every paired adaptive-step outcome without dropping failures."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    rows = list(csv.DictReader((args.directory/'summary.csv').open()))
    pairs = {}
    for row in rows:
        pairs.setdefault(int(row['seed']), {})[row['method']] = row
    names = ('OptimizedProblem', 'AdaptiveProblem')
    summary = {'n_paired_seeds': len(pairs), 'methods': {},
               'both_success_iteration_wins': {'adaptive': 0, 'fixed': 0, 'ties': 0},
               'status_mismatches': [], 'per_seed': []}
    for name in names:
        sample = [p[name] for p in pairs.values()]
        summary['methods'][name] = {
            'author_success_count': sum(r['feasible_flag'] == 'True' for r in sample),
            'strict_success_count': sum(bool(r['first_strict_iteration']) for r in sample),
            'total_solve_seconds': sum(float(r['solve_s']) for r in sample),
            'total_outer_iterations': sum(int(r['outer_iterations']) for r in sample),
            'total_inner_iterations': sum(int(r['inner_iterations']) for r in sample),
            'errors': sum(bool(r['error']) for r in sample),
            'budget_exhausted': sum(r['solved'] == 'False' for r in sample),
        }
    for seed, p in sorted(pairs.items()):
        fixed, adaptive = (p[n] for n in names)
        fs, ads = (r['feasible_flag'] == 'True' for r in (fixed, adaptive))
        if fs != ads:
            summary['status_mismatches'].append(seed)
        if fs and ads:
            f, a = (int(r['outer_iterations']) for r in (fixed, adaptive))
            key = 'adaptive' if a < f else 'fixed' if a > f else 'ties'
            summary['both_success_iteration_wins'][key] += 1
        summary['per_seed'].append({'seed': seed, 'fixed_success': fs,
            'adaptive_success': ads, 'fixed_outer': int(fixed['outer_iterations']),
            'adaptive_outer': int(adaptive['outer_iterations']),
            'fixed_seconds': float(fixed['solve_s']),
            'adaptive_seconds': float(adaptive['solve_s'])})
    (args.directory/'aggregate.json').write_text(json.dumps(summary, indent=2))

    informative = [x for x in summary['per_seed'] if max(x['fixed_outer'], x['adaptive_outer']) > 1]
    fig, ax = plt.subplots(figsize=(9, 5))
    for x in informative:
        color = 'tab:blue' if x['fixed_success'] and x['adaptive_success'] else 'tab:gray'
        ax.plot([x['fixed_outer'], x['adaptive_outer']],
                [x['seed'], x['seed']], color=color)
        ax.scatter(x['fixed_outer'], x['seed'], marker='o', color=color)
        ax.scatter(x['adaptive_outer'], x['seed'], marker='x', color=color)
    ax.set(xlabel='Outer iterations (circle: fixed; cross: adaptive)',
           ylabel='Random seed', title='Paired adaptive-step comparison')
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(args.directory/'outer_iterations.png', dpi=160)
    print(json.dumps({k: v for k, v in summary.items() if k != 'per_seed'}, indent=2))


if __name__ == '__main__':
    main()

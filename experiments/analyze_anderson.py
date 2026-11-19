"""Summarize every paired run, including budget exhaustion and infeasibility."""
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
    names = ('OptimizedProblem', 'AndersonProblem')
    result = {'n_paired_seeds': len(pairs), 'methods': {},
              'status_mismatches': [], 'strict_mismatches': [],
              'both_success_inner_wins': {'anderson': 0, 'baseline': 0, 'ties': 0},
              'per_seed': []}
    for name in names:
        sample = [p[name] for p in pairs.values()]
        result['methods'][name] = {
            'author_success_count': sum(x['feasible_flag']=='True' for x in sample),
            'strict_success_count': sum(bool(x['first_strict_iteration']) for x in sample),
            'total_solve_seconds': sum(float(x['solve_s']) for x in sample),
            'total_outer_iterations': sum(int(x['outer_iterations']) for x in sample),
            'total_inner_iterations': sum(int(x['inner_iterations']) for x in sample),
            'budget_exhausted': sum(x['solved']=='False' for x in sample),
            'errors': sum(bool(x['error']) for x in sample),
        }
    for seed,p in sorted(pairs.items()):
        a,b = (p[n] for n in names)
        aok,bok = (x['feasible_flag']=='True' for x in (a,b))
        astrict,bstrict = (bool(x['first_strict_iteration']) for x in (a,b))
        if aok != bok: result['status_mismatches'].append(seed)
        if astrict != bstrict: result['strict_mismatches'].append(seed)
        if aok and bok:
            ai,bi = (int(x['inner_iterations']) for x in (a,b))
            key = 'anderson' if bi<ai else 'baseline' if bi>ai else 'ties'
            result['both_success_inner_wins'][key] += 1
        result['per_seed'].append({'seed':seed,'baseline_success':aok,'anderson_success':bok,
            'baseline_inner':int(a['inner_iterations']),'anderson_inner':int(b['inner_iterations']),
            'baseline_outer':int(a['outer_iterations']),'anderson_outer':int(b['outer_iterations']),
            'baseline_s':float(a['solve_s']),'anderson_s':float(b['solve_s']),
            'baseline_power_gap_mw':float(a['final_power_violation_mw']),
            'anderson_power_gap_mw':float(b['final_power_violation_mw']),
            'baseline_dual_gap_mw':float(a['final_surrogate_gap_mw']),
            'anderson_dual_gap_mw':float(b['final_surrogate_gap_mw'])})
    (args.directory/'aggregate.json').write_text(json.dumps(result,indent=2))
    fig,ax=plt.subplots(figsize=(6,6))
    for x in result['per_seed']:
        color='tab:blue' if x['baseline_success'] and x['anderson_success'] else 'tab:gray'
        ax.scatter(x['baseline_inner'],x['anderson_inner'],color=color,s=24)
    maximum=max(max(x['baseline_inner'],x['anderson_inner']) for x in result['per_seed'])
    ax.plot([0,maximum],[0,maximum],color='black',linestyle='--',linewidth=1)
    ax.set(xlabel='Cached baseline inner iterations',ylabel='Anderson inner iterations',
           title='Matched random scenarios')
    ax.grid(alpha=.25);fig.tight_layout();fig.savefig(args.directory/'inner_iterations.png',dpi=160)
    print(json.dumps({k:v for k,v in result.items() if k!='per_seed'},indent=2))


if __name__=='__main__':
    main()

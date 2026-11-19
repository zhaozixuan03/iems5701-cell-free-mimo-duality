"""Summarize all outcomes, separating certified failures from solver timeouts."""
import argparse
import json
import re
from pathlib import Path
from math import comb

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def sinr_gap(run):
    text = run['attempts'][-1]['stdout']
    hits = re.findall(r'max SINR gap: ([^\n]+)', text)
    return float(hits[-1]) if hits else None


def status(run):
    if any(a['error'] for a in run['attempts']):
        return 'error'
    if run['feasible_per_ap']:
        return 'feasible'
    if run['solved']:
        return 'solver_infeasible'
    return 'unresolved'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    cfg = parser.parse_args()
    data = [json.loads(x) for x in (cfg.folder/'runs.jsonl').read_text().splitlines()]
    pairs = []
    for row in data:
        runs = {r['method']: r for r in row['runs']}
        b, p = runs['OptimizedProblem'], runs['VariableQProblem']
        pairs.append({'seed': row['seed'], 'rate': row['rate'],
                      'fixed': status(b), 'variable': status(p),
                      'fixed_power_gap_mw': b['final_power_gap_mw'],
                      'variable_power_gap_mw': p['final_power_gap_mw'],
                      'fixed_sinr_gap': sinr_gap(b),
                      'variable_sinr_gap': sinr_gap(p),
                      'fixed_solve_s': b['total_solve_s'],
                      'variable_solve_s': p['total_solve_s']})
    categories = ['feasible', 'solver_infeasible', 'unresolved', 'error']
    fixed_success = np.array([x['fixed'] == 'feasible' for x in pairs], dtype=int)
    variable_success = np.array([x['variable'] == 'feasible' for x in pairs], dtype=int)
    gain = int(np.sum((fixed_success == 0) & (variable_success == 1)))
    loss = int(np.sum((fixed_success == 1) & (variable_success == 0)))
    discordant = gain + loss
    rates = sorted(set(x['rate'] for x in pairs))
    if len(rates) == 1:
        rng = np.random.default_rng(5702)
        samples = rng.integers(0, len(pairs), size=(10000, len(pairs)))
        differences = (variable_success - fixed_success)[samples].mean(axis=1)
        bootstrap_ci = [float(x) for x in np.quantile(differences,[.025,.975])]
        exact_p = min(1.0, 2*sum(comb(discordant, k) for k in
                                range(0, min(gain, loss)+1)) / 2**discordant) if discordant else 1.0
    else:
        # The same network seeds recur at multiple rates, so the combined
        # rows are not independent units for bootstrap or McNemar inference.
        bootstrap_ci = None
        exact_p = None
    by_rate = {}
    for rate in rates:
        subset = [x for x in pairs if x['rate'] == rate]
        by_rate[str(rate)] = {
            'networks': len(subset),
            'fixed_feasible': sum(x['fixed'] == 'feasible' for x in subset),
            'variable_feasible': sum(x['variable'] == 'feasible' for x in subset),
            'gain': sum(x['fixed'] != 'feasible' and x['variable'] == 'feasible'
                        for x in subset),
            'loss': sum(x['fixed'] == 'feasible' and x['variable'] != 'feasible'
                        for x in subset)}
    summary = {'networks': len(pairs), 'rate': rates, 'by_rate': by_rate,
               'fixed': {s: sum(x['fixed'] == s for x in pairs) for s in categories},
               'variable': {s: sum(x['variable'] == s for x in pairs) for s in categories},
               'paired_success_gain_loss': [gain, loss],
               'success_difference': float((variable_success-fixed_success).mean()),
               'paired_seed_bootstrap_95_percentile': bootstrap_ci,
               'two_sided_exact_mcnemar_p': exact_p,
               'certified_gain_seeds': [x['seed'] for x in pairs if x['fixed'] ==
                                        'solver_infeasible' and x['variable'] == 'feasible'],
               'certified_loss_seeds': [x['seed'] for x in pairs if x['fixed'] ==
                                        'feasible' and x['variable'] == 'solver_infeasible'],
               'gain_from_unresolved_seeds': [x['seed'] for x in pairs if x['fixed'] ==
                                              'unresolved' and x['variable'] == 'feasible'],
               'loss_to_unresolved_seeds': [x['seed'] for x in pairs if x['fixed'] ==
                                            'feasible' and x['variable'] == 'unresolved'],
               'total_solve_s': {'fixed': sum(x['fixed_solve_s'] for x in pairs),
                                 'variable': sum(x['variable_solve_s'] for x in pairs)},
               'max_positive_sinr_gap_when_feasible': {
                   method: max([x[method+'_sinr_gap'] for x in pairs if
                                x[method] == 'feasible'] or [float('nan')])
                   for method in ('fixed','variable')},
               'pairs': pairs}
    (cfg.folder/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
    fig, ax = plt.subplots(figsize=(7, 4))
    fixed = np.array([summary['fixed'][x] for x in categories])
    variable = np.array([summary['variable'][x] for x in categories])
    xx = np.arange(len(categories))
    ax.bar(xx-.19, fixed, width=.38, label='Fixed Q=4')
    ax.bar(xx+.19, variable, width=.38, label='Variable Q, same 64 links')
    ax.set(xticks=xx, xticklabels=['Feasible', 'Solver infeasible', 'Unresolved', 'Error'],
           ylabel='Network count', title='Paired AP association outcomes')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=.2)
    fig.tight_layout()
    fig.savefig(cfg.folder/'outcomes.png', dpi=170)
    paired_counts = [int(np.sum((fixed_success == 1) & (variable_success == 1))),
                     gain, loss,
                     int(np.sum((fixed_success == 0) & (variable_success == 0)))]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    labels = ['Both feasible', 'Variable only', 'Fixed only', 'Neither feasible']
    colors = ['#4e8495', '#e88b28', '#b84d4d', '#9aa4ac']
    ax.barh(labels, paired_counts, color=colors)
    ax.invert_yaxis()
    for i, count in enumerate(paired_counts):
        ax.text(count + .15, i, str(count), va='center')
    ax.set(xlabel='Paired network count', xlim=(0,max(paired_counts)+4),
           title='Which networks became feasible?')
    ax.grid(axis='x',alpha=.2)
    fig.tight_layout()
    fig.savefig(cfg.folder/'paired_outcomes.png',dpi=170)
    if len(rates) > 1:
        fig, ax = plt.subplots(figsize=(6, 4))
        for key, label in [('fixed_feasible','Fixed Q=4'),
                           ('variable_feasible','Variable Q, same 64 links')]:
            ax.plot(rates, [by_rate[str(r)][key]/by_rate[str(r)]['networks']
                            for r in rates], marker='o', label=label)
        ax.set(xlabel='Target spectral efficiency (bit/s/Hz)',
               ylabel='Feasible fraction', ylim=(0,1),
               title='Rate stress test (paired networks at each rate)')
        ax.legend(fontsize=8)
        ax.grid(alpha=.2)
        fig.tight_layout()
        fig.savefig(cfg.folder/'feasibility_vs_rate.png', dpi=170)
    print(json.dumps({k:v for k,v in summary.items() if k != 'pairs'},indent=2))


if __name__ == '__main__':
    main()

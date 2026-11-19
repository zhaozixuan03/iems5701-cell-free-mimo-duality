"""Save per-AP powers for one illustrative fresh-validation network."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.compare_clustering import run
from optimized_problem import OptimizedProblem
from variable_q_problem import VariableQProblem


def main():
    seed, rate = 177, 3.5
    folder = ROOT/'results/variable_q_illustration_seed177'
    folder.mkdir(parents=True, exist_ok=True)
    cfg = SimpleNamespace(attempts=2, max_outer=120, tol_fp=1e-5, tol_psg=0.1)
    records = []
    for cls in (OptimizedProblem, VariableQProblem):
        np.random.seed(seed)
        problem = cls(16,16,4,1000,N_sim=100)
        problem.set_constraints((2**rate-1)*np.ones(16),
                                1000*np.ones(16),4,'local')
        result = run(problem,cfg)
        result['per_ap_power_mw'] = np.asarray(problem.powers[-1]).tolist()
        result['q_by_user'] = [len(x) for x in problem.UE_clusters]
        result['clusters'] = [list(map(int,x)) for x in problem.UE_clusters]
        records.append(result)
    (folder/'data.json').write_text(json.dumps({'seed':seed,'rate':rate,
        'n_sim':100,'max_outer':120,'tol_fp':1e-5,'tol_psg':0.1,
        'methods':records,
        'note':'Post-hoc illustration only. Fixed-Q final iterate is solver-infeasible, not a feasible design.'},indent=2))
    fig, ax = plt.subplots(figsize=(9,4))
    x = np.arange(16)
    for i, r in enumerate(records):
        ax.bar(x+(.18 if i else -.18),r['per_ap_power_mw'],width=.36,
               label=('Fixed Q=4 (infeasible iterate)' if i==0 else
                      'Variable Q (feasible solution)'))
    ax.axhline(1000,color='#b53d3d',linestyle='--',label='Per-AP limit 1000 mW')
    ax.set(xlabel='AP index',ylabel='Downlink power (mW)',
           xticks=x,title='Network seed 177: equal 64 CSI links, different allocation')
    ax.legend(fontsize=8)
    ax.grid(axis='y',alpha=.2)
    fig.tight_layout()
    fig.savefig(folder/'per_ap_power.png',dpi=170)
    print(folder)


if __name__ == '__main__':
    main()

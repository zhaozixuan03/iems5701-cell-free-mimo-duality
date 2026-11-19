"""Descriptive success count under several wall-clock budgets on this machine."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    runs=json.loads((args.directory/'aggregate.json').read_text())['per_seed']
    budgets=(0.1,0.25,0.5,1.0,2.0,5.0)
    rows=[]
    for t in budgets:
        rows.append({'budget_s':t,'baseline_success':sum(x['baseline_success'] and
                     x['baseline_s']<=t for x in runs),
                     'anderson_success':sum(x['anderson_success'] and
                     x['anderson_s']<=t for x in runs)})
    with (args.directory/'budget_success.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    fig,ax=plt.subplots(figsize=(7,4))
    for field,label in [('baseline_success','Cached baseline'),('anderson_success','Anderson')]:
        ax.step([r['budget_s'] for r in rows],[r[field] for r in rows],where='post',label=label)
        ax.scatter([r['budget_s'] for r in rows],[r[field] for r in rows],s=20)
    ax.set(xlabel='Solve-time budget per scenario (seconds)',ylabel='Scenarios solved within budget',
           title='Descriptive budget view of 30 paired scenarios',xlim=(0,5),ylim=(0,len(runs)+1))
    ax.grid(alpha=.25);ax.legend();fig.tight_layout()
    fig.savefig(args.directory/'budget_success.png',dpi=160)
    print(rows)


if __name__=='__main__':main()

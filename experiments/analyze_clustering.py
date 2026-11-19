"""Summarize exploratory AP-association results, retaining unresolved samples."""
import argparse
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    rows=[json.loads(line) for line in (args.directory/'runs.jsonl').open()]
    summary=[]
    for rate in sorted({x['rate'] for x in rows}):
        subset=[x for x in rows if x['rate']==rate]
        methods={}
        for name in ('OptimizedProblem','LoadAwareProblem'):
            samples=[next(z for z in x['runs'] if z['method']==name) for x in subset]
            methods[name]={'solved':sum(z['solved'] for z in samples),
                           'feasible':sum(z['solved'] and z['feasible_per_ap'] for z in samples),
                           'unresolved':sum(not z['solved'] for z in samples),
                           'total_solve_s':sum(z['total_solve_s'] for z in samples)}
        mismatches=[x['seed'] for x in subset if len({z['solved'] and z['feasible_per_ap']
                    for z in x['runs']})>1]
        summary.append({'rate':rate,'n':len(subset),'mean_changed_user_clusters':
                       sum(x['changed_user_clusters'] for x in subset)/len(subset),
                       'methods':methods,'feasibility_mismatch_seeds':mismatches})
    (args.directory/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()

"""Run four fresh-seed settings sequentially, preserving complete logs."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'anderson_robustness'
OUT.mkdir(parents=True,exist_ok=True)
SEEDS=list(range(76,88))
SETTINGS=[(3.0,4),(4.0,4),(3.5,2),(3.5,8)]
records=[]
for rate,q in SETTINGS:
    name=f'rate_{rate:.1f}_q_{q}'
    folder=OUT/name
    command=[sys.executable,str(ROOT/'experiments'/'benchmark_anderson.py'),
             '--seeds',*map(str,SEEDS),'--rate',str(rate),'--Q',str(q),
             '--output',str(folder)]
    with (OUT/f'{name}_stdout.log').open('w') as stdout, (OUT/f'{name}_stderr.log').open('w') as stderr:
        status=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,
                              env={**os.environ,'OPENBLAS_NUM_THREADS':'1',
                                   'MPLBACKEND':'Agg','MPLCONFIGDIR':'/tmp'})
    if status.returncode:
        raise RuntimeError(f'{name} failed with code {status.returncode}')
    subprocess.run([sys.executable,str(ROOT/'experiments'/'analyze_anderson.py'),str(folder)],
                   cwd=ROOT,check=True,stdout=subprocess.DEVNULL,
                   env={**os.environ,'OPENBLAS_NUM_THREADS':'1',
                        'MPLBACKEND':'Agg','MPLCONFIGDIR':'/tmp'})
    aggregate=json.loads((folder/'aggregate.json').read_text())
    record={'rate':rate,'Q':q,'seeds':SEEDS,
            'baseline':aggregate['methods']['OptimizedProblem'],
            'anderson':aggregate['methods']['AndersonProblem'],
            'status_mismatches':aggregate['status_mismatches'],
            'strict_mismatches':aggregate['strict_mismatches']}
    records.append(record)
    (OUT/'aggregate.json').write_text(json.dumps(records,indent=2))
    print(name,record['baseline']['author_success_count'],
          record['anderson']['author_success_count'],
          record['baseline']['total_inner_iterations'],
          record['anderson']['total_inner_iterations'],flush=True)

"""Combine the same 20 networks at rates 3.0, 3.5 and 4.0 for plotting."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sources = [ROOT/'results/variable_q_rate_stress/runs.jsonl',
           ROOT/'results/variable_q_rate_middle/runs.jsonl']
out = ROOT/'results/variable_q_rate_sweep'
out.mkdir(parents=True, exist_ok=True)
records = [json.loads(line) for path in sources for line in path.read_text().splitlines()]
keys = [(x['rate'],x['seed']) for x in records]
assert len(keys) == len(set(keys)) == 60
assert {x['rate'] for x in records} == {3.0,3.5,4.0}
assert all({x['seed'] for x in records if x['rate'] == rate} == set(range(226,246))
           for rate in (3.0,3.5,4.0))
(out/'runs.jsonl').write_text(''.join(json.dumps(x,allow_nan=False)+'\n'
                                      for x in sorted(records,key=lambda r:(r['rate'],r['seed']))))
(out/'metadata.json').write_text(json.dumps({'derived_from':
    [str(p.relative_to(ROOT)) for p in sources],
    'same_seeds_at_each_rate':list(range(226,246)),
    'note':'Raw stdout/stderr and run metadata remain in the source directories.'},indent=2))
print(out)

"""exp-008: sweep config overrides over a base config; one build per override (exact pass off unless set).

Usage: python -I -B sweep.py <base_config.json> <overrides.json> <out.jsonl>
overrides.json: list of dicts merged into the base config.
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

if __name__ == '__main__':
    from invsqrt import generate
    base = json.load(open(sys.argv[1]))
    overrides = json.load(open(sys.argv[2]))
    work = str(REPO / 'experiments' / 'exp-008' / 'out' / 'work')
    with open(sys.argv[3], 'a', encoding='utf-8') as f:
        for ov in overrides:
            cfg = dict(base, **ov)
            try:
                res = generate.run(cfg, work, None, log=lambda *a: None, nbatch=4)
                row = {'ov': ov, 'model': res['model'], 'final': res.get('final'), 'raw_peak': res.get('raw', {}).get('peak')}
            except Exception as e:
                row = {'ov': ov, 'error': repr(e)}
            print(json.dumps(row), flush=True)
            f.write(json.dumps(row) + '\n')

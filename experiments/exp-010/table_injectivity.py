"""exp-010: is the port's 8-bit address recoverable from its lookup words? (distinct values over the 256 addresses)

Usage: python -I -B experiments/exp-010/table_injectivity.py <config.json> <work_dir>
Reads only our own exp-008 table cache (tab_*.npy); no pickle is loaded.
"""
import json, pathlib, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))
if __name__ == '__main__':
    import numpy as np
    from invsqrt import calib as Ca, generate as G
    cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    prm = G.params_from(cfg)
    tables = np.load(pathlib.Path(sys.argv[2]) / f'tab_{G.tag(prm, cfg)}.npy')
    lay = Ca.layout(tables, prm, cfg['LB'], cfg['S'])
    words = {'u(L init)': lay.u[:256], 'H': lay.H[:256], 'C1(T init)': tables[:256, 1], 'C2': tables[:256, 2]}
    out = {k: int(len(np.unique(np.asarray(v, dtype=np.int64)))) for k, v in words.items()}
    out['(C1,C2)'] = int(len({(int(a), int(b)) for a, b in zip(tables[:256, 1], tables[:256, 2])}))
    out['(u,H,C1,C2)'] = int(len({(int(a), int(b), int(c), int(d)) for a, b, c, d in zip(lay.u[:256], lay.H[:256], tables[:256, 1], tables[:256, 2])}))
    for p in (0, 1):
        sl = slice(128 * p, 128 * p + 128)
        out[f'C1 distinct, p={p} (128 addresses)'] = int(len(np.unique(tables[sl, 1])))
        out[f'u distinct, p={p}'] = int(len(np.unique(lay.u[sl])))
    print(json.dumps(out, indent=1))

"""End-to-end invsqrt generator driven by a JSON config.

fit tables (cached) -> H/L layout -> LP angle calibration (cached) -> exact all-x model
check -> build -> kickmix sample check against the model -> exact-domain post-pass ->
kickmix sample check again -> write .kmb and a report.

Config keys (all required unless noted):
  F0, FT, F2, G0           model precisions (model.Params)
  dropA, dropB             rows left out of step A / B (lists)
  LB, S                    H/L split: L width and H shift
  drop                     lowest L phase positions given no rotation
  wins                     nested-window plan string, e.g. "17:11,10;15:9,8"
  kbig, qcap               (optional) in-place adder prefixes for step B
  exact_pass               (optional, default true) run exact.py on the built circuit
  rad1, rad2               (optional) fit neighbourhood radii (default 6, 3)

The pipeline structure follows marsyas's Apache-2.0 run.py/hsplit.py main (see package
docstring); this file is ours.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import pickle
import sys
import time

import numpy as np

from . import build as Bd
from . import calib as Ca
from . import check as Ck
from . import exact as Ex
from . import fit as Fm
from . import model as M


def params_from(cfg) -> M.Params:
    nr = 14
    return M.Params(F0=cfg['F0'], FT=cfg['FT'], F2=cfg['F2'], G0=cfg['G0'], tcap=cfg.get('tcap', True),
                    rowsA=tuple(i for i in range(nr) if i not in cfg.get('dropA', [])),
                    rowsB=tuple(i for i in range(nr) if i not in cfg.get('dropB', [])))


def tag(prm: M.Params, cfg) -> str:
    dA = ''.join(f'{i:x}' for i in range(14) if i not in prm.rowsA)
    dB = ''.join(f'{i:x}' for i in range(14) if i not in prm.rowsB)
    return f"{prm.F0}_{prm.FT}_{prm.F2}_{prm.G0}_sd{'_tc' if prm.tcap else ''}_a{dA}_b{dB}_r{cfg.get('rad1', 6)}{cfg.get('rad2', 3)}"


def kmb_sha256(circ) -> str:
    buf = io.BytesIO()
    circ.to_file(buf, format='kmb')
    return hashlib.sha256(buf.getvalue()).hexdigest()


def run(cfg: dict, work: str, out_path: str | None = None, workers: int = 8, nbatch: int = 8, log=print):
    os.makedirs(work, exist_ok=True)
    t0 = time.time()
    prm = params_from(cfg)
    tg = tag(prm, cfg)
    ref = M.reference(os.path.join(work, 'ref.npz'))
    tpath = os.path.join(work, f'tab_{tg}.npy')
    if os.path.exists(tpath):
        tables = np.load(tpath)
    else:
        tables, _ = Fm.fit_all(prm, rad1=cfg.get('rad1', 6), rad2=cfg.get('rad2', 3), workers=workers)
        np.save(tpath, tables)
    log(f'tables {time.time() - t0:.1f}s')
    lay = Ca.layout(tables, prm, cfg['LB'], cfg['S'])
    if lay is None:
        raise ValueError('layout infeasible')
    drop = cfg.get('drop', 1)
    cpath = os.path.join(work, f'hang_{tg}_L{lay.LB}_S{lay.S}_d{drop}.pkl')
    if os.path.exists(cpath):
        with open(cpath, 'rb') as f:
            angs, worst, margin, nrot = pickle.load(f)
    else:
        res = Ca.calibrate_multi(tables, prm, lay, ref, drop=drop)
        if res is None:
            raise ValueError('calibration LP failed')
        angs, worst, margin, nrot = res
        with open(cpath, 'wb') as f:
            pickle.dump((angs, worst, margin, nrot), f)
    log(f'calibration worst {worst} margin {margin} nrot {nrot} ({time.time() - t0:.1f}s)')
    model = {'worst': worst, 'min_margin': int(margin), 'nrot_model': nrot, 'pass': bool(worst < 1 and margin > 0)}
    if not model['pass']:
        return {'model': model, 'cfg': cfg}
    a, p, xn, bounds = Fm.domains()
    W = M.window_ranges1(tables, prm, xn, p)
    o = Bd.Opts(WA=W['A'], gA=1, mdel=True)
    o.wins = Bd.parse_plan(cfg['wins']) if cfg.get('wins') else None
    o.kbig = int(cfg.get('kbig', 0))
    o.qcap = cfg.get('qcap')
    if o.wins:
        o.wcb = cfg.get('wcb') or Bd.choose_cbits(tables, prm, lay, o.wins)
        if o.wcb is None:
            raise ValueError('no window counter bits fit')
    log(f'windows A {W}, wcb {o.wcb}')
    circ, peak = Bd.build_hsplit(tables, prm, o, lay, angs)
    phase_fn = lambda xs: Ca.phases_multi(Ca.regs(tables, prm, lay, xs), angs)
    rep_raw = Ck.report(circ, phase_fn, margin, nbatch=nbatch)
    rep_raw['peak'] = peak
    rep_raw['sha256'] = kmb_sha256(circ)
    log(f'raw build {rep_raw} ({time.time() - t0:.1f}s)')
    final = circ
    exact_stats = None
    if cfg.get('exact_pass', True):
        final, exact_stats = Ex.run(circ, work)
        log(f'exact pass {exact_stats} ({time.time() - t0:.1f}s)')
    rep = Ck.report(final, phase_fn, margin, nbatch=nbatch)
    rep['sha256'] = kmb_sha256(final)
    log(f'final {rep} ({time.time() - t0:.1f}s)')
    if out_path:
        final.to_file(out_path, format='kmb')
    return {'cfg': cfg, 'tag': tg, 'model': model, 'windows': {'A': W, 'wcb': o.wcb}, 'raw': rep_raw,
            'exact_stats': exact_stats, 'final': rep, 'seconds': round(time.time() - t0, 1),
            'tables_sha256': hashlib.sha256(tables.tobytes()).hexdigest(),
            'angles': [[int(v) for v in ang] for ang in angs]}


def main(argv):
    cfg_path, work, out_path = argv[0], argv[1], argv[2]
    with open(cfg_path, encoding='utf-8') as f:
        cfg = json.load(f)
    res = run(cfg, work, out_path)
    rep_path = os.path.splitext(out_path)[0] + '.report.json'
    with open(rep_path, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'angles'}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])

"""Fit integer coefficient tables against the exact truncated arithmetic of model.py.

Per segment: continuous minimax (LP) quadratic in the centred delta, then an integer
neighbourhood search over (C1, C2) with the best C0 for each, scored by the max
relative error of Y over exactly the (p, x_n) inputs that occur.

Ported from marsyas's Apache-2.0 notebook (see package docstring). change: the worker
pool uses the 'spawn' start method (Windows) and receives each segment's inputs
explicitly instead of through a module global set before a fork; only the G0 > 0 / sd
paths the 13.94x build uses are kept.
"""
from __future__ import annotations

import concurrent.futures as cf
import multiprocessing as mp

import numpy as np
from scipy.optimize import linprog

from . import model as M

_D = None


def domains():
    """Distinct (p, x_n) over all legal x, sorted by segment address, and segment bounds."""
    global _D
    if _D is not None:
        return _D
    xs = np.arange(1, M.MAX_X + 1, dtype=np.int64)
    t, xn, p, s = M.decompose(xs)
    key = np.unique((p << 22) | xn)
    p = key >> 22
    xn = key & ((1 << 22) - 1)
    a = (p << 7) | ((xn >> 14) & 127)
    order = np.argsort(a, kind='stable')
    a, p, xn = a[order], p[order], xn[order]
    bounds = np.searchsorted(a, np.arange(257))
    _D = (a, p, xn, bounds)
    return _D


def ytrue(p, xn):
    return np.where(p == 1, 1.0, 2 ** -0.5) * 2 ** 10.5 / np.sqrt(xn.astype(np.float64))


def lp_fit(dc, y):
    """Minimax relative fit y ~ c0 - c1 dc + c2 dc^2 on 600 sample points."""
    idx = np.unique(np.r_[np.linspace(0, len(dc) - 1, 600).astype(int)])
    d, yy = dc[idx], y[idx]
    A1 = np.c_[np.ones_like(d), -d, d * d, -yy]
    A2 = np.c_[-np.ones_like(d), d, -d * d, -yy]
    A = np.r_[A1, A2]
    bvec = np.r_[yy, -yy]
    r = linprog([0, 0, 0, 1], A_ub=A, b_ub=bvec, bounds=[(None, None)] * 3 + [(0, None)], method='highs')
    return r.x[:3]


def best_C0(R, ytgt, w, top):
    d = R - ytgt
    c = -0.5 * (d.max() + d.min())
    best = None
    cands = [np.floor(c) - 1, np.floor(c), np.floor(c) + 1, np.floor(c) + 2]
    hi = top - 1 - R.max()
    cands = [min(v, hi) for v in cands]
    for C0 in cands:
        sc = np.max(np.abs(C0 + R - ytgt) * w)
        if best is None or sc < best[0]:
            best = (sc, int(C0))
    return best


def best_C0_g(R, ytgt, w, G0, top):
    d = R - ytgt
    c = int(np.floor(-0.5 * (d.max() + d.min()) + (1 << G0) / 2))
    best = None
    hi = int(top - 1 - R.max())
    cands = sorted(set(min(v, hi) for v in range(c - (1 << G0), c + (1 << G0) + 1)))
    for C0 in cands:
        e = (((C0 + R) >> G0) << G0) - ytgt
        sc = np.max(np.abs(e) * w)
        if best is None or sc < best[0]:
            best = (sc, C0)
    return best


def fit_segment(p, xn, prm: M.Params, rad1=6, rad2=3):
    b = xn & 0x3FFF
    dc = (b - 8191.5) * 2.0 ** -21
    y = ytrue(p, xn)
    c0, c1, c2 = lp_fit(dc, y)
    ytgt = (y - 0.5) * 2 ** prm.F0
    w = 1.0 / (y * 2 ** prm.F0) * 2 ** 24   # error / tolerance (approx)
    top = 1 << (prm.F0 - 1)
    zeros = np.zeros(len(b), np.int64)
    cache = {}

    def ev(C1, C2):
        key = (C1, C2)
        if key in cache:
            return cache[key]
        T = M.eval_T(zeros + C1, zeros + C2, b, prm)
        if T.min() < 0 or T.max() >= (1 << prm.nT) or C1 >= (1 << prm.nT):
            r = (np.inf, 0)
        else:
            R = M.eval_Y(zeros, T, b, prm)
            r = best_C0(R, ytgt, w, top) if prm.G0 == 0 else best_C0_g(R, ytgt, w, prm.G0, top)
        cache[key] = r
        return r

    k1 = int(round(c1 * 2 ** prm.FT))
    k2 = int(round(c2 * 2 ** prm.F2))
    best = None
    for C2 in range(k2 - rad2, k2 + rad2 + 1):
        for C1 in range(k1 - rad1, k1 + rad1 + 1):
            sc, C0 = ev(C1, C2)
            if best is None or sc < best[0]:
                best = (sc, C0, C1, C2)
    improved = True
    while improved:
        improved = False
        _, _, C1b, C2b = best
        for d2 in (-1, 0, 1):
            for d1 in range(-3, 4):
                sc, C0 = ev(C1b + d1, C2b + d2)
                if sc < best[0] - 1e-12:
                    best = (sc, C0, C1b + d1, C2b + d2)
                    improved = True
    return best


def _work(args):
    seg, p, xn, prm, rad1, rad2 = args
    if len(p) == 0:
        return seg, (0.0, 0, 0, 0)
    return seg, fit_segment(p, xn, prm, rad1, rad2)


def fit_all(prm: M.Params, rad1=6, rad2=3, workers=8):
    """(256, 3) int64 table [C0, C1, C2] per segment address, and the worst approx score."""
    a, p, xn, bounds = domains()
    tasks = [(s, p[bounds[s]:bounds[s + 1]], xn[bounds[s]:bounds[s + 1]], prm, rad1, rad2) for s in range(256)]
    tables = np.zeros((256, 3), dtype=np.int64)
    worst = 0.0
    if workers <= 1:
        results = map(_work, tasks)
    else:
        ex = cf.ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context('spawn'))
        results = ex.map(_work, tasks)
    for seg, (sc, C0, C1, C2) in results:
        tables[seg] = (C0, C1, C2)
        worst = max(worst, sc)
    if workers > 1:
        ex.shutdown()
    return tables, worst

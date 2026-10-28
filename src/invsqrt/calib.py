"""H/L output split layout and LP calibration of the rotation angles.

Y' = H 2^S + L with H a pure table word and L = u + D (D = the Horner correction) kept
in [0, 2^LB). Each register is phased through a shift register (positions j weigh
2^(j - R0 - 10) turns exactly); the non-Clifford, non-T angles are re-optimised by a
cutting-plane LP to maximise the minimum margin tol(x) - |error(x)| over all legal x.
Angles are integers in units of 2^-64 turns, so the final check is exact.

Ported from marsyas's Apache-2.0 notebook (hsplit.py and calib.py there; see the package
docstring; the LP calibration idea is credited there to lightningv08, the H/L split to
anazemcev). change: the reference arrays are passed in instead of read from a module
cache; dead code paths are dropped.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from . import fit as Fm
from . import model as M


class Layout:
    pass


def layout(tables, prm, LB, S):
    a, p, xn, bounds = Fm.domains()
    b = xn & 0x3FFF
    C0, C1, C2 = tables[a, 0], tables[a, 1], tables[a, 2]
    T = M.eval_T(C1, C2, b, prm)
    D = M.eval_Y(C0, T, b, prm) - C0
    dmin = np.minimum.reduceat(D, bounds[:-1])
    dmax = np.maximum.reduceat(D, bounds[:-1])
    u = np.zeros(256, np.int64)
    H = np.zeros(256, np.int64)
    for k in range(256):
        c0 = int(tables[k, 0])
        base = c0 % (1 << S)
        j = 0
        while base + j * (1 << S) + dmin[k] < 0:
            j += 1
        uk = base + j * (1 << S)
        if uk + dmax[k] >= (1 << LB) or c0 - uk < 0:
            return None
        u[k] = uk
        H[k] = (c0 - uk) >> S
    lay = Layout()
    lay.LB, lay.S, lay.u, lay.H = LB, S, u, H
    lay.nHf = prm.F0 - 1 - S          # H register span up to the constant bit
    lay.nH = max(int(H.max()).bit_length(), 1)
    assert lay.nH <= lay.nHf
    return lay


def phases(V, ang):
    acc = np.zeros(len(V), dtype=np.uint64)
    for j, a in enumerate(ang):
        a = int(a) & M.MASK64
        if a == 0:
            continue
        acc += ((V >> j) & 1).astype(np.uint64) * np.uint64(a)
    return acc


def regs(tables, prm, lay, xs):
    """[(shifted register value, offset, top index)] for the H and L phase registers."""
    t, xn, p, s = M.decompose(xs)
    a = (p << 7) | ((xn >> 14) & 127)
    b = xn & 0x3FFF
    C0, C1, C2 = tables[a, 0], tables[a, 1], tables[a, 2]
    T = M.eval_T(C1, C2, b, prm)
    Y = M.eval_Y(C0, T, b, prm)
    L = lay.u[a] + (Y - C0)
    VH = (lay.H[a] + (1 << lay.nHf)) << s
    VL = (L >> prm.G0) << s
    offH = lay.S - prm.G0
    return [(VH << offH, offH, lay.nHf), (VL, 0, lay.LB - prm.G0 - 1)]


def phases_multi(R, angs):
    acc = np.zeros(len(R[0][0]), dtype=np.uint64)
    for (V, off, h0), ang in zip(R, angs):
        acc += phases(V, ang)
    return acc


def exact_angles(prm):
    R0 = prm.F0 - prm.G0
    return [int(1 << (64 + j - R0 - 10)) for j in range(R0 + 10)]


def spans(prm, R):
    R0 = prm.F0 - prm.G0
    return [[pp for pp in range(off, off + h0 + 11) if pp <= R0 + 6] for V, off, h0 in R]


def check_multi(tables, prm, lay, angs, ref):
    target, tol = ref
    xs = np.arange(1, M.MAX_X + 1, dtype=np.int64)
    R = regs(tables, prm, lay, xs)
    ph = phases_multi(R, angs)
    err = (ph - target).view(np.int64)
    used = np.abs(err).astype(np.float64)
    return float((used / tol).max()), float((tol.astype(np.float64) - used).min()), err, tol, R


def calibrate_multi(tables, prm, lay, ref, drop=1, iters=12, verbose=False):
    R0 = prm.F0 - prm.G0
    ex = exact_angles(prm)
    xs = np.arange(1, M.MAX_X + 1, dtype=np.int64)
    R = regs(tables, prm, lay, xs)
    sp = spans(prm, R)
    angs = [list(ex) for _ in R]
    var = []
    for r, (V, off, h0) in enumerate(R):
        for pp in range(R0 + 10):
            if not (off <= pp <= off + h0 + 10):
                angs[r][pp] = 0
        pos = sp[r]
        if r == 1:   # drop the lowest L positions
            for pp in pos[:drop]:
                angs[r][pp] = 0
            pos = pos[drop:]
        var += [(r, pp) for pp in pos]
    worst, margin, err, tol, _ = check_multi(tables, prm, lay, angs, ref)
    if verbose:
        print('start', worst, margin, flush=True)
    bits = np.stack([((R[r][0] >> pp) & 1).astype(np.float32) for r, pp in var], axis=1)
    tolf = tol.astype(np.float64)
    errf = err.astype(np.float64)
    act = np.argsort(tolf - np.abs(errf))[:20000]
    best = None
    S_ = 2.0 ** 20
    for it in range(iters):
        A = bits[act].astype(np.float64)
        e = errf[act] / S_
        tl = tolf[act] / S_
        n = len(var)
        c = np.zeros(n + 1)
        c[-1] = -1
        one = np.ones_like(tl)
        Aub = np.r_[np.c_[A, one], np.c_[-A, one]]
        bub = np.r_[tl - e, tl + e]
        res = linprog(c, A_ub=Aub, b_ub=bub, bounds=[(-2**20, 2**20)] * n + [(None, None)], method='highs')
        if res.x is None:
            break
        d = np.round(res.x[:n] * S_).astype(np.int64)
        tot = errf + bits @ d.astype(np.float64)
        slack = tolf - np.abs(tot)
        w = 2.0 if slack.min() <= 0 else 1.0 / slack.min()
        if verbose:
            print(f'it {it} minslack {slack.min():.4g}', flush=True)
        if best is None or w < best[0]:
            best = (w, d.copy())
        act2 = np.union1d(act, np.argsort(slack)[:5000])
        if len(act2) == len(act):
            break
        act = act2
    if best is None:
        return None
    d = best[1]
    for k, (r, pp) in enumerate(var):
        angs[r][pp] = int(angs[r][pp]) + int(d[k])
    worst, margin, _, _, _ = check_multi(tables, prm, lay, angs, ref)
    return angs, worst, margin, len(var)

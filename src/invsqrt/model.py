"""Exact integer model of the invsqrt circuit (single-bit normalization, centred quadratic).

Ported from marsyas's Apache-2.0 notebook (see package docstring). change: only the
signed-digit ("sd") row mode the 13.94x build uses is kept; the Booth and plain-row
modes are dropped. The reference cache path is a parameter.

Notation
  x in [1, MAX_X], 22-bit. t = 21 - floor(log2 x) (leading zeros), x_n = x << t in [2^21, 2^22).
  t = 16 f16 + 8 f8 + 4 f4 + 2 f2 + f1,  s = t >> 1,  p = f1.
  1/sqrt(x) = 2^(s-10) * Y,  Y = (p ? 1 : 2^-1/2) / sqrt(x_n / 2^21)  in (1/2, 1].
  Segment address a = (p << 7) | ((x_n >> 14) & 127); delta_int b = x_n & 0x3FFF (14 bits).
  Signed digits: d' = sum_i (2 b_i - 1) 2^(i-22), rows rounded.

Arithmetic (all integer):
  T  = C1 - sum_{i in rowsA} (2b_i - 1) rd(C2, eA_i + 1)        (step A)
  Y' = C0 - sum_{i in rowsB} (2b_i - 1) rd(T,  eB_i + 1)  mod 2^(F0-1)   (step B)
  eA_i = 21 + F2 - FT - i, eB_i = 21 + FT - F0 - i.
  Phase (turns) = 2^(s-10) * (Y' 2^-F0 + 1/2).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass

import numpy as np

MAX_X = 3133452
WIDTH = 22
MASK64 = (1 << 64) - 1


def shr(v, e):
    """v * 2^-e floored (e may be negative)."""
    return (v >> e) if e >= 0 else (v << -e)


@dataclass(frozen=True)
class Params:
    F0: int = 28          # Y LSB weight 2^-F0; register holds Y - 1/2 in F0-1 bits
    FT: int = 19          # T LSB 2^-FT
    F2: int = 8           # C2 LSB 2^-F2; register F2-1 bits
    G0: int = 1           # unrotated guard LSBs of Y' (phase uses Y' >> G0)
    rowsA: tuple = tuple(range(14))
    rowsB: tuple = tuple(range(14))
    tcap: bool = True     # T < 2^(FT-1): T register FT-1 bits

    @property
    def nT(self):
        return self.FT - 1 if self.tcap else self.FT

    def eA(self, i):
        return 21 + self.F2 - self.FT - i

    def eB(self, i):
        return 21 + self.FT - self.F0 - i


def decompose(xs):
    xs = np.asarray(xs, dtype=np.int64)
    lg = np.floor(np.log2(xs.astype(np.float64))).astype(np.int64)
    lg = np.where((1 << (lg + 1)) <= xs, lg + 1, lg)
    lg = np.where((1 << lg) > xs, lg - 1, lg)
    t = 21 - lg
    xn = xs << t
    p = t & 1
    s = t >> 1
    return t, xn, p, s


def reference(cache_path=None):
    """Verifier target (uint64 units of 2^-64 turns) and tolerance for every x, as in
    verify_submission_invsqrt.reference_values with beta = 1, precision_bits = 24."""
    if cache_path and os.path.exists(cache_path):
        with np.load(cache_path) as z:
            return z['target'], z['tol']
    rs = [math.isqrt((1 << 130) // x) for x in range(1, MAX_X + 1)]
    target = np.array([((r + 1) >> 1) & MASK64 for r in rs], dtype=np.uint64)
    tol = np.array([min(r >> 25, 1 << 63) for r in rs], dtype=np.uint64)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        np.savez(cache_path, target=target, tol=tol)
    return target, tol


def rd(v, s):
    """v * 2^-s rounded half up (s <= 0: exact left shift)."""
    if s <= 0:
        return v << (-s)
    return (v >> s) + ((v >> (s - 1)) & 1)


def sd_apply(acc, op, b, rows, e_of):
    for i in rows:
        sig = 2 * ((b >> i) & 1) - 1
        acc = acc - sig * rd(op, e_of(i) + 1)
    return acc


def eval_T(C1, C2, b, prm: Params):
    return sd_apply(C1.copy(), C2, b, prm.rowsA, prm.eA)


def eval_Y(C0, T, b, prm: Params):
    return sd_apply(C0.copy(), T, b, prm.rowsB, prm.eB)


def rotation_cost(n_rot, min_margin_units):
    """T count of n_rot rotations at the verifier's eps for a given minimum margin."""
    eps = math.pi * min_margin_units / 2**64 / n_rot
    return n_rot * (0.56 * math.log2(1 / eps) + 5.3)


def window_ranges1(tables, prm: Params, xn, p):
    """1-guard offset scheme: minimal W with (acc mod 2^(W+1)) - 2^W + d in [-2^(W+1), 2^(W+1))."""
    a = (p << 7) | ((xn >> 14) & 127)
    b = xn & 0x3FFF
    C0, C1, C2 = tables[a, 0], tables[a, 1], tables[a, 2]
    T = eval_T(C1, C2, b, prm)
    Y = eval_Y(C0, T, b, prm)
    out = {}
    for name, acc, d, n in (('A', C1, T - C1, prm.nT), ('B', C0, Y - C0, prm.F0 - 1)):
        W = None
        for w in range(1, n - 1):
            r = (acc & ((1 << (w + 1)) - 1)) - (1 << w) + d
            if r.min() >= -(1 << (w + 1)) and r.max() < (1 << (w + 1)):
                W = w
                break
        out[name] = W
    return out

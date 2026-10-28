"""Exact-domain post-pass: track every qubit's classical value on all 3,133,452 legal inputs;
Toffoli-like gates whose controls are provably constant or equal/opposite become
CNOT/CZ/SWAP or are deleted.

Ported from marsyas's Apache-2.0 notebook (exact.py there; idea credited to Artem /
anazemcev; see the package docstring). change: works on a kmx text file in a caller-given
directory instead of a mktemp path, and returns the statistics.

Soundness: value ops (X, CX, CCX, SWAP, CSWAP, R) under an inline classical condition are
refused; a PUSH_CONDITION block must be value-neutral (checked), so tracking it as if it
always ran gives the right values after the block.
"""
from __future__ import annotations

import os
import re

import numpy as np
import kickmix as km

from . import model as M

VALUE_OPS = {'X', 'CX', 'CCX', 'SWAP', 'CSWAP', 'R'}


def run(circ: km.Circuit, work_dir: str):
    os.makedirs(work_dir, exist_ok=True)
    tmp = os.path.join(work_dir, '_exact_in.kmx')
    circ.to_file(tmp, format='kmx')
    with open(tmp, encoding='utf-8') as f:
        lines = f.read().split('\n')
    os.remove(tmp)
    xq = [int(re.findall(r'\d+', repr(q))[-1]) for q in circ.register_data['x']]
    exp = []
    for line in lines:
        tok = line.split()
        if tok and tok[0] in ('CCX', 'CCZ', 'CSWAP'):
            cond = ''
            if 'if' in tok:
                k = tok.index('if')
                cond = ' ' + ' '.join(tok[k:])
                tok = tok[:k]
            qs = tok[1:]
            if len(qs) > 3:
                for i in range(0, len(qs), 3):
                    exp.append(f'{tok[0]} ' + ' '.join(qs[i:i + 3]) + cond)
                continue
        exp.append(line)
    lines = exp
    N = M.MAX_X
    xs = np.arange(1, N + 1, dtype=np.int64)
    val = {}

    def V(q):
        if q not in val:
            val[q] = np.zeros(N, dtype=bool)
        return val[q]

    for i, q in enumerate(xq):
        val[q] = ((xs >> i) & 1).astype(bool)
    out = []
    stats = {'ccx_del': 0, 'ccx_cx': 0, 'ccz_del': 0, 'ccz_cz': 0, 'cswap_del': 0, 'cswap_swap': 0}
    snaps = []

    def const(v):
        if not v.any():
            return 0
        if v.all():
            return 1
        return None

    for line in lines:
        tok = line.split()
        if not tok:
            out.append(line)
            continue
        op = tok[0]
        cond = ''
        if 'if' in tok:
            k = tok.index('if')
            cond = ' ' + ' '.join(tok[k:])
            tok = tok[:k]
        qs = [int(t[1:]) for t in tok[1:] if t.startswith('q')]
        if op == 'PUSH_CONDITION':
            snaps.append({})
            out.append(line)
            continue
        if op == 'POP_CONDITION':
            for q, v0 in snaps.pop().items():
                if not np.array_equal(v0, V(q)):
                    raise RuntimeError('conditional block is not value-neutral')
            out.append(line)
            continue
        if op in VALUE_OPS or op == 'HMR':
            if cond:
                raise RuntimeError('conditional value op: ' + line)
            if snaps:
                for q in qs:
                    for d in snaps:
                        if q not in d:
                            d[q] = V(q).copy()
        if op == 'CCX':
            a, b_, t = qs
            va, vb = V(a), V(b_)
            ca, cb = const(va), const(vb)
            if ca == 0 or cb == 0 or np.array_equal(va, ~vb):
                stats['ccx_del'] += 1
            elif ca == 1:
                out.append(f'CX q{b_} q{t}{cond}')
                stats['ccx_cx'] += 1
                V(t)[:] ^= vb
            elif cb == 1 or np.array_equal(va, vb):
                out.append(f'CX q{a} q{t}{cond}')
                stats['ccx_cx'] += 1
                V(t)[:] ^= va
            else:
                out.append(line)
                V(t)[:] ^= va & vb
            continue
        if op == 'CCZ':
            a, b_, t = qs
            vs = [V(a), V(b_), V(t)]
            cs = [const(v) for v in vs]
            if 0 in cs:
                stats['ccz_del'] += 1
                continue
            done = False
            for i in range(3):
                for j in range(i + 1, 3):
                    if np.array_equal(vs[i], ~vs[j]):
                        stats['ccz_del'] += 1
                        done = True
                        break
                if done:
                    break
            if done:
                continue
            for i in range(3):
                if cs[i] == 1:
                    o = [qs[k] for k in range(3) if k != i]
                    out.append(f'CZ q{o[0]} q{o[1]}{cond}')
                    stats['ccz_cz'] += 1
                    done = True
                    break
            if done:
                continue
            for i in range(3):
                for j in range(i + 1, 3):
                    if np.array_equal(vs[i], vs[j]) and not done:
                        k = 3 - i - j
                        out.append(f'CZ q{qs[i]} q{qs[k]}{cond}')
                        stats['ccz_cz'] += 1
                        done = True
            if not done:
                out.append(line)
            continue
        if op == 'CSWAP':
            cq, a, b_ = qs
            vc, va, vb = V(cq), V(a), V(b_)
            cc = const(vc)
            if cc == 0 or np.array_equal(va, vb):
                stats['cswap_del'] += 1
                continue
            if cc == 1:
                out.append(f'SWAP q{a} q{b_}')
                stats['cswap_swap'] += 1
                val[a], val[b_] = vb.copy(), va.copy()
                continue
            out.append(line)
            m = vc & (va ^ vb)
            va ^= m
            vb ^= m
            continue
        out.append(line)
        if op == 'X':
            for q in qs:
                V(q)[:] ^= True
        elif op == 'CX':
            for a, t in zip(qs[0::2], qs[1::2]):
                V(t)[:] ^= V(a)
        elif op == 'SWAP':
            for a, t in zip(qs[0::2], qs[1::2]):
                val[a], val[t] = V(t).copy(), V(a).copy()
        elif op in ('R', 'HMR'):
            for q in qs:
                V(q)[:] = False
    c2 = km.Circuit('\n'.join(out))
    return c2, stats

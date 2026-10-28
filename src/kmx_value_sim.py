"""Lane-parallel classical (value-only) simulator for kickmix .kmx text circuits.

Every lane is one basis input. Qubit and classical-bit values are tracked as numpy
bool arrays over the lanes; phase instructions (Z, CZ, CCZ, NEG, Z_POW) are ignored.
`HMR q b` writes an independent uniform random outcome per lane into b and resets q.
`PUSH_CONDITION if b` / `POP_CONDITION` and inline `... if b` restrict value updates
to the lanes where the condition bits are 1.

What it reports (used to read the structure of a circuit, ours or a downloaded one,
without executing any downloaded code):
  * per instruction index, the number of "live" qubits: qubits that are nonzero on at
    least one lane (an upper bound on the number of qubits that must be allocated);
  * executed Toffoli-like gates (CCX, CCZ, CSWAP), with conditioned gates counted on the
    fraction of lanes where their condition holds (the verifier's per-shot mean);
  * Toffolis between Z_POW markers or any caller-given line ranges.

Usage:
    python -I -B src/kmx_value_sim.py circuit.kmx out.json [--step 1] [--lanes all|N]
"""

from __future__ import annotations

import json
import re
import sys

import numpy as np

MAX_X = 3133452
TOFFOLI_LIKE = ('CCX', 'CCZ', 'CSWAP')
PHASE_ONLY = {'Z', 'CZ', 'CCZ', 'NEG', 'Z_POW', 'S', 'T', 'INFO_TAG'}
_TOK = re.compile(r'([qb])(\d+)')


def parse(path):
    """Yield (op, [('q'|'b', idx), ...], cond_bit or None) per instruction line."""
    with open(path, encoding='utf-8') as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            op = t[0]
            cond = None
            if 'if' in t:
                k = t.index('if')
                cond = int(t[k + 1][1:])
                t = t[:k]
            ops = []
            for s in t[1:]:
                m = _TOK.fullmatch(s)
                if m:
                    ops.append((m.group(1), int(m.group(2))))
            yield op, ops, cond, line.rstrip('\n')


def simulate(path, xs, seed=0, record=True):
    rng = np.random.default_rng(seed)
    n = len(xs)
    Q: dict[int, np.ndarray] = {}
    Bt: dict[int, np.ndarray] = {}
    regs: dict[str, list[int]] = {}
    pending: dict[str, list[int]] = {}
    zeros = np.zeros(n, dtype=bool)

    def q(i):
        v = Q.get(i)
        if v is None:
            v = Q[i] = np.zeros(n, dtype=bool)
        return v

    def bit(i):
        v = Bt.get(i)
        if v is None:
            v = Bt[i] = np.zeros(n, dtype=bool)
        return v

    cond_stack: list[np.ndarray] = []
    live_nonzero: set[int] = set()
    profile = []          # (line_no, live_count) at Toffoli-like gates and Z_POW
    tof_exec = 0.0
    tof_static = 0
    tof_lines = []        # (line_no, op, executed fraction)
    zpow_lines = []
    peak = (0, -1)
    x_loaded = False
    lineno = 0
    for op, ops, cond, raw in parse(path):
        lineno += 1
        if op == 'APPEND_TO_REGISTER':
            pending.setdefault(raw.split()[2], []).append(ops[0][1])
            continue
        if op == 'REGISTER':
            name = raw.split('"')[1]
            rid = raw.split()[1]
            regs[name] = pending.pop(rid, [])
            if name == 'x' and not x_loaded:
                for k, qi in enumerate(regs['x']):
                    Q[qi] = ((xs >> k) & 1).astype(bool)
                    if Q[qi].any():
                        live_nonzero.add(qi)
                x_loaded = True
            continue
        mask = None
        if cond_stack:
            mask = cond_stack[-1]
        if cond is not None:
            c = bit(cond)
            mask = c if mask is None else (mask & c)
        if op == 'PUSH_CONDITION':
            c = bit(cond)
            cond_stack.append(c.copy() if not cond_stack else (cond_stack[-1] & c))
            continue
        if op == 'POP_CONDITION':
            cond_stack.pop()
            continue
        frac = 1.0 if mask is None else float(mask.mean())
        if op in TOFFOLI_LIKE:
            tof_static += 1
            tof_exec += frac
            if record:
                tof_lines.append((lineno, op, frac))
        if op == 'Z_POW':
            zpow_lines.append((lineno, raw.split()[1], raw.split()[2]))
        if op in PHASE_ONLY:
            pass
        elif op == 'X':
            a = q(ops[0][1])
            if mask is None:
                np.logical_not(a, out=a)
            else:
                a ^= mask
        elif op == 'CX':
            c, t = q(ops[0][1]), q(ops[1][1])
            t ^= c if mask is None else (c & mask)
        elif op == 'CCX':
            a, b_, t = q(ops[0][1]), q(ops[1][1]), q(ops[2][1])
            v = a & b_
            t ^= v if mask is None else (v & mask)
        elif op == 'SWAP':
            i, j = ops[0][1], ops[1][1]
            a, b_ = q(i), q(j)
            if mask is None:
                Q[i], Q[j] = b_, a
            else:
                d = (a ^ b_) & mask
                a ^= d
                b_ ^= d
        elif op == 'CSWAP':
            c, a, b_ = q(ops[0][1]), q(ops[1][1]), q(ops[2][1])
            d = (a ^ b_) & c
            if mask is not None:
                d &= mask
            a ^= d
            b_ ^= d
        elif op == 'R':
            a = q(ops[0][1])
            if mask is None:
                a[:] = False
            else:
                a &= ~mask
        elif op == 'HMR':
            qi, bi = ops[0][1], ops[1][1]
            r = rng.random(n) < 0.5
            a, bb = q(qi), bit(bi)
            if mask is None:
                a[:] = False
                bb[:] = r
            else:
                a &= ~mask
                bb[:] = np.where(mask, r, bb)
        elif op == 'BIT_STORE0':
            bb = bit(ops[0][1])
            if mask is None:
                bb[:] = False
            else:
                bb &= ~mask
        elif op == 'BIT_STORE1':
            bb = bit(ops[0][1])
            if mask is None:
                bb[:] = True
            else:
                bb |= mask
        elif op == 'BIT_INVERT':
            bb = bit(ops[0][1])
            if mask is None:
                np.logical_not(bb, out=bb)
            else:
                bb ^= mask
        else:
            raise ValueError(f'unhandled op {op!r} at line {lineno}: {raw}')
        if record and op not in PHASE_ONLY:
            # incremental liveness: only the qubits this instruction touched can change
            for kind, i in ops:
                if kind == 'q':
                    if Q[i].any():
                        live_nonzero.add(i)
                    else:
                        live_nonzero.discard(i)
            live = len(live_nonzero)
            if live > peak[0]:
                peak = (live, lineno)
        if record and (op in TOFFOLI_LIKE or op == 'Z_POW'):
            profile.append((lineno, len(live_nonzero)))
    restored = all(np.array_equal(Q[qi], ((xs >> k) & 1).astype(bool)) for k, qi in enumerate(regs.get('x', [])))
    xset = set(regs.get('x', []))
    dirty = sorted(i for i, v in Q.items() if i not in xset and v.any())
    return {
        'lanes': n,
        'toffoli_static': tof_static,
        'toffoli_executed_mean': tof_exec,
        'num_qubits_touched': len(Q),
        'x_restored': restored,
        'dirty_scratch': dirty[:20],
        'peak_live': peak,
        'profile': profile,
        'tof_lines': tof_lines,
        'zpow_lines': zpow_lines,
    }


def main(argv):
    path, out = argv[0], argv[1]
    lanes = 'all'
    for a in argv[2:]:
        if a.startswith('--lanes='):
            lanes = a.split('=', 1)[1]
    if lanes == 'all':
        xs = np.arange(1, MAX_X + 1, dtype=np.int64)
    else:
        rng = np.random.default_rng(1)
        xs = np.unique(np.r_[rng.integers(1, MAX_X + 1, int(lanes)), [1, 2, 3, MAX_X]]).astype(np.int64)
    res = simulate(path, xs)
    summary = {k: v for k, v in res.items() if k not in ('profile', 'tof_lines')}
    print(json.dumps(summary, indent=1)[:3000])
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f)


if __name__ == '__main__':
    main(sys.argv[1:])

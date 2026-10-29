"""exp-010: width ledger of a kickmix invsqrt .kmx circuit, read as text (no downloaded code runs).

Usage: python -I -B experiments/exp-010/kmx_ledger.py <circuit.kmx> <out.json> [--every=N]

--every=N adds a timeline: every N lines, the class histogram of the live qubits and the class of
each x-register qubit k (for a non-x/xn value also the class of value XOR xn bit k).
A Toffoli-like gate's width is max(live before, live after) the gate.

Value-only lane simulation (the src/kmx_value_sim.py semantics: X/CX/CCX/SWAP/CSWAP/R/HMR and
classical bit ops, with PUSH_CONDITION / inline `if` masks; phase ops ignored) over every
x in [1, 3,133,452], run twice side by side with independent HMR outcomes (lanes are
bit-packed, 2 x 3,133,456 lanes, the 4 pad lanes are x = 1). A qubit is "live" when it is
nonzero on some lane.

Segments are cut at the circuit's Z_POW groups (gaps > 500 lines): pre, phase group 1,
mid, phase group 2, post (for invsqrt: pre = normalize + lookup, G1 = H phase,
mid = steps A and B, G2 = L phase, post = uncompute). For each segment it records the
maximum live count, and at that maximum the class of every live qubit:
  const      same value on every lane
  random     differs between the two HMR draws
  x k        equal to bit k of the input x
  xn k       equal to bit k of the normalized xn = x << t (t = leading zeros, 22-bit word)
  flag       a function of t only
  table      a function of a = (p, top 7 bits of xn below the leading 1), p = t & 1, only
  table_t    a function of (t, top 7 bits) only
  arith_p    a function of (p, xn) only (as our L and T words are)
  arith      anything else (a function of x)
For each class it also reports m_p = the fewest top bits of xn that, with p, determine the
qubit, and m_t the same with t.

Phase temp analysis per Z_POW group: the temp is the group's most frequent Z_POW qubit;
the window runs from just after its last HMR/R before the group's first Z_POW to the
group's last Z_POW. Every qubit that feeds the temp in the window (CX source, CCX input,
CSWAP control or swap partner) is listed with its class at the window start, its register
(x or not), and whether it was live at the window start and stays live through the window
end (persistent) or not (phase-only).
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time

import numpy as np

MAX_X = 3133452
TOFF = ('CCX', 'CCZ', 'CSWAP')
PHASE_ONLY = {'Z', 'CZ', 'CCZ', 'NEG', 'Z_POW', 'S', 'T', 'INFO_TAG'}
VALUE_TARGET = {'X': [0], 'CX': [1], 'CCX': [2], 'SWAP': [0, 1], 'CSWAP': [1, 2], 'R': [0], 'HMR': [0]}
_TOK = re.compile(r'([qb])(\d+)')


def parse(path):
    out = []
    with open(path, encoding='utf-8') as f:
        for raw in f:
            t = raw.split()
            if not t:
                out.append(('', [], None, ''))
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
            out.append((op, ops, cond, raw.rstrip('\n')))
    return out


class Keys:
    """Dense group ids for the classifier keys over x = 1..MAX_X."""

    def __init__(self):
        xs = np.arange(1, MAX_X + 1, dtype=np.int64)
        lg = np.floor(np.log2(xs.astype(np.float64))).astype(np.int64)
        lg = np.where((1 << (lg + 1)) <= xs, lg + 1, lg)
        lg = np.where((1 << lg) > xs, lg - 1, lg)
        self.t = 21 - lg
        self.xn = xs << self.t
        self.p = self.t & 1
        self.xs = xs
        self._ids = {}

    def ids(self, fam, m):
        k = (fam, m)
        if k not in self._ids:
            top = (self.xn >> (21 - m)) & ((1 << m) - 1) if m else np.zeros_like(self.xn)
            base = self.p if fam == 'p' else self.t
            key = (base << m) | top
            _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
            self._ids[k] = (inv.astype(np.int32), cnt)
        return self._ids[k]

    def func_of(self, v, fam, m):
        ids, cnt = self.ids(fam, m)
        s = np.bincount(ids, weights=v, minlength=len(cnt))
        return bool(np.all((s == 0) | (s == cnt)))

    def min_m(self, v, fam):
        if not self.func_of(v, fam, 21):
            return None
        lo, hi = 0, 21
        while lo < hi:
            mid = (lo + hi) // 2
            if self.func_of(v, fam, mid):
                hi = mid
            else:
                lo = mid + 1
        return lo


def classify(K: Keys, arr, HB, XP, XNP, fast=False):
    """arr: packed lanes, two halves of HB bytes (x = 1..MAX_X, then pad lanes x = 1).
    XP[k] / XNP[k]: packed bit k of x / of xn over one half. fast: class only, no m_p / m_t."""
    A, B = arr[:HB], arr[HB:]
    if not np.array_equal(A, B):
        return {'cls': 'random'}
    if not A.any() or np.all(A == 255):
        return {'cls': 'const', 'value': int(A[0] & 1)}
    for k, xb in enumerate(XP):
        if np.array_equal(A, xb):
            return {'cls': 'x', 'bit': k}
    for k, xb in enumerate(XNP):
        if np.array_equal(A, xb):
            return {'cls': 'xn', 'bit': k}
    vf = np.unpackbits(A, count=MAX_X, bitorder='little').astype(np.float64)
    if fast:
        if K.func_of(vf, 't', 0):
            c = 'flag'
        elif K.func_of(vf, 'p', 7):
            c = 'table'
        elif K.func_of(vf, 't', 7):
            c = 'table_t'
        elif K.func_of(vf, 'p', 21):
            c = 'arith_p'
        else:
            c = 'arith'
        return {'cls': c}
    mt = K.min_m(vf, 't')
    mp = K.min_m(vf, 'p')
    if mt == 0:
        c = 'flag'
    elif mp is not None and mp <= 7:
        c = 'table'
    elif mt is not None and mt <= 7:
        c = 'table_t'
    elif mp is not None:
        c = 'arith_p'
    else:
        c = 'arith'
    return {'cls': c, 'm_p': mp, 'm_t': mt}


def main(path, out_path, every=0):
    t0 = time.time()
    lines = parse(path)
    nl = len(lines)
    # registers
    pending, regs = {}, {}
    for op, ops, cond, raw in lines:
        if op == 'APPEND_TO_REGISTER':
            pending.setdefault(raw.split()[2], []).append(ops[0][1])
        elif op == 'REGISTER':
            regs[raw.split('"')[1]] = pending.pop(raw.split()[1], [])
    xq = regs['x']
    xset = set(xq)
    # Z_POW groups and segments
    zl = [i for i, l in enumerate(lines) if l[0] == 'Z_POW']
    groups = []
    for i in zl:
        if groups and i - groups[-1][-1] <= 500:
            groups[-1].append(i)
        else:
            groups.append([i])
    cuts = [0]
    for g in groups:
        cuts += [g[0], g[-1] + 1]
    cuts.append(nl)
    seg_names = ['pre']
    for k in range(len(groups)):
        seg_names += [f'G{k + 1}', 'mid' if k + 1 < len(groups) else 'post']
    if len(groups) == 0:
        seg_names = ['all']
        cuts = [0, nl]
    seg_of = np.zeros(nl, dtype=np.int16)
    for s in range(len(cuts) - 1):
        seg_of[cuts[s]:cuts[s + 1]] = s
    # phase temps and windows
    windows = []
    for g in groups:
        tq = collections.Counter(lines[i][1][0][1] for i in g).most_common(1)[0][0]
        start = None
        for i in range(g[0] - 1, -1, -1):
            op, ops = lines[i][0], lines[i][1]
            if op in ('HMR', 'R') and ops and ops[0] == ('q', tq):
                start = i + 1
                break
        if start is None:
            start = 0
        windows.append({'temp': tq, 'start': start, 'end': g[-1], 'first_zpow': g[0], 'n_zpow_on_temp':
                        sum(1 for i in g if lines[i][1][0][1] == tq), 'n_zpow': len(g)})
    # checkpoints: window start, first zpow, end+1 of every window
    ck_lines = {}
    for w, win in enumerate(windows):
        ck_lines[win['start']] = f'G{w + 1}.start'
        ck_lines[win['first_zpow']] = f'G{w + 1}.first_zpow'
        ck_lines[win['end'] + 1] = f'G{w + 1}.after_end'

    # ---- simulation
    Np = ((MAX_X + 7) // 8) * 8
    NL = 2 * Np
    NB = NL // 8
    xs1 = np.concatenate([np.arange(1, MAX_X + 1, dtype=np.int64), np.ones(Np - MAX_X, dtype=np.int64)])
    xs2 = np.concatenate([xs1, xs1])
    valid1 = np.concatenate([np.ones(MAX_X, dtype=np.uint8), np.zeros(Np - MAX_X, dtype=np.uint8)])
    VALID = np.packbits(np.concatenate([valid1, valid1]), bitorder='little')
    nvalid = 2 * MAX_X
    rng = np.random.default_rng(12345)
    Q, Bt = {}, {}
    for k, qi in enumerate(xq):
        Q[qi] = np.packbits(((xs2 >> k) & 1).astype(np.uint8), bitorder='little')
    del xs2

    def q(i):
        v = Q.get(i)
        if v is None:
            v = Q[i] = np.zeros(NB, dtype=np.uint8)
        return v

    def bit(i):
        v = Bt.get(i)
        if v is None:
            v = Bt[i] = np.zeros(NB, dtype=np.uint8)
        return v

    # ---- classification
    K = Keys()
    HB = Np // 8
    padx = np.ones(Np - MAX_X, dtype=np.int64)
    XP = [np.packbits(np.concatenate([(K.xs >> k) & 1, (padx >> k) & 1]).astype(np.uint8), bitorder='little')
          for k in range(22)]
    XNP = [np.packbits(np.concatenate([(K.xn >> k) & 1, (padx << 21) >> k & 1]).astype(np.uint8), bitorder='little')
           for k in range(22)]
    cache = {}

    def cls_of(arr, fast=False):
        h = (hash(arr.tobytes()), fast)
        if h in cache:
            return cache[h]
        r = classify(K, arr, HB, XP, XNP, fast)
        cache[h] = r
        return r

    def describe(snap, fast=False):
        vals, lv = snap
        per = {}
        for qi in sorted(lv):
            c = dict(cls_of(vals[qi], fast))
            c['reg'] = 'x' if qi in xset else ''
            per[qi] = c
        hist = collections.Counter(c['cls'] for c in per.values())
        hist_reg = collections.Counter((c['cls'], c['reg'] or '-') for c in per.values())
        return per, dict(sorted(hist.items())), {f'{a}|{b}': n for (a, b), n in sorted(hist_reg.items())}

    live = set(qi for qi in xq if Q[qi].any())
    trans = collections.defaultdict(list)      # qubit -> [(line, became_live)]
    for qi in live:
        trans[qi].append((0, True))
    live_at = np.zeros(nl, dtype=np.int16)
    nseg = len(cuts) - 1
    seg_max = [(-1, -1)] * nseg
    seg_snap = [None] * nseg
    seg_touch = [collections.Counter() for _ in range(nseg)]
    seg_tof = [[0, 0.0] for _ in range(nseg)]
    snaps = {}
    stack = []
    win_feed = [collections.defaultdict(set) for _ in windows]
    tof_hist = collections.Counter()           # live count at each executed Toffoli-like gate (weight = exec frac)

    timeline = []

    def tl_entry(ln):
        per, hist, hist_reg = describe((Q, set(live)), fast=True)
        xs_ = {}
        for k, qi in enumerate(xq):
            c = per.get(qi, {'cls': 'zero'})
            e = {'cls': c['cls']}
            if c['cls'] not in ('xn', 'x', 'zero', 'random'):
                d = Q[qi] ^ np.concatenate([XNP[k], XNP[k]])
                e['delta_xn'] = cls_of(d, True)['cls']
            if 'bit' in c:
                e['bit'] = c['bit']
            xs_[k] = e
        return {'line': ln + 1, 'live': len(live), 'seg': seg_names[seg_of[ln]], 'classes': hist,
                'classes_by_reg': hist_reg, 'x_reg': xs_}

    def snapshot():
        return {qi: Q[qi].copy() for qi in live}, set(live)

    for ln, (op, ops, cond, raw) in enumerate(lines):
        if ln in ck_lines:
            snaps[ck_lines[ln]] = (ln, snapshot())
        if every and ln % every == 0:
            timeline.append(tl_entry(ln))
        s = seg_of[ln]
        if op in ('', 'APPEND_TO_REGISTER', 'REGISTER'):
            live_at[ln] = len(live)
            continue
        mask = stack[-1] if stack else None
        if cond is not None:
            c = bit(cond)
            mask = c if mask is None else (mask & c)
        if op == 'PUSH_CONDITION':
            c = bit(cond)
            stack.append(c.copy() if not stack else (stack[-1] & c))
            live_at[ln] = len(live)
            continue
        if op == 'POP_CONDITION':
            stack.pop()
            live_at[ln] = len(live)
            continue
        for kind, i in ops:
            if kind == 'q':
                seg_touch[s][i] += 1
        if op in TOFF:
            fr = 1.0 if mask is None else int(np.bitwise_count(mask & VALID).sum()) / nvalid
            seg_tof[s][0] += 1
            seg_tof[s][1] += fr
            n_before = len(live)
        for w, win in enumerate(windows):
            if win['start'] <= ln <= win['end'] and op in ('CX', 'CCX', 'CSWAP'):
                qs = [i for kind, i in ops if kind == 'q']
                tq = win['temp']
                if op == 'CX' and qs[1] == tq:
                    win_feed[w][qs[0]].add('cx_src')
                elif op == 'CCX' and qs[2] == tq:
                    win_feed[w][qs[0]].add('ccx_in')
                    win_feed[w][qs[1]].add('ccx_in')
                elif op == 'CSWAP' and tq in qs[1:]:
                    win_feed[w][qs[0]].add('cswap_ctl')
                    other = qs[2] if qs[1] == tq else qs[1]
                    win_feed[w][other].add('cswap_partner')
        if op in PHASE_ONLY:
            pass
        elif op == 'X':
            a = q(ops[0][1])
            if mask is None:
                np.bitwise_not(a, out=a)
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
                a[:] = 0
            else:
                a &= ~mask
        elif op == 'HMR':
            qi, bi = ops[0][1], ops[1][1]
            r = rng.integers(0, 256, NB, dtype=np.uint8)
            a, bb = q(qi), bit(bi)
            if mask is None:
                a[:] = 0
                bb[:] = r
            else:
                a &= ~mask
                bb[:] = (r & mask) | (bb & ~mask)
        elif op == 'BIT_STORE0':
            bb = bit(ops[0][1])
            if mask is None:
                bb[:] = 0
            else:
                bb &= ~mask
        elif op == 'BIT_STORE1':
            bb = bit(ops[0][1])
            if mask is None:
                bb[:] = 255
            else:
                bb |= mask
        elif op == 'BIT_INVERT':
            bb = bit(ops[0][1])
            if mask is None:
                np.bitwise_not(bb, out=bb)
            else:
                bb ^= mask
        else:
            raise ValueError(f'unhandled op {op!r} at line {ln + 1}: {raw}')
        if op not in PHASE_ONLY:
            for kind, i in ops:
                if kind == 'q':
                    nz = bool(Q[i].any())
                    if nz and i not in live:
                        live.add(i)
                        trans[i].append((ln + 1, True))
                    elif not nz and i in live:
                        live.discard(i)
                        trans[i].append((ln + 1, False))
        n = len(live)
        live_at[ln] = n
        if op in TOFF:
            tof_hist[max(n_before, n)] += fr
        if n > seg_max[s][0]:
            seg_max[s] = (n, ln)
            seg_snap[s] = snapshot()
    sim_s = time.time() - t0
    restored = all(np.array_equal(Q[qi], np.packbits(((np.concatenate([xs1, xs1]) >> k) & 1).astype(np.uint8),
                                                        bitorder='little')) for k, qi in enumerate(xq))
    dirty = sorted(i for i, v in Q.items() if i not in xset and v.any())

    segs = []
    for s in range(nseg):
        n, ln = seg_max[s]
        if seg_snap[s] is None:
            continue
        per, hist, hist_reg = describe(seg_snap[s])
        idle = [qi for qi in per if seg_touch[s][qi] == 0]
        idle_hist = collections.Counter(per[qi]['cls'] for qi in idle)
        lo, hi = cuts[s], cuts[s + 1]
        segs.append({'name': seg_names[s], 'lines': [lo + 1, hi], 'max_live': n, 'max_line': ln + 1,
                     'classes_at_max': hist, 'classes_by_reg_at_max': hist_reg,
                     'idle_in_segment_at_max': len(idle), 'idle_classes': dict(sorted(idle_hist.items())),
                     'toffoli_static': seg_tof[s][0], 'toffoli_exec_mean': round(seg_tof[s][1], 4),
                     'qubits': {str(k): v for k, v in per.items()},
                     'idle_qubits': idle})
    wins = []
    for w, win in enumerate(windows):
        g = f'G{w + 1}'
        ln0, snap0 = snaps[f'{g}.start']
        ln1, snap1 = snaps[f'{g}.after_end']
        lnz, snapz = snaps[f'{g}.first_zpow']
        per0, _, _ = describe(snap0)
        perz, histz, histz_reg = describe(snapz)
        feed = []
        for qi, roles in sorted(win_feed[w].items()):
            if qi == win['temp']:
                continue
            c0 = per0.get(qi, {'cls': 'zero'})
            feed.append({'q': qi, 'reg': 'x' if qi in xset else '', 'roles': sorted(roles), 'cls_at_start': c0,
                         'live_at_start': qi in snap0[1], 'live_after_end': qi in snap1[1],
                         'transitions': [t for t in trans[qi] if ln0 - 3000 <= t[0] <= ln1 + 3000][:12]})
        fc = collections.Counter()
        for f in feed:
            kind = 'x-reg' if f['reg'] else ('persistent' if f['live_at_start'] and f['live_after_end'] else 'phase-only')
            fc[(kind, f['cls_at_start']['cls'])] += 1
        wins.append({**{k: (v + 1 if k in ('start', 'end', 'first_zpow') else v) for k, v in win.items()},
                     'live_at_start': len(snap0[1]), 'live_at_first_zpow': len(snapz[1]),
                     'live_after_end': len(snap1[1]),
                     'persistent_through_window': len(snap0[1] & snap1[1]),
                     'persistent_classes_by_reg': dict(sorted(collections.Counter(
                         f"{per0[qi]['cls']}|{'x' if qi in xset else '-'}" for qi in snap0[1] & snap1[1]).items())),
                     'classes_at_first_zpow': histz, 'classes_by_reg_at_first_zpow': histz_reg,
                     'feeders': feed,
                     'feeder_summary': {f'{a}|{b}': n for (a, b), n in sorted(fc.items())}})
    th = sorted(tof_hist.items())
    tot = sum(v for _, v in th)
    out = {'circuit': path, 'lines': nl, 'lanes': MAX_X, 'draws': 2, 'sim_seconds': round(sim_s, 1),
           'seconds': round(time.time() - t0, 1),
           'x_restored': restored, 'dirty_scratch': dirty[:20], 'num_qubits_touched': len(Q),
           'peak_live': int(live_at.max()), 'peak_line': int(live_at.argmax()) + 1,
           'toffoli_static': sum(v[0] for v in seg_tof), 'toffoli_exec_mean': round(sum(v[1] for v in seg_tof), 4),
           'toffoli_exec_by_live': {int(k): round(v, 4) for k, v in th},
           'toffoli_exec_frac_at_ge': {str(k): round(sum(v for kk, v in th if kk >= k) / tot, 4) for k in
                                       (59, 63, 72, 84, 89, 92)} if tot else {},
           'zpow_groups': [[g[0] + 1, g[-1] + 1, len(g)] for g in groups],
           'segments': segs, 'phase_windows': wins, 'timeline_every': every, 'timeline': timeline,
           'live_profile_rle': rle(live_at)}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('segments', 'phase_windows', 'live_profile_rle', 'timeline')}, indent=1))
    for sg in segs:
        print(sg['name'], sg['lines'], 'max', sg['max_live'], '@', sg['max_line'], sg['classes_at_max'], 'idle',
              sg['idle_in_segment_at_max'], sg['idle_classes'], 'tof', sg['toffoli_static'], sg['toffoli_exec_mean'])
    for w in wins:
        print('window', w['temp'], w['start'], w['end'], 'zpow on temp', w['n_zpow_on_temp'], 'live start/first/after',
              w['live_at_start'], w['live_at_first_zpow'], w['live_after_end'], w['feeder_summary'])


def rle(a):
    out = []
    prev, start = None, 0
    for i, v in enumerate(a.tolist()):
        if v != prev:
            if prev is not None:
                out.append([start + 1, i, prev])
            prev, start = v, i
    out.append([start + 1, len(a), prev])
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ev = [int(a.split('=')[1]) for a in sys.argv[3:] if a.startswith('--every=')]
    main(sys.argv[1], sys.argv[2], ev[0] if ev else 0)

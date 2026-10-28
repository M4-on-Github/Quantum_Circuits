"""Semantic classification of every Toffoli-like gate in a .kmx dqi circuit (exp-005).

Usage: python -I kernel_semantics.py <skeleton.npz> <dqi.kmx.xz> <out.json> <out_per_gate.npz> [plain|restart]

Text analysis only: the .kmx is parsed by this script and evaluated by its own bit-parallel Boolean
model (Python ints as lane vectors). Nothing in the input is executed.

1. Segmentation. The Toffoli stream is cut into segments: occurrences of the relabelled Toffoli
   skeleton of the first instance of every tagged sub-kernel (patterns.py; longest first,
   non-overlapping), and the maximal uncovered runs between them, split at tag-path changes.
2. Value model per segment. The segment's line range runs from just after the previous Toffoli-like
   gate to its own last Toffoli-like gate. Every quantum operand in the range is a free input at the
   range start. CX, SWAP, X, CCX, CSWAP act on values; R and HMR reset to 0; phase gates (Z, CZ,
   CCZ, NEG) and classical-bit ops do not change values. Ops inside PUSH_CONDITION blocks are applied
   as if the condition were true (those gates are flagged as conditioned).
3. Per Toffoli-like gate, for each control: an affinity test (second derivative zero on 48 random
   (x, u, v) triples; a quadratic control passes one triple with probability <= 3/4) and, for affine
   controls, the exact set of start-of-segment qubits it depends on.
4. Per segment: the affine x affine gates are 2-coloured (all qubits of one control's support share a
   colour, the two controls get different colours). Each connected component is a bilinear map between
   operand sets A and B; its widths |A|, |B| and its gate count are recorded. A component whose
   constraints cannot be 2-coloured (a control support shared by both sides, as in a squaring or a
   quadratic form of one register) is flagged as not bipartite.
5. Mode 'restart': inside a segment, a CCX with a non-affine control starts a new sub-segment (all
   touched qubits become fresh inputs just before it). Chained products then each get their own
   operand sets, while AND trees (zero tests, comparators) fall apart into 1 x 1 components.
"""
import json
import lzma
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patterns as P  # noqa: E402

D_SAMPLES = 48
SEED = 5005


def segments(d, paths):
    p = d['path']; op, a, b, c = d['op'], d['a'], d['b'], d['c']
    N = len(op)
    first = {}
    i = 0
    while i < N:
        j = i
        while j < N and p[j] == p[i]:
            j += 1
        key = (paths[p[i]], j - i)
        if '/' in key[0] and key[1] <= 400 and key not in first:
            first[key] = i
        i = j
    uniq = {}
    for (name, n), s in first.items():
        t = P.relabel(op[s:s + n], a[s:s + n], b[s:s + n], c[s:s + n])
        uniq.setdefault(t, []).append(f'{name}#{n}')
    cov = np.full(N, -1, np.int32)
    names, lengths = [], []
    for t, ks in sorted(uniq.items(), key=lambda kv: (-len(kv[0]), kv[1])):
        names.append('|'.join(sorted(ks)))
        lengths.append(len(t))
        nid = len(names) - 1
        for h in P.find(t, op, a, b, c):
            if (cov[h:h + len(t)] == -1).all():
                cov[h:h + len(t)] = nid
    segs = []  # (start, end, label)
    i = 0
    while i < N:
        if cov[i] >= 0:
            nid = cov[i]
            n = lengths[nid]
            segs.append((i, i + n, 'T:' + names[nid]))
            i += n
            continue
        j = i
        while j < N and cov[j] < 0 and p[j] == p[i]:
            j += 1
        segs.append((i, j, 'run:' + paths[p[i]]))
        i = j
    assert sum(e - s for s, e, _ in segs) == N
    return segs, names


class Seg:
    def __init__(self, start, end, label, first_line, last_line):
        self.start, self.end, self.label = start, end, label
        self.first_line, self.last_line = first_line, last_line
        self.lines = []


def qubits_of(parts):
    return [int(t[1:]) for t in parts[1:] if t.startswith('q')]


def analyse(seg, rng, restart=False):
    """Per-gate records (kind, (affine, support) per control, ..., sub-segment index).

    With restart=True, a CCX with a non-affine control starts a new sub-segment: every touched qubit
    becomes a fresh input just before that gate, and the gate is described in the new basis.
    """
    V = sorted({q for parts in seg.lines for q in qubits_of(parts)})
    n = len(V)
    idx = {q: k for k, q in enumerate(V)}
    # lanes: [0] base x0, [1..n] x0 ^ e_v, then 4*D degree lanes
    L = 1 + n + 4 * D_SAMPLES
    base = 1 + n
    ALL = (1 << L) - 1

    def fresh_state():
        bits = np.zeros((n, L), dtype=bool)
        x0 = rng.integers(0, 2, n).astype(bool)
        bits[:, 0] = x0
        bits[:, 1:n + 1] = x0[:, None]
        bits[np.arange(n), 1 + np.arange(n)] ^= True
        for t in range(D_SAMPLES):
            x = rng.integers(0, 2, n).astype(bool)
            u = rng.integers(0, 2, n).astype(bool)
            v = rng.integers(0, 2, n).astype(bool)
            bits[:, base + 4 * t + 0] = x
            bits[:, base + 4 * t + 1] = x ^ u
            bits[:, base + 4 * t + 2] = x ^ v
            bits[:, base + 4 * t + 3] = x ^ u ^ v
        packed = np.packbits(bits, axis=1, bitorder='little')
        return {V[k]: int.from_bytes(packed[k].tobytes(), 'little') for k in range(n)}

    st = fresh_state()
    sub = 0
    deg_mask = 0
    for t in range(D_SAMPLES):
        deg_mask |= 1 << (base + 4 * t)
    recs = []

    def describe(val):
        y = val >> base
        y = y ^ (y >> 1) ^ (y >> 2) ^ (y >> 3)
        aff = (y << base) & deg_mask == 0
        if not aff:
            return False, None
        b0 = val & 1
        diff = (val >> 1) & ((1 << n) - 1)
        if b0:
            diff ^= (1 << n) - 1
        supp = []
        k = 0
        while diff:
            if diff & 1:
                supp.append(V[k])
            diff >>= 1
            k += 1
        return True, supp

    for parts in seg.lines:
        o = parts[0]
        if o == 'CX':
            c, t = int(parts[1][1:]), int(parts[2][1:])
            st[t] ^= st[c]
        elif o == 'SWAP':
            x, y = int(parts[1][1:]), int(parts[2][1:])
            st[x], st[y] = st[y], st[x]
        elif o == 'CCX':
            x, y, t = int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
            r1, r2 = describe(st[x]), describe(st[y])
            if restart and not (r1[0] and r2[0]):
                st = fresh_state()
                sub += 1
                r1, r2 = describe(st[x]), describe(st[y])
            recs.append((0, r1, r2, sub))
            st[t] ^= st[x] & st[y]
        elif o == 'CCZ':
            x, y, z = int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
            recs.append((1, describe(st[x]), describe(st[y]), describe(st[z]), sub))
        elif o == 'CSWAP':
            cc, x, y = int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
            recs.append((2, describe(st[cc]), None, sub))
            dd = (st[x] ^ st[y]) & st[cc]
            st[x] ^= dd
            st[y] ^= dd
        elif o == 'X':
            q = int(parts[1][1:])
            st[q] ^= ALL
        elif o in ('R', 'HMR'):
            st[int(parts[1][1:])] = 0
        elif o in ('Z', 'CZ', 'NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'PUSH_CONDITION',
                   'POP_CONDITION', 'INFO_TAG'):
            pass
        else:
            raise ValueError(f'unhandled op {parts}')
    assert len(recs) == seg.end - seg.start, (seg.label, len(recs), seg.end - seg.start)
    return recs


def colour(recs):
    """2-colours qubits over affine x affine CCX gates. Returns components and conflict count."""
    parent, par = {}, {}

    def find(x):
        if parent[x] == x:
            return x, 0
        r, p = find(parent[x])
        parent[x] = r
        par[x] ^= p
        return r, par[x]

    def add(x):
        if x not in parent:
            parent[x] = x
            par[x] = 0

    def union(x, y, rel):
        rx, px = find(x)
        ry, py = find(y)
        if rx == ry:
            return (px ^ py) == rel
        parent[rx] = ry
        par[rx] = px ^ py ^ rel
        return True

    conflicts = 0
    conflict_q = []
    gate_root = []
    for r in recs:
        if r[0] != 0 or not (r[1][0] and r[2][0]) or not r[1][1] or not r[2][1]:
            gate_root.append(None)
            continue
        s1 = [(r[3], q) for q in r[1][1]]
        s2 = [(r[3], q) for q in r[2][1]]
        for q in s1 + s2:
            add(q)
        ok = all(union(s1[0], q, 0) for q in s1[1:]) and all(union(s2[0], q, 0) for q in s2[1:])
        ok = union(s1[0], s2[0], 1) and ok
        if not ok:
            conflicts += 1
            conflict_q.append(s1[0])
        gate_root.append(s1[0])
    comps = {}
    for q in parent:
        rt, pq = find(q)
        comps.setdefault(rt, [set(), set()])[pq].add(q)
    gate_comp = [None if g is None else find(g)[0] for g in gate_root]
    bad_roots = {find(q)[0] for q in conflict_q}
    return comps, gate_comp, conflicts, bad_roots


def main(skel_path, kmx_path, out_path, per_gate_path=None, mode='plain'):
    restart = mode == 'restart'
    d = np.load(skel_path)
    meta = json.loads(str(d['meta']))
    paths = meta['paths']
    line = d['line']
    segs, names = segments(d, paths)
    rng = np.random.default_rng(SEED)
    segobjs = []
    prev = -1
    for s, e, lab in segs:
        segobjs.append(Seg(s, e, lab, int(prev) + 1, int(line[e - 1])))
        prev = line[e - 1]
    N = len(line)
    g_kind = np.full(N, -1, np.int8)      # 0 affine x affine, 1 some control non-affine, 2 CSWAP, 3 CCZ
    g_w1 = np.zeros(N, np.int16)
    g_w2 = np.zeros(N, np.int16)
    g_compA = np.zeros(N, np.int16)
    g_compB = np.zeros(N, np.int16)
    g_seg = np.zeros(N, np.int32)
    g_bip = np.zeros(N, bool)             # gate belongs to a conflict-free (bipartite) component
    g_comp = np.full(N, -1, np.int32)     # global component id (-1: gate not in any component)
    comp_counter = [0]
    seg_out = []
    k = 0
    cur = segobjs[0]
    def finish(cur, k):
                recs = analyse(cur, rng, restart)
                comps, gate_comp, conflicts, bad_roots = colour(recs)
                sizes = {rt: (len(A), len(B)) for rt, (A, B) in comps.items()}
                gid = {rt: comp_counter[0] + j for j, rt in enumerate(comps)}
                comp_counter[0] += len(comps)
                for off, r in enumerate(recs):
                    gi = cur.start + off
                    g_seg[gi] = k
                    if r[0] == 2:
                        g_kind[gi] = 2
                        continue
                    if r[0] == 1:
                        g_kind[gi] = 3
                        continue
                    a1, a2 = r[1], r[2]
                    g_kind[gi] = 0 if (a1[0] and a2[0]) else 1
                    g_w1[gi] = len(a1[1]) if a1[0] else -1
                    g_w2[gi] = len(a2[1]) if a2[0] else -1
                    if gate_comp[off] is not None:
                        A, B = sizes[gate_comp[off]]
                        g_compA[gi], g_compB[gi] = min(A, B), max(A, B)
                        g_bip[gi] = gate_comp[off] not in bad_roots
                        g_comp[gi] = gid[gate_comp[off]]
                seg_out.append({'k': k, 'start': cur.start, 'end': cur.end, 'label': cur.label,
                                'lines': [cur.first_line, cur.last_line], 'conflicts': conflicts,
                                'components': sorted([sorted(v) for v in sizes.values()], reverse=True)[:8],
                                'n_bad_components': len(bad_roots),
                                'n_sub': 1 + max((r[-1] for r in recs), default=0),
                                'n_components': len(sizes)})
                cur.lines = None

    opener = lzma.open if str(kmx_path).endswith('.xz') else open
    with opener(kmx_path, 'rt', encoding='utf-8') as f:
        for ln, text in enumerate(f):
            while k < len(segobjs) and ln > cur.last_line:
                finish(cur, k)
                k += 1
                if k < len(segobjs):
                    cur = segobjs[k]
            if k == len(segobjs):
                break
            if ln >= cur.first_line:
                parts = text.split()
                if parts and parts[0] not in ('REGISTER', 'APPEND_TO_REGISTER'):
                    cur.lines.append(parts)
    if k < len(segobjs):
        finish(cur, k)
        k += 1
    assert k == len(segobjs), (k, len(segobjs))
    Path(out_path).write_text(json.dumps({'templates': names, 'segments': seg_out}, indent=0))
    if per_gate_path:
        np.savez_compressed(per_gate_path, kind=g_kind, w1=g_w1, w2=g_w2, compA=g_compA, compB=g_compB, bip=g_bip, comp=g_comp,
                            seg=g_seg)
    print(json.dumps({'segments': len(seg_out), 'kinds': {int(x): int((g_kind == x).sum()) for x in range(-1, 4)}}))


if __name__ == '__main__':
    main(*sys.argv[1:6])

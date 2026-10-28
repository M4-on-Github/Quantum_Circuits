"""Field-multiplication test for bilinear 12 x 12 kernels found by kernel_semantics.py (exp-005).

Usage: python -I field_test.py <skeleton.npz> <dqi.kmx.xz> <semantics.json> <out.json> [max_per_label]

For each selected segment whose largest bilinear component has both operand widths in 12..32 (at most
max_per_label segments per (label, Toffoli count, widths)): take the segment's lines up to
just before the next Toffoli-like gate (so the product's fan-out is included), fix every other input at
a random value x0, and evaluate the circuit text with this script's own Boolean model on all
2^12 values of operand A and on b in {0, e_1, ..., e_12} of operand B. With
B(a, b) = F(a, b) ^ F(a, 0) ^ F(0, b) ^ F(0, 0) over all touched qubits it checks:
  - bilinear in b (B(a, b1 ^ b2) = B(a, b1) ^ B(a, b2) on 256 random triples);
  - the same B for a second random x0 (the product does not depend on other inputs);
  - no zero divisors: for every a != 0 the 12 vectors B(a, e_j) are linearly independent,
    which is what a field (or semifield) multiplication a * b requires;
  - output rank: the span of all B(a, b) has dimension 12.
Wider operands (m-bit x n-bit, m <= n, up to 32): sampled version (test_wide), 256 random nonzero
operands per side: rank n when the m-bit side is fixed, rank m when the n-bit side is fixed.
Text evaluation only; nothing in the input is executed.
"""
import json
import lzma
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel_semantics as KS  # noqa: E402


def run_lines(lines, st, ALL):
    for parts in lines:
        o = parts[0]
        if o == 'CX':
            st[int(parts[2][1:])] ^= st[int(parts[1][1:])]
        elif o == 'SWAP':
            x, y = int(parts[1][1:]), int(parts[2][1:])
            st[x], st[y] = st[y], st[x]
        elif o == 'CCX':
            st[int(parts[3][1:])] ^= st[int(parts[1][1:])] & st[int(parts[2][1:])]
        elif o == 'CSWAP':
            c, x, y = int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
            dd = (st[x] ^ st[y]) & st[c]
            st[x] ^= dd
            st[y] ^= dd
        elif o == 'X':
            st[int(parts[1][1:])] ^= ALL
        elif o in ('R', 'HMR'):
            st[int(parts[1][1:])] = 0
    return st


def gf2_rank(rows):
    rows = [r for r in rows if r]
    rank = 0
    while rows:
        piv = max(rows)
        hb = piv.bit_length() - 1
        rows = [r ^ piv if (r >> hb) & 1 else r for r in rows if r != piv]
        rows = [r for r in rows if r]
        rank += 1
    return rank


def evaluate(lines, V, Aq, Bq, x0, avals, bvals):
    """Returns, per qubit in V, an int lane-vector of final values for the (a, b) lane grid."""
    na, nb = len(avals), len(bvals)
    L = na * nb
    ALL = (1 << L) - 1
    st = {}
    for q in V:
        st[q] = ALL if x0[q] else 0
    for k, q in enumerate(Aq):
        bits = np.repeat(((avals >> k) & 1).astype(bool), nb)
        st[q] = int.from_bytes(np.packbits(bits, bitorder='little').tobytes(), 'little')
    for k, q in enumerate(Bq):
        bits = np.tile(((bvals >> k) & 1).astype(bool), na)
        st[q] = int.from_bytes(np.packbits(bits, bitorder='little').tobytes(), 'little')
    return run_lines(lines, st, ALL), L


def outputs(st, V, L):
    """Lane -> output vector (Python int over V) for every lane."""
    nbytes = (L + 7) // 8
    mat = np.zeros((len(V), L), dtype=bool)
    for i, q in enumerate(V):
        mat[i] = np.unpackbits(np.frombuffer(st[q].to_bytes(nbytes, 'little'), np.uint8), bitorder='little')[:L]
    packed = np.packbits(mat.T, axis=1, bitorder='little')
    return [int.from_bytes(r.tobytes(), 'little') for r in packed]


def test_segment(lines_tof, lines_all, rng):
    n_tof = sum(1 for p in lines_tof if p[0] in ('CCX', 'CCZ', 'CSWAP'))
    seg = KS.Seg(0, n_tof, 'x', 0, 0)
    seg.lines = lines_tof
    recs = KS.analyse(seg, rng)
    comps, gate_comp, conflicts, bad_roots = KS.colour(recs)
    big = max(comps.values(), key=lambda AB: len(AB[0]) * len(AB[1]))
    Aq, Bq = sorted(q for _, q in big[0]), sorted(q for _, q in big[1])  # keys are (sub, qubit)
    res = {'n_toffoli': len(recs), 'conflicts': conflicts, 'A': len(Aq), 'B': len(Bq),
           'A_qubits': [min(Aq), max(Aq)], 'B_qubits': [min(Bq), max(Bq)],
           'n_components': len(comps)}
    if not (len(Aq) == 12 and len(Bq) == 12):
        if 12 <= min(len(Aq), len(Bq)) and max(len(Aq), len(Bq)) <= 32:
            res.update(test_wide(lines_all, Aq, Bq, rng))
        else:
            res['skipped'] = 'operand widths outside 12..32'
        return res
    V = sorted({int(t[1:]) for p in lines_all for t in p[1:] if t.startswith('q')})
    avals = np.arange(4096, dtype=np.int64)
    bvals = np.array([0] + [1 << j for j in range(12)], dtype=np.int64)
    Bmaps = []
    for trial in range(2):
        x0 = {q: bool(rng.integers(0, 2)) for q in V}
        st, L = evaluate(lines_all, V, Aq, Bq, x0, avals, bvals)
        out = outputs(st, V, L)
        F = lambda ai, bi: out[ai * 13 + bi]
        Bm = [[F(a, j) ^ F(a, 0) ^ F(0, j) ^ F(0, 0) for j in range(13)] for a in range(4096)]
        Bmaps.append(Bm)
    res['x0_independent'] = Bmaps[0] == Bmaps[1]
    Bm = Bmaps[0]
    zero_div = sum(1 for a in range(1, 4096) if gf2_rank(Bm[a][1:]) < 12)
    res['zero_divisor_a_count'] = zero_div
    span = []
    for a in range(1, 4096, 97):
        span += Bm[a][1:]
    res['output_rank'] = gf2_rank(span)
    # bilinearity in b on random triples (separate evaluation with random b lanes)
    bl = rng.integers(0, 4096, size=(256, 2))
    a_r = rng.integers(1, 4096, size=256)
    x0 = {q: bool(rng.integers(0, 2)) for q in V}
    bvals2 = np.concatenate([bl[:, 0], bl[:, 1], bl[:, 0] ^ bl[:, 1], [0]])
    st, L = evaluate(lines_all, V, Aq, Bq, x0, a_r, bvals2)
    out = outputs(st, V, L)
    nb = len(bvals2)
    st0, L0 = evaluate(lines_all, V, Aq, Bq, x0, np.zeros(1, np.int64), bvals2)
    out0 = outputs(st0, V, L0)
    bad = 0
    for i in range(256):
        base = i * nb
        def Bf(col):
            return out[base + col] ^ out[base + nb - 1] ^ out0[col] ^ out0[nb - 1]
        if Bf(i) ^ Bf(256 + i) ^ Bf(512 + i):
            bad += 1
    res['bilinear_violations_of_256'] = bad
    res['field_like'] = bool(res['x0_independent'] and zero_div == 0 and bad == 0 and res['output_rank'] == 12)
    return res


def sampled_ranks(lines_all, V, Pq, Qq, rng, n_samples=256):
    """Ranks of b -> B(p, b) (b over the Qq side) for random nonzero p on the Pq side, for two x0."""
    m = len(Pq)
    pv = np.concatenate([[0], rng.integers(1, 1 << m, size=n_samples)]).astype(np.int64)
    qv = np.array([0] + [1 << j for j in range(len(Qq))], dtype=np.int64)
    nq = len(qv)
    maps = []
    for trial in range(2):
        x0 = {q: bool(rng.integers(0, 2)) for q in V}
        st, L = evaluate(lines_all, V, Pq, Qq, x0, pv, qv)
        out = outputs(st, V, L)
        F = lambda i, j: out[i * nq + j]
        maps.append([[F(i, j) ^ F(i, 0) ^ F(0, j) ^ F(0, 0) for j in range(1, nq)] for i in range(1, len(pv))])
    ranks = [gf2_rank(r) for r in maps[0]]
    return ranks, maps[0] == maps[1]


def test_wide(lines_all, Aq, Bq, rng):
    """Sampled no-zero-divisor test for a bilinear map between an m-bit and an n-bit operand (m <= n).

    For a field-type product (GF(2^m) scalar times a GF(2^m)-vector, or a GF(2^n) product) every nonzero
    m-bit operand gives a rank-n map and every nonzero n-bit operand gives a rank-m map.
    """
    S, Lg = (Aq, Bq) if len(Aq) <= len(Bq) else (Bq, Aq)
    V = sorted({int(t[1:]) for p in lines_all for t in p[1:] if t.startswith('q')})
    r_s, ind_s = sampled_ranks(lines_all, V, S, Lg, rng)
    r_l, ind_l = sampled_ranks(lines_all, V, Lg, S, rng)
    res = {'small_side': len(S), 'large_side': len(Lg),
           'rank_fix_small_min_max': [min(r_s), max(r_s)], 'rank_fix_large_min_max': [min(r_l), max(r_l)],
           'x0_independent': bool(ind_s and ind_l), 'samples_per_side': len(r_s)}
    res['field_like'] = bool(res['x0_independent'] and min(r_s) == len(Lg) and min(r_l) == len(S))
    return res


def main(skel, kmx, semj, outp, max_per_label=3):
    max_per_label = int(max_per_label)
    d = np.load(skel)
    line = d['line']
    sem = json.loads(Path(semj).read_text())
    chosen = {}
    for s in sem['segments']:
        comps = s['components']
        if not comps or not (12 <= comps[0][0] and comps[0][1] <= 32):
            continue
        key = (s['label'], s['end'] - s['start'], tuple(comps[0]))
        if len(chosen.setdefault(key, [])) < max_per_label:
            chosen[key].append(s)
    want = sorted((s for v in chosen.values() for s in v), key=lambda s: s['lines'][0])
    ranges = []
    for s in want:
        end_all = int(line[s['end']]) - 1 if s['end'] < len(line) else s['lines'][1]
        ranges.append((s['lines'][0], s['lines'][1], end_all, s))
    bufs = [([], []) for _ in ranges]
    last = max(r[2] for r in ranges)
    with lzma.open(kmx, 'rt', encoding='utf-8') as f:
        for ln, text in enumerate(f):
            if ln > last:
                break
            for (lo, hi_t, hi_a, _), (bt, ba) in zip(ranges, bufs):
                if lo <= ln <= hi_a:
                    parts = text.split()
                    if parts[0] in ('REGISTER', 'APPEND_TO_REGISTER'):
                        continue
                    ba.append(parts)
                    if ln <= hi_t:
                        bt.append(parts)
    rng = np.random.default_rng(7)
    results = []
    for (lo, hi_t, hi_a, s), (bt, ba) in zip(ranges, bufs):
        r = test_segment(bt, ba, rng)
        r.update({'segment': s['k'], 'label': s['label'], 'lines': [lo, hi_a]})
        results.append(r)
        print(json.dumps({k: r.get(k) for k in ('segment', 'label', 'n_toffoli', 'A', 'B', 'zero_divisor_a_count',
                                                'output_rank', 'rank_fix_small_min_max', 'rank_fix_large_min_max',
                                                'x0_independent', 'bilinear_violations_of_256',
                                                'field_like')}), flush=True)
    Path(outp).write_text(json.dumps(results, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])

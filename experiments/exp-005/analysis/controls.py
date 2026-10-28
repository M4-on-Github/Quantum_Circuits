"""Controls and structural checks behind statements in the exp-005 README (critic-fix revision).

Usage (repo root):
  .venv/Scripts/python.exe -I -B experiments/exp-005/analysis/controls.py \
      experiments/exp-005/out/skeleton.npz experiments/exp-005/out/semantics.json \
      experiments/exp-005/kaggle_output_dump/exp005dump/dqi.kmx.xz experiments/exp-005/controls.json

Text analysis of the downloaded circuit only (it is parsed, never executed); control circuits are built
with kickmix's own builder. Sections of the output JSON:

  semantic_controls  kickmix 1.0.0 builds (gf_mul, init/del_gf2_mul, controlled multiply, two and chained
                     multiplies, controlled gf2_iadd, 12-bit zero test, CX-mixed operand, multiply by own
                     copy). Each is treated as one segment and classified with kernel_semantics.analyse /
                     colour in plain and restart mode; fingerprint hits of the 63- and 75-Toffoli kickmix
                     templates (patterns.find) are counted in its skeleton.
  field_controls     field_test.test_segment on kickmix gf_mul (n = 12, 24) and on truncated polynomial
                     products c = a*b mod x^n (n = 12, 24), which have zero divisors.
  jet_skeletons      for the five jet-only tagged sub-kernels: occurrences of the first instance's
                     relabelled Toffoli skeleton in the whole circuit, and how many lie inside that tag.
  kernels_126        the three field-tested 126-Toffoli 24 x 24 kernels (segments 1856, 2807, 2856):
                     rank of b -> B(e_i, b) for every basis vector, a dense sampled rank test (16,384
                     nonzero operands per side), and an explicit zero-divisor witness (a, b nonzero,
                     B(a, b) = 0) re-checked by direct evaluation at two random settings x0 of the other inputs.
  field_test_input   which semantics file and max_per_label reproduce out/field_test.json's segment list.
"""
import json
import lzma
import sys
import tempfile
from pathlib import Path

import numpy as np
import kickmix as km

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patterns as P  # noqa: E402
import kmx_skeleton  # noqa: E402
import kernel_semantics as KS  # noqa: E402
import field_test as FT  # noqa: E402

SKIP = ('REGISTER', 'APPEND_TO_REGISTER')


# ---------------------------------------------------------------- control circuits (kickmix builder)

def build(kind):
    b = km.CircuitBuilder()
    n = 24 if kind.endswith('_24') else 12
    gf = km.GF2Field(n)
    a = b.create_quantum_register(n, name='A')
    x = b.create_quantum_register(n, name='B')
    t = b.create_quantum_register(n, name='T')
    y = b.create_quantum_register(n, name='Y')
    z = b.create_quantum_register(n, name='Z')
    c = b.create_quantum_register(1, name='C')
    if kind in ('gf_mul', 'gf_mul_24'):
        b.ixor_gf2_mul(a, x, target=t, field=gf)
    elif kind == 'init_del_gf2_mul':
        r = b.init_gf2_mul(a, x, field=gf)
        b.del_gf2_mul(a, x, target=r, field=gf)
    elif kind == 'controlled_gf_mul':
        b.ixor_gf2_mul(a, x, target=t, field=gf, control=c[0])
    elif kind == 'two_gf_mul':
        b.ixor_gf2_mul(a, x, target=t, field=gf)
        b.ixor_gf2_mul(y, z, target=t, field=gf)
    elif kind == 'chained_gf_mul':
        b.ixor_gf2_mul(a, x, target=t, field=gf)
        b.ixor_gf2_mul(t, y, target=z, field=gf)
    elif kind == 'controlled_gf2_iadd':
        b.gf2_iadd(a, target=t, field=gf, control=c[0])
    elif kind == 'zero_test_12':
        b.flip_if_equal(x, 0, target=c[0])
    elif kind == 'gf_mul_cx_mixed_operand':
        b.cx(y, a)
        b.ixor_gf2_mul(a, x, target=t, field=gf)
    elif kind == 'gf_mul_by_own_copy':
        b.cx(a, z)
        b.ixor_gf2_mul(a, z, target=t, field=gf)
    elif kind in ('truncated_product_12', 'truncated_product_24'):
        for i in range(n):
            for j in range(n - i):
                b.ccx(a[i], x[j], t[i + j])
    else:
        raise ValueError(kind)
    return b.finish_circuit()


def kmx_lines(circ, tmp, name):
    p = Path(tmp) / f'{name}.kmx'
    circ.to_file(str(p), format='kmx')
    lines = [s.split() for s in p.read_text().splitlines()]
    return p, [s for s in lines if s and s[0] not in SKIP]


def skeleton(path, tmp, name):
    npz = Path(tmp) / f'{name}.npz'
    kmx_skeleton.main(str(path), str(npz))
    with np.load(npz) as z:
        return {k: z[k] for k in z.files}


def components(lines, n_tof, restart):
    seg = KS.Seg(0, n_tof, 'control', 0, 0)
    seg.lines = lines
    recs = KS.analyse(seg, np.random.default_rng(KS.SEED), restart)
    comps, gate_comp, conflicts, bad = KS.colour(recs)
    gates = {}
    for g in gate_comp:
        if g is not None:
            gates[g] = gates.get(g, 0) + 1
    out = sorted(([min(len(A), len(B)), max(len(A), len(B)), gates.get(rt, 0), rt not in bad]
                  for rt, (A, B) in comps.items()), reverse=True)
    nonaff = sum(1 for r in recs if r[0] == 0 and not (r[1][0] and r[2][0]))
    return {'components_minW_maxW_toffoli_bipartite': out, 'nonaffine_control_gates': nonaff,
            'conflicts': conflicts}


def semantic_controls(tmp):
    templates = {}
    for kind in ('gf_mul', 'controlled_gf_mul'):
        p, _ = kmx_lines(build(kind), tmp, 'tpl_' + kind)
        s = skeleton(p, tmp, 'tpl_' + kind)
        templates[kind] = P.relabel(s['op'], s['a'], s['b'], s['c'])
    res = {'template_toffoli': {k: len(v) for k, v in templates.items()}, 'builds': {}}
    for kind in ('gf_mul', 'init_del_gf2_mul', 'controlled_gf_mul', 'two_gf_mul', 'chained_gf_mul',
                 'controlled_gf2_iadd', 'zero_test_12', 'gf_mul_cx_mixed_operand', 'gf_mul_by_own_copy'):
        circ = build(kind)
        n_tof = int(circ.operation_statistics().num_toffoli_like)
        p, lines = kmx_lines(circ, tmp, kind)
        s = skeleton(p, tmp, kind)
        n_skel = len(s['op'])
        r = {'num_toffoli_like': n_tof, 'skeleton_toffoli_like': n_skel,
             'fingerprint_hits': {k: len(P.find(t, s['op'], s['a'], s['b'], s['c'])) for k, t in templates.items()},
             'plain': components(lines, n_skel, False), 'restart': components(lines, n_skel, True)}
        res['builds'][kind] = r
        print(json.dumps({kind: {'n': n_tof, 'fp': r['fingerprint_hits'],
                                 'plain': r['plain']['components_minW_maxW_toffoli_bipartite'][:4],
                                 'restart': r['restart']['components_minW_maxW_toffoli_bipartite'][:4]}}), flush=True)
    return res


def field_controls(tmp):
    res = {}
    rng = np.random.default_rng(5005)
    for kind in ('gf_mul', 'truncated_product_12', 'gf_mul_24', 'truncated_product_24'):
        _, lines = kmx_lines(build(kind), tmp, 'ft_' + kind)
        r = FT.test_segment(lines, lines, rng)
        r.pop('A_qubits', None)
        r.pop('B_qubits', None)
        res[kind] = r
        print(json.dumps({kind: r}), flush=True)
    return res


# ---------------------------------------------------------------- jet skeleton occurrences

JET_ONLY = ['extract/inverse24 scalar/inverse12 norm', 'extract/inverse24 scalar/inverse12 products',
            'extract/inverse24 products', 'unextract/reverse start inverse with flag',
            'unextract/reverse cached phase inverse']


def jet_skeletons(d):
    paths = json.loads(str(d['meta']))['paths']
    p, op, a, b, c = d['path'], d['op'], d['a'], d['b'], d['c']
    out = {}
    for name in JET_ONLY:
        pid = paths.index(name)
        idx = np.nonzero(p == pid)[0]
        s = int(idx[0])
        e = s
        while e < len(p) and p[e] == pid:
            e += 1
        t = P.relabel(op[s:e], a[s:e], b[s:e], c[s:e])
        hits = P.find(t, op, a, b, c)
        inside = sum(1 for h in hits if (p[h:h + len(t)] == pid).all())
        out[name] = {'template_toffoli': len(t), 'tag_static_toffoli': int(len(idx)),
                     'occurrences_whole_circuit': len(hits), 'occurrences_inside_tag': inside}
    print(json.dumps({'jets': out}), flush=True)
    return out


# ---------------------------------------------------------------- 126-Toffoli kernels

def null_combo(rows):
    """Returns a nonzero bitmask m with XOR of rows[j] over set bits of m equal to 0, or None."""
    basis = []  # (pivot value, combo)
    for j, r in enumerate(rows):
        cmb = 1 << j
        for v, m in basis:
            if r ^ v < r:
                r ^= v
                cmb ^= m
        if r == 0:
            return cmb
        basis.append((r, cmb))
        basis.sort(reverse=True)
    return None


def side_test(lines, V, Pq, Qq, rng, n_samples):
    m = len(Pq)
    basis = [1 << k for k in range(m)]
    pv = np.array([0] + basis + rng.integers(1, 1 << m, size=n_samples).tolist(), dtype=np.int64)
    qv = np.array([0] + [1 << j for j in range(len(Qq))], dtype=np.int64)
    nq = len(qv)
    x0 = {q: bool(rng.integers(0, 2)) for q in V}
    st, L = FT.evaluate(lines, V, Pq, Qq, x0, pv, qv)
    out = FT.outputs(st, V, L)
    F = lambda i, j: out[i * nq + j]
    ranks, witness = [], None
    for i in range(1, len(pv)):
        rows = [F(i, j) ^ F(i, 0) ^ F(0, j) ^ F(0, 0) for j in range(1, nq)]
        r = FT.gf2_rank(rows)
        ranks.append(r)
        if r < len(Qq) and witness is None:
            witness = (int(pv[i]), null_combo(rows))
    basis_ranks = ranks[:m]
    sampled = ranks[m:]
    res = {'side_width': m, 'other_width': len(Qq), 'basis_vector_ranks': basis_ranks,
           'sampled_nonzero_operands': n_samples, 'sampled_min_rank': min(sampled),
           'sampled_rank_deficient': sum(1 for r in sampled if r < len(Qq))}
    if witness is not None:
        a, bm = witness
        checks = []
        for trial in range(2):
            x0 = {q: bool(rng.integers(0, 2)) for q in V}
            st, L = FT.evaluate(lines, V, Pq, Qq, x0, np.array([0, a], np.int64), np.array([0, bm], np.int64))
            o = FT.outputs(st, V, L)
            checks.append(o[3] ^ o[2] ^ o[1] ^ o[0] == 0)
        res['witness'] = {'operand_on_this_side': hex(a), 'operand_on_other_side': hex(bm),
                          'B_is_zero_at_two_random_x0': checks}
    return res


def kernels_126(d, semj, kmx, ks=(1856, 2807, 2856), n_samples=16384):
    line = d['line']
    sem = json.loads(Path(semj).read_text())
    segs = {s['k']: s for s in sem['segments'] if s['k'] in ks}
    ranges = {}
    for k, s in segs.items():
        end_all = int(line[s['end']]) - 1 if s['end'] < len(line) else s['lines'][1]
        ranges[k] = (s['lines'][0], s['lines'][1], end_all)
    bufs = {k: ([], []) for k in ranges}
    last = max(r[2] for r in ranges.values())
    with lzma.open(kmx, 'rt', encoding='utf-8') as f:
        for ln, text in enumerate(f):
            if ln > last:
                break
            for k, (lo, hi_t, hi_a) in ranges.items():
                if lo <= ln <= hi_a:
                    parts = text.split()
                    if parts[0] in SKIP:
                        continue
                    bufs[k][1].append(parts)
                    if ln <= hi_t:
                        bufs[k][0].append(parts)
    rng = np.random.default_rng(126)
    out = {}
    for k in ks:
        bt, ba = bufs[k]
        n_tof = sum(1 for p in bt if p[0] in ('CCX', 'CCZ', 'CSWAP'))
        seg = KS.Seg(0, n_tof, 'x', 0, 0)
        seg.lines = bt
        recs = KS.analyse(seg, rng)
        comps, _, conflicts, _ = KS.colour(recs)
        big = max(comps.values(), key=lambda AB: len(AB[0]) * len(AB[1]))
        Aq, Bq = sorted(q for _, q in big[0]), sorted(q for _, q in big[1])
        V = sorted({int(t[1:]) for p in ba for t in p[1:] if t.startswith('q')})
        r = {'label': segs[k]['label'], 'n_toffoli': n_tof, 'A': len(Aq), 'B': len(Bq), 'conflicts': conflicts,
             'n_components': len(comps), 'lines': [ranges[k][0], ranges[k][2]],
             'fix_A': side_test(ba, V, Aq, Bq, rng, n_samples), 'fix_B': side_test(ba, V, Bq, Aq, rng, n_samples)}
        r['zero_divisor_found'] = 'witness' in r['fix_A'] or 'witness' in r['fix_B']
        out[str(k)] = r
        print(json.dumps({k: {x: r[x] for x in ('label', 'n_toffoli', 'A', 'B', 'zero_divisor_found')} |
                          {'A_basis_ranks': r['fix_A']['basis_vector_ranks'],
                           'A_deficient': r['fix_A']['sampled_rank_deficient'],
                           'B_deficient': r['fix_B']['sampled_rank_deficient']}}), flush=True)
    return out


# ---------------------------------------------------------------- field_test.py input check

def field_test_selection(semj, max_per_label):
    sem = json.loads(Path(semj).read_text())
    chosen = {}
    for s in sem['segments']:
        comps = s['components']
        if not comps or not (12 <= comps[0][0] and comps[0][1] <= 32):
            continue
        key = (s['label'], s['end'] - s['start'], tuple(comps[0]))
        if len(chosen.setdefault(key, [])) < max_per_label:
            chosen[key].append(s['k'])
    return sorted(k for v in chosen.values() for k in v)


def field_test_input(semj, here):
    got = [r['segment'] for r in json.loads((here / 'out' / 'field_test.json').read_text())]
    res = {'field_test_json_segments': len(got)}
    for name in (Path(semj).name, 'semantics_restart.json'):
        for mpl in (3, 6):
            sel = field_test_selection(Path(semj).parent / name, mpl)
            res[f'{name}_max_per_label_{mpl}'] = {'segments': len(sel), 'equals_field_test_json': sel == got}
    print(json.dumps({'field_test_input': res}), flush=True)
    return res


def main(skel, semj, kmx, outp):
    here = Path(__file__).resolve().parent.parent
    d = dict(np.load(skel))
    res = {'kickmix_version': __import__('importlib.metadata').metadata.version('kickmix')}
    res['field_test_input'] = field_test_input(semj, here)
    res['jet_skeletons'] = jet_skeletons(d)
    with tempfile.TemporaryDirectory() as tmp:
        res['semantic_controls'] = semantic_controls(tmp)
        res['field_controls'] = field_controls(tmp)
    res['kernels_126'] = kernels_126(d, semj, kmx)
    Path(outp).write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:5])

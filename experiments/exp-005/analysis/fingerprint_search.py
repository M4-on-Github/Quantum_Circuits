"""Searches a dqi Toffoli skeleton for kickmix 1.0.0's own GF(2^12) multiplier structure (exp-005).

Usage: python -I fingerprint_search.py <skeleton.npz> <out.json>

Builds, with kickmix's builder (own code), an isolated GF(2^12) `ixor_gf2_mul` (63 Toffoli) and a
qubit-controlled one (75), extracts their relabelled Toffoli skeletons (patterns.relabel) and counts
non-overlapping occurrences in the given skeleton. As a self-check, the 63-gate core must be found
once inside the controlled build.
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import kickmix as km

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patterns as P  # noqa: E402
import kmx_skeleton  # noqa: E402


def build(kind):
    b = km.CircuitBuilder()
    a = b.create_quantum_register(12, name='A')
    x = b.create_quantum_register(12, name='B')
    t = b.create_quantum_register(12, name='T')
    c = b.create_quantum_register(1, name='C')
    gf = km.GF2Field(12)
    if kind == 'ixor_gf2_mul':
        b.ixor_gf2_mul(a, x, target=t, field=gf)
    elif kind == 'ixor_gf2_mul_controlled':
        b.ixor_gf2_mul(a, x, target=t, field=gf, control=c[0])
    return b.finish_circuit()


def skeleton_of(circ, d, name):
    kmx = Path(d) / f'{name}.kmx'
    npz = Path(d) / f'{name}.npz'
    circ.to_file(str(kmx), format='kmx')
    kmx_skeleton.main(str(kmx), str(npz))
    with np.load(npz) as z:
        return {k: z[k] for k in z.files}


def main(skel_path, out_path):
    d = np.load(skel_path)
    op, a, b, c = d['op'], d['a'], d['b'], d['c']
    out = {'skeleton_toffoli_like': int(len(op)), 'searches': {}}
    with tempfile.TemporaryDirectory() as tmp:
        for kind in ('ixor_gf2_mul', 'ixor_gf2_mul_controlled'):
            circ = build(kind)
            s = skeleton_of(circ, tmp, kind)
            t = P.relabel(s['op'], s['a'], s['b'], s['c'])
            hits = P.find(t, op, a, b, c)
            out['searches'][kind] = {'template_toffoli': len(t),
                                     'num_toffoli_like': int(circ.operation_statistics().num_toffoli_like),
                                     'hits': len(hits)}
            if kind == 'ixor_gf2_mul':
                core = t
        # self-check: the 63-gate core is found inside the controlled build
        s = skeleton_of(build('ixor_gf2_mul_controlled'), tmp, 'self_check')
        out['self_check_core_in_controlled_build'] = len(P.find(core, s['op'], s['a'], s['b'], s['c']))
    Path(out_path).write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == '__main__':
    main(*sys.argv[1:3])

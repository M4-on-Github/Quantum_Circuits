"""Simulate a built circuit on sample x with kickmix and compare phases bit-exactly with
the model; report Q, mean executed Toffolis, rotations and the projected cost.

Ported from marsyas's Apache-2.0 notebook (check.py there; see the package docstring).
change: the model phase is passed in as a function instead of a module global.
"""
from __future__ import annotations

import numpy as np
import kickmix as km

from . import model as M

REFERENCE_COST = 2076774.233715282


def to_bits(v, w):
    return (v[None, :] >> np.arange(w, dtype=np.uint64)[:, None]) & 1 == 1


def from_bits(bits):
    return (bits.astype(np.uint64) << np.arange(len(bits), dtype=np.uint64)[:, None]).sum(axis=0)


def half_turns_to_units(h):
    n, d = h.as_integer_ratio()
    return (((n << 64) // d + 1) >> 1) & M.MASK64


def sim_check(circ, phase_fn, nbatch=16, seed=1, batch=256):
    regs = circ.register_data
    xr = km.array(list(regs['x']))
    xset = set(regs['x'])
    scratch = km.array([km.q(i) for i in range(circ.num_qubits) if km.q(i) not in xset])
    rng = np.random.default_rng(seed)
    sim = km.Simulator(batch_size=batch, seed=seed, debug_print=False, counting_operations=True)
    shots = 0
    for k in range(nbatch):
        xs = rng.integers(1, M.MAX_X + 1, batch, dtype=np.uint64)
        if k == 0:
            edges = [1, 2, 3, M.MAX_X] + [v for p in range(1, 22) for v in (2**p - 1, 2**p, 2**p + 1) if v <= M.MAX_X]
            xs[:len(edges)] = edges
        sim.clear_for_shot()
        sim.write_across_shots(xr, to_bits(xs, 22))
        sim.do(circ)
        assert np.array_equal(from_bits(sim.read_across_shots(xr)), xs), 'x not restored'
        dirty = sim.read_across_shots(scratch).any(axis=1)
        assert not dirty.any(), f'scratch dirty {np.flatnonzero(dirty)[:5]}'
        ph = np.array([half_turns_to_units(sim.read_shot_phase(i)) for i in range(batch)], dtype=np.uint64)
        md = phase_fn(xs.astype(np.int64))
        if not np.array_equal(ph, md):
            i = int(np.flatnonzero(ph != md)[0])
            raise AssertionError(f'mismatch x={xs[i]} circ={ph[i]} model={md[i]}')
        shots += batch
    st = sim.operation_statistics()
    return st.num_toffoli_like / shots, st.num_t_like / shots, st.num_z_pow(min_clifford_hierarchy_level=4) / shots


def report(circ, phase_fn, min_margin, nbatch=16):
    tof, tl, nrot = sim_check(circ, phase_fn, nbatch=nbatch)
    out = {'Q': circ.num_qubits, 'toffoli_sampled_mean': tof, 't': tl, 'rot': nrot,
           'max_toffoli': circ.operation_statistics().num_toffoli_like}
    if min_margin and min_margin > 0:
        T = tl + M.rotation_cost(nrot, min_margin)
        out['C'] = tof + T / 4
        out['cost'] = out['Q'] * out['C']
        out['ratio'] = REFERENCE_COST / out['cost']
    return out

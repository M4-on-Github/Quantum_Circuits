"""Equivalence test for src/kmx_segment_sim.py: segmented vs whole-circuit simulation.

Usage: python test_segsim.py <circuit.kmx> [shots] [seed]
Random inputs on every register (S qubits and E bits), same simulator seed for both runs.
Checks equal Toffoli count, equal final qubits, bits and phases, and that per-path totals add up.
"""
import json
import sys
from pathlib import Path

import numpy as np
import kickmix as km

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
import kmx_segment_sim as seg  # noqa: E402

kmx = sys.argv[1]
shots = int(sys.argv[2]) if len(sys.argv) > 2 else 256
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 12345
c = km.Circuit.from_file(kmx, format='kmx')
rng = np.random.default_rng(seed)
regs = c.register_data
inputs = {name: rng.integers(0, 2, size=(len(list(r)), shots)).astype(bool) for name, r in regs.items()}
for name in inputs:  # zero half of the E registers so classically conditioned blocks get skipped
    if name.startswith("E"):
        inputs[name] &= rng.random(shots) < 0.5


def fresh():
    sim = km.Simulator(batch_size=shots, counting_operations=True, seed=seed)
    sim.use_same_registers_as(c)
    for name, r in regs.items():
        sim.write_across_shots(km.array(list(r)), inputs[name])
    return sim


def state(sim):
    qs = sim.read_across_shots(km.array([km.q(k) for k in range(c.num_qubits)]))
    bs = sim.read_across_shots(km.array([km.b(k) for k in range(c.num_bits)])) if c.num_bits else None
    return qs, bs, sim.read_phase_flipped_across_shots()


a = fresh()
a.do(c)
full_tof = int(a.operation_statistics().num_toffoli_like)
sa = state(a)
b = fresh()
res = seg.run_segmented(kmx, b, km=km)
sb = state(b)
out = {
    'full_toffoli': full_tof,
    'seg_toffoli': res['total_executed_toffoli'],
    'qubits_equal': bool(np.array_equal(sa[0], sb[0])),
    'bits_equal': bool(sa[1] is None or np.array_equal(sa[1], sb[1])),
    'phase_equal': bool(np.array_equal(sa[2], sb[2])),
    'per_path_sum_x_shots': sum(res['per_shot_by_path'].values()) * shots,
    'static_total': c.operation_statistics().num_toffoli_like,
    'segments': res['segments'],
    'inexact_fraction': res['inexact_executed_fraction'],
    'uncond_mismatches': res['uncond_segment_mismatches'],
    'top_paths': dict(list(res['per_shot_by_path'].items())[:8]),
}
print(json.dumps(out, indent=1))
ok = (out['full_toffoli'] == out['seg_toffoli'] and out['qubits_equal'] and out['bits_equal']
      and out['phase_equal'] and abs(out['per_path_sum_x_shots'] - full_tof) < 1e-6 * max(1, full_tof)
      and not out['uncond_mismatches'])
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)

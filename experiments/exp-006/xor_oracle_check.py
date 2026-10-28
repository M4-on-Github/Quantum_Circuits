"""exp-006: which target-register promise do the downloaded ANGLE_k circuits need?

python -I xor_oracle_check.py <label> <stage_dir> <verifiers_dir> <out_json> [shots_per_address]

For every circuit k, on all valid addresses a < 76 + R*B, with z drawn per shot from
  mode "random":   uniform random 8-bit words in all J target registers;
  mode "sign":     random words whose top two bits are equal (the sign-canonical set,
                   which contains every state the verifier's traversal reaches);
  mode "zero":     z = 0 (the verifier's first-circuit input).
it runs the circuit once in kickmix's simulator and checks: no phase flip, selection unchanged,
workspace back to 0, and words == z XOR delta_k(a), with delta_k from the npz `angle_words`
(batch k XOR batch k-1). Reports the fraction of failing shots per check.
Circuits are loaded only via kickmix.Circuit.from_file; the npz only via numpy(allow_pickle=False).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np


def main() -> None:
    label, stage, verifiers, out_json = sys.argv[1:5]
    S = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    sys.path.insert(0, str(Path(verifiers).resolve()))
    import kickmix as km
    from dfthcsos.scoreinfra.circuits import register_layout

    stage = Path(stage)
    with np.load(stage / "submission.npz", allow_pickle=False) as z:
        words = z["angle_words"].astype(np.int64)
    A, n_ang = words.shape
    circuits = []
    k = 0
    while (stage / f"angle_k_{k}.kmb").is_file():
        circuits.append(km.Circuit.from_file(str(stage / f"angle_k_{k}.kmb"), format="kmb"))
        k += 1
    layout = register_layout(circuits)
    J, brot = layout.batch_size, layout.brot
    K = len(circuits)
    padded = np.zeros((A, K * J), dtype=np.int64)
    padded[:, :n_ang] = words
    batches = padded.reshape(A, K, J)
    rng = np.random.default_rng(20261028)
    shots = A * S
    addresses = np.tile(np.arange(A, dtype=np.int64), S)
    addr_bits = ((addresses[None, :] >> np.arange(len(layout.selection))[:, None]) & 1).astype(bool)
    place = np.int64(1) << np.arange(brot, dtype=np.int64)
    public = layout.public_qubits
    results = []
    t0 = time.time()
    for k, c in enumerate(circuits):
        delta = batches[:, k, :] ^ (batches[:, k - 1, :] if k else 0)
        delta_t = np.tile(delta, (S, 1))
        sign_canonical_delta = bool(np.all(((delta >> (brot - 1)) & 1) == ((delta >> (brot - 2)) & 1)))
        work = km.array([km.q(i) for i in range(c.num_qubits) if i not in public])
        row = {"k": k, "delta_sign_canonical": sign_canonical_delta}
        for mode in ("zero", "sign", "random"):
            if mode == "zero":
                zw = np.zeros((shots, J), dtype=np.int64)
            else:
                zw = rng.integers(0, 1 << brot, size=(shots, J), dtype=np.int64)
                if mode == "sign":
                    top = (zw >> (brot - 2)) & 1
                    zw = (zw & ~(np.int64(1) << (brot - 1))) | (top << (brot - 1))
            sim = km.Simulator(batch_size=shots, debug_print=False, seed=int(rng.integers(1 << 62)),
                               counting_operations=True)
            sim.use_same_registers_as(c)
            sim.write_across_shots(layout.selection, addr_bits)
            for j, w in enumerate(layout.words):
                sim.write_across_shots(w, ((zw[:, j][None, :] >> np.arange(brot)[:, None]) & 1).astype(bool))
            sim.do(c)
            phase = np.asarray(sim.read_phase_flipped_across_shots(), dtype=bool)
            sel_bad = np.any(np.asarray(sim.read_across_shots(layout.selection)) != addr_bits, axis=0)
            work_bad = np.any(np.asarray(sim.read_across_shots(work)), axis=0) if len(work) else np.zeros(shots, bool)
            got = np.stack([place @ np.asarray(sim.read_across_shots(w)).astype(np.int64) for w in layout.words], axis=1)
            word_bad = np.any(got != (zw ^ delta_t), axis=1)
            any_bad = phase | sel_bad | work_bad | word_bad
            row[mode] = {"shots": shots, "fail_frac": float(any_bad.mean()), "phase": float(phase.mean()),
                         "selection": float(sel_bad.mean()), "workspace": float(work_bad.mean()),
                         "words": float(word_bad.mean()),
                         "mean_toffoli_per_shot": sim.operation_statistics().num_toffoli_like / shots}
        results.append(row)
        print(k, {m: row[m]["fail_frac"] for m in ("zero", "sign", "random")}, flush=True)
    out = {"label": label, "addresses": A, "shots_per_address": S, "J": J, "brot": brot,
           "rng_seed": 20261028, "runtime_s": round(time.time() - t0, 1), "per_circuit": results}
    Path(out_json).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

"""exp-007 probes P1-P4 on the official ANGLE_k checking path (small synthetic table).

Run from anywhere:  .venv/Scripts/python.exe -B experiments/exp-007/probes.py
Writes experiments/exp-007/probes_result.json and scratch circuits under
experiments/exp-007/out/ (gitignored).

The checking path is the unmodified data/verifiers/dfthcsos/scoreinfra/circuits.py:
recover_words_from_circuits (forward + reverse simulation, state checks, dynamic
Toffoli count) and load_circuits / read_circuit_family (file discovery).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data" / "verifiers"))
sys.path.insert(0, str(REPO / "src"))

import kickmix as km  # noqa: E402
from dfthcsos.scoreinfra.circuits import (  # noqa: E402
    InvalidCircuits,
    load_circuits,
    recover_words_from_circuits,
)
from angleload.qrom import SELECTION, angle_deltas, word_name  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "probes"

# Small synthetic table: A addresses (not a power of two), N_ANGLES words per row.
A, N_ANGLES, J, BROT = 37, 5, 2, 4
TABLE_SEED = 7
SEEDS = [0, 12345]
P2_PAIRS = 1000


def table() -> np.ndarray:
    rng = np.random.default_rng(TABLE_SEED)
    return rng.integers(0, 2**BROT, size=(A, N_ANGLES), dtype=np.int64)


def padded_ints(delta: np.ndarray, n: int) -> list[int]:
    """Rows of an (A, J) word table as little-endian ints over the J*brot word bits, padded to 2**n."""
    vals = [sum(int(delta[a, j]) << (j * BROT) for j in range(delta.shape[1])) for a in range(delta.shape[0])]
    return vals + [0] * ((1 << n) - len(vals))


def batches(words: np.ndarray) -> np.ndarray:
    """(K, A, J) zero-padded batches."""
    K = -(-N_ANGLES // J)
    padded = np.zeros((A, K * J), dtype=np.int64)
    padded[:, :N_ANGLES] = words
    return padded.reshape(A, K, J).transpose(1, 0, 2)


def new_builder():
    b = km.CircuitBuilder()
    n = (A - 1).bit_length()
    sel = b.create_quantum_register(n, SELECTION)
    regs = [b.create_quantum_register(BROT, word_name(j)) for j in range(J)]
    flat = km.array([q for r in regs for q in r])  # word_0 bits 0.., word_1 bits 0..: little endian over J*brot
    return b, sel, regs, flat, n


def p1_family(words: np.ndarray, p2_pairs: int = 0) -> list[km.Circuit]:
    """ANGLE_k = init_lookup(delta_k -> clean ancilla), CX ancilla -> words, del_lookup(ancilla)."""
    circuits = []
    for k, delta in enumerate(angle_deltas(words, J)):
        b, sel, regs, flat, n = new_builder()
        tab = padded_ints(delta, n)
        anc = b.alloc_qubits(J * BROT)
        b.init_lookup(table=tab, address=sel, target=anc)
        for i in range(J * BROT):
            b.cx(anc[i], flat[i])
        b.del_lookup(table=tab, address=sel, target=anc)
        b.free(anc)
        if k == 0 and p2_pairs:
            q = b.alloc_qubits(2)
            m = b.alloc_bits(1)[0]
            b.hmr(q[0], m)  # q[0] is |0>: random outcome, no phase kickback
            b.push_condition(m)
            for _ in range(p2_pairs):
                b.ccx(sel[0], sel[1], q[1])
                b.ccx(sel[0], sel[1], q[1])
            b.pop_condition()
            b.free(q)
            b.free(m)
        circuits.append(b.finish_circuit())
    return circuits


def p3_family(words: np.ndarray) -> list[km.Circuit]:
    """C-012 literal: ANGLE_k = MBU-clear the words assuming they hold batch[k-1], then load batch[k]."""
    bat = batches(words)
    circuits = []
    for k in range(bat.shape[0]):
        b, sel, regs, flat, n = new_builder()
        if k > 0:
            b.del_lookup(table=padded_ints(bat[k - 1], n), address=sel, target=flat)
        b.init_lookup(table=padded_ints(bat[k], n), address=sel, target=flat)
        circuits.append(b.finish_circuit())
    return circuits


def static(circuits) -> list[int]:
    return [int(c.operation_statistics().num_toffoli_like) for c in circuits]


def check(circuits, seed: int) -> dict:
    t0 = time.perf_counter()
    try:
        recovered, layout, tof = recover_words_from_circuits(
            circuits, num_vectors=A, num_angles=N_ANGLES, seed=seed
        )
        ok = bool(np.array_equal(recovered, table()))
        return {"status": "PASS", "words_match_table": ok, "toffoli_dynamic_both_passes": float(tof),
                "runtime_s": round(time.perf_counter() - t0, 3)}
    except InvalidCircuits as exc:
        return {"status": "FAIL", "error": str(exc), "runtime_s": round(time.perf_counter() - t0, 3)}


def write_dir(circuits, d: Path, extra: dict[str, km.Circuit] | None = None) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.kmb"):
        f.unlink()
    for k, c in enumerate(circuits):
        c.to_file(d / f"angle_k_{k}.kmb", format="kmb")
    for name, c in (extra or {}).items():
        c.to_file(d / name, format="kmb")
    return d


def main() -> None:
    words = table()
    res: dict = {"table": {"A": A, "n_angles": N_ANGLES, "J": J, "brot": BROT, "seed": TABLE_SEED,
                           "shots_per_address": 64}, "kickmix": None}
    from importlib.metadata import version
    res["kickmix"] = version("kickmix")

    p1 = p1_family(words)
    res["P1"] = {"num_qubits": [int(c.num_qubits) for c in p1], "static": static(p1),
                 "static_both_passes": 2 * sum(static(p1)),
                 "runs": {str(s): check(p1, s) for s in SEEDS}}

    p2 = p1_family(words, p2_pairs=P2_PAIRS)
    runs = {str(s): check(p2, s) for s in SEEDS}
    for s, r in runs.items():
        if r["status"] == "PASS" and res["P1"]["runs"][s]["status"] == "PASS":
            extra = r["toffoli_dynamic_both_passes"] - res["P1"]["runs"][s]["toffoli_dynamic_both_passes"]
            r["extra_dynamic_vs_P1"] = extra
            r["implied_condition_fraction"] = extra / (2 * 2 * P2_PAIRS)
    res["P2"] = {"num_qubits": [int(c.num_qubits) for c in p2], "static": static(p2),
                 "static_both_passes": 2 * sum(static(p2)),
                 "extra_static_both_passes": 2 * (sum(static(p2)) - sum(static(p1))),
                 "runs": runs}

    p3 = p3_family(words)
    res["P3"] = {"num_qubits": [int(c.num_qubits) for c in p3], "static": static(p3),
                 "runs": {str(s): check(p3, s) for s in SEEDS}}

    # P4(a): K forward circuits followed by K "uncompute" circuits (here: the same P1 circuits reversed).
    d4a = write_dir(p1 + p1[::-1], OUT / "p4a")
    fam4a = load_circuits(d4a)
    res["P4a"] = {"files": sorted(f.name for f in d4a.glob("*.kmb")), "loaded": len(fam4a),
                  "run": check(list(fam4a), SEEDS[0])}
    # P4(b): P1 family plus an extra differently named "dagger" file.
    d4b = write_dir(p1, OUT / "p4b", extra={"angle_k_0_dag.kmb": p3[0]})
    fam4b = load_circuits(d4b)
    res["P4b"] = {"files": sorted(f.name for f in d4b.glob("*.kmb")), "loaded": len(fam4b),
                  "loaded_equal_P1": all(x == y for x, y in zip(fam4b, p1)) and len(fam4b) == len(p1),
                  "run": check(list(fam4b), SEEDS[0])}

    (HERE / "probes_result.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

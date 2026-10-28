"""exp-007 P5: build the full-size reference family with an MBU section in every circuit.

  .venv/Scripts/python.exe -B experiments/exp-007/build_p5.py

1. Checks that `angleload.mbu.emit_qrom_xor` with the word bits as targets emits
   the same circuit (`==`) as `angleload.qrom.build_qrom_circuit` for every k of
   the sample table (so the MBU variant differs from the reference only in the
   MBU section).
2. Checks `build_mbu_section_family` on a small synthetic table with the official
   `recover_words_from_circuits`.
3. Builds P5 from the sample `submission.npz` angle_words (brot 12, J 8):
   word_7 bits 0..3 go through a clean 4-qubit ancilla and `emit_mbu_clear`.
   Writes out/p5/angle_k_*.kmb plus a copy of the sample submission.npz, and
   p5_build.json (widths, static Toffoli counts, file hashes).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data" / "verifiers"))
sys.path.insert(0, str(REPO / "src"))

import kickmix as km  # noqa: E402
from dfthcsos.scoreinfra.circuits import recover_words_from_circuits  # noqa: E402
from angleload.qrom import SELECTION, angle_deltas, build_family, word_name  # noqa: E402
from angleload.mbu import build_mbu_section_family, emit_qrom_xor, word_bit_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
SAMPLE_NPZ = REPO / "data" / "sample_submission" / "dfthcsos" / "submission.npz"
OUT = HERE / "out" / "p5"
BROT, J, MBU_WORD, MBU_BITS = 12, 8, 7, 4


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    rec: dict = {"brot": BROT, "J": J, "mbu_word": MBU_WORD, "mbu_bits": MBU_BITS}
    words = np.load(SAMPLE_NPZ, allow_pickle=False)["angle_words"]
    rec["angle_words_shape"] = list(words.shape)

    # 1. emitter equivalence with the reference port.
    t0 = time.perf_counter()
    ref = build_family(words, BROT, J)
    same = []
    for k, delta in enumerate(angle_deltas(words, J)):
        b = km.CircuitBuilder()
        A = delta.shape[0]
        n = (A - 1).bit_length()
        sel = b.create_quantum_register(n, SELECTION)
        regs = [b.create_quantum_register(BROT, word_name(j)) for j in range(J)]
        targets = [regs[j][bit] for j in range(J) for bit in range(BROT - 1, -1, -1)]
        emit_qrom_xor(b, sel, word_bit_rows(delta, BROT), targets)
        same.append(bool(b.finish_circuit() == ref[k]))
    rec["emitter_equals_reference_per_k"] = same
    rec["emitter_check_s"] = round(time.perf_counter() - t0, 2)

    # 2. small synthetic check on the official checking path.
    rng = np.random.default_rng(11)
    small = rng.integers(0, 2**6, size=(45, 13), dtype=np.int64)
    fam = build_mbu_section_family(small, 6, 3, word=2, nbits=3)
    got, _, tof = recover_words_from_circuits(fam, num_vectors=45, num_angles=13, seed=0)
    rec["small_check"] = {"A": 45, "n_angles": 13, "brot": 6, "J": 3, "word": 2, "nbits": 3,
                          "passed": bool(np.array_equal(got, small)), "toffoli_dynamic_both_passes": float(tof),
                          "static_both_passes": 2 * sum(int(c.operation_statistics().num_toffoli_like) for c in fam)}

    # 3. full-size P5 family.
    t0 = time.perf_counter()
    p5 = build_mbu_section_family(words, BROT, J, MBU_WORD, MBU_BITS)
    rec["build_s"] = round(time.perf_counter() - t0, 2)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("angle_k_*"):
        f.unlink()
    files = []
    for k, c in enumerate(p5):
        p = OUT / f"angle_k_{k}.kmb"
        c.to_file(p, format="kmb")
        files.append({"k": k, "num_qubits": int(c.num_qubits),
                      "static_toffoli": int(c.operation_statistics().num_toffoli_like),
                      "ref_static_toffoli": int(ref[k].operation_statistics().num_toffoli_like),
                      "ref_num_qubits": int(ref[k].num_qubits),
                      "sha256": sha(p)})
    shutil.copyfile(SAMPLE_NPZ, OUT / "submission.npz")
    rec["files"] = files
    rec["static_both_passes"] = 2 * sum(f["static_toffoli"] for f in files)
    rec["ref_static_both_passes"] = 2 * sum(f["ref_static_toffoli"] for f in files)
    rec["max_num_qubits"] = max(f["num_qubits"] for f in files)
    rec["submission_npz_sha256"] = sha(OUT / "submission.npz")
    (HERE / "p5_build.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in rec.items() if k != "files"}, indent=2))
    for f in files:
        print(f["k"], f["num_qubits"], f["static_toffoli"], f["ref_static_toffoli"])


if __name__ == "__main__":
    main()

"""Balanced clean unary-tree QROM loaders for the dfthcsos ANGLE_k family.

Contract (data/verifiers/dfthcsos/SCORING_README.md, "What a submission must do"):
the 75 angle words of each address row are cut into K = ceil(75 / J) batches of
J words (zero padded). Circuit k is the XOR oracle |a>|z> -> |a>|z ^ delta[k, a]>
with delta[0] = batch[0] and delta[k] = batch[k] ^ batch[k-1]. Public registers:
"selection" (exactly ceil(log2(A)) qubits) and "word_0".."word_{J-1}" (brot qubits
each, little endian). Every other qubit is clean workspace.

Construction (one circuit): a balanced segment tree over the address range
[0, 2**n), n = ceil(log2(A)), most significant selection bit first.
- The root split uses the top selection bit itself as the control (negated for the
  lower half), so it costs no ancilla and no Toffoli.
- Every deeper internal node that has addresses on both sides holds the AND of its
  parent's control and its level's selection bit in ancilla[level - 1]:
  init_and(parent, NOT bit) for the left child (1 Toffoli), then CX(parent, anc)
  turns it into parent AND bit for the right child, then del_and uncomputes it by
  measurement (no Toffoli). n - 1 ancillas in total.
- A node whose range lies inside [0, A) and either holds a single address or whose
  rows are all equal to its first row (a constant segment) is a leaf: it XORs that
  row into the word registers with one CX per set bit.
- A node whose right half starts at or beyond A only recurses into its left half
  under the same control.
For A = 3976 with no constant segments this is A - 2 = 3974 Toffolis per circuit.

Lineage, licence and modification notice
----------------------------------------
This module is a derivative work (a port) of the official competition file
data/verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py
(SHA-256 8daccdca69f2d718b0176cd9281803df84a988ea5ac6c167fbb02e461ac2b371),
which is distributed under the Apache License, Version 2.0; the licence text is
data/verifiers/LICENSE.txt (also http://www.apache.org/licenses/LICENSE-2.0).
Any release of this code must ship that licence text.

Modified in this repository (2026-10-28, exp-002):
- Renamed: batch_deltas -> angle_deltas, build_angle_k_circuit ->
  build_qrom_circuit (inner load -> xor_row, node -> visit),
  build_angle_k_family -> build_family, write_kmx_family -> write_family.
  Comments and docstrings rewritten; the command-line entry point and
  load_angle_words are not ported; circuit_stats is added.
- One functional change, the constant-segment leaf test. This port tests rows:
  (delta[lo:hi] == delta[lo]).all(), i.e. every row equals the first row. The
  reference tests one scalar: np.all(delta[lo:hi] == delta[lo, 0]), i.e. every
  word equals the first word of the first row. On the sample angle_words table
  (brot 12, J 8) neither test fires and the output is byte-identical to the
  reference script's. On tables with runs of identical rows the port emits
  fewer Toffolis than the reference; in the exp-002 critic probe both families
  passed the official recover_words_from_circuits check.
The gate emission order is otherwise the reference's.
"""

from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Sequence

import kickmix as km
import numpy as np

SELECTION = "selection"


def word_name(j: int) -> str:
    return f"word_{j}"


def angle_deltas(angle_words: np.ndarray, J: int) -> np.ndarray:
    """(K, A, J) table: delta[k] = batch[k] ^ batch[k-1] of the zero-padded rows."""
    words = np.asarray(angle_words, dtype=np.int64)
    if words.ndim != 2 or (words < 0).any():
        raise ValueError("angle_words must be a non-negative 2-D integer table (A, N-1)")
    A, n_angles = words.shape
    K = max(1, ceil(n_angles / J))
    padded = np.zeros((A, K * J), dtype=np.int64)
    padded[:, :n_angles] = words
    batches = np.ascontiguousarray(padded.reshape(A, K, J).transpose(1, 0, 2))
    deltas = batches.copy()
    deltas[1:] ^= batches[:-1]
    return deltas


def build_qrom_circuit(delta: np.ndarray, brot: int) -> km.Circuit:
    """One ANGLE_k circuit loading the (A, J) table `delta` (words < 2**brot)."""
    delta = np.asarray(delta, dtype=np.int64)
    A, J = delta.shape
    if A < 2:
        raise ValueError("need at least 2 addresses")
    if (delta < 0).any() or (delta >> brot).any():
        raise ValueError(f"words must lie in [0, 2**{brot})")
    n = (A - 1).bit_length()

    b = km.CircuitBuilder()
    sel = b.create_quantum_register(n, SELECTION)
    word_regs = [b.create_quantum_register(brot, word_name(j)) for j in range(J)]
    anc = b.alloc_qubits(n - 1) if n > 1 else []
    msb_first = [sel[n - 1 - i] for i in range(n)]

    # Precompute, per row, the CX targets of that row (word j, bit high -> low).
    def xor_row(row: int, ctrl) -> None:
        r = delta[row]
        for j in range(J):
            v = int(r[j])
            for bit in range(brot - 1, -1, -1):
                if (v >> bit) & 1:
                    b.cx(ctrl, word_regs[j][bit])

    def is_leaf(lo: int, hi: int) -> bool:
        if hi > A:
            return False
        if hi - lo == 1:
            return True
        return bool((delta[lo:hi] == delta[lo]).all())

    def visit(ctrl, level: int, lo: int, hi: int) -> None:
        # Invariant: ctrl is 1 exactly when lo <= address < hi.
        if lo >= A:
            return
        if is_leaf(lo, hi):
            xor_row(lo, ctrl)
            return
        mid = (lo + hi) >> 1
        if mid >= A:
            visit(ctrl, level + 1, lo, mid)
            return
        bit = msb_first[level]
        a = anc[level - 1]
        b.x(bit)
        b.init_and(ctrl, bit, a)  # a = ctrl AND NOT bit  (1 Toffoli)
        b.x(bit)
        visit(a, level + 1, lo, mid)
        b.cx(ctrl, a)  # a = ctrl AND bit
        visit(a, level + 1, mid, hi)
        b.del_and(ctrl, bit, a)  # measurement-based uncompute

    half = 1 << (n - 1)
    top = msb_first[0]
    b.x(top)
    visit(top, 1, 0, half)
    b.x(top)
    visit(top, 1, half, 2 * half)
    return b.finish_circuit()


def build_family(angle_words: np.ndarray, brot: int, J: int) -> list[km.Circuit]:
    return [build_qrom_circuit(d, brot) for d in angle_deltas(angle_words, J)]


def circuit_stats(circuits: Sequence[km.Circuit]) -> list[dict]:
    return [
        {
            "k": k,
            "num_qubits": int(c.num_qubits),
            "toffoli_static": int(c.operation_statistics().num_toffoli_like),
            "num_instructions": len(c),
        }
        for k, c in enumerate(circuits)
    ]


def write_family(circuits: Sequence[km.Circuit], out_dir: str | Path, fmt: str = "kmb") -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("angle_k_*.km[bx]"):
        stale.unlink()
    paths = []
    for k, c in enumerate(circuits):
        p = out_dir / f"angle_k_{k}.{fmt}"
        if fmt == "kmb":
            c.to_file(p, format="kmb")
        else:
            p.write_text(str(c).rstrip("\n") + "\n", encoding="utf-8")
        paths.append(p)
    return paths

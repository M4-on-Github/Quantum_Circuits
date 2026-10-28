"""ANGLE_k variants with a measurement-based uncompute (MBU) section (exp-007).

Builder-level helpers on top of the segment-tree QROM of `qrom.py`:

- `emit_qrom_xor(b, sel, rows, targets)`: the same balanced segment-tree unary
  QROM as `qrom.build_qrom_circuit` (same tree, same gate order, top selection
  bit as a free control, `init_and` / measurement-based `del_and`), but it XORs
  the bit rows `rows[a]` into an arbitrary ordered list of target qubits and
  frees its ladder ancillas afterwards. With `targets` = the word bits in
  `qrom.xor_row` order it emits the reference circuit's gates.
- `emit_mbu_clear(b, sel, num_addresses, rows, qubits)`: clears qubits that hold
  `rows[a]` by measurement: HMR every qubit (outcome bit m_i, phase
  (-1)^(m_i * rows[a, i])), then a phase fix-up by unary iteration over the
  addresses: for each address a and each set bit i of rows[a], a Z on the match
  qubit conditioned on m_i. The fix-up's Toffolis are the unary iteration's;
  the conditioned Z gates are Clifford.
- `build_mbu_section_family(angle_words, brot, J, word, nbits)`: the reference
  family where, in every circuit, the low `nbits` bits of word register `word`
  go through an MBU section instead of being XORed in directly: the QROM XORs
  them into a clean ancilla register (in the same pass), CX copies the ancilla
  into the word bits, and `emit_mbu_clear` uncomputes the ancilla. Same
  function as the reference family, more Toffolis; a legality probe, not an
  optimization.

Lineage: `emit_qrom_xor` re-implements the tree walk of `qrom.py`, itself a port
of the Apache-2.0 data/verifiers/dfthcsos/example_submission/
angle_k_reference_circuit.py (see the notice in qrom.py; the licence text is
data/verifiers/LICENSE.txt). Written 2026-10-28 for exp-007.
"""

from __future__ import annotations

from typing import Sequence

import kickmix as km
import numpy as np

from .qrom import SELECTION, angle_deltas, word_name


def word_bit_rows(delta: np.ndarray, brot: int) -> np.ndarray:
    """(A, J * brot) bool rows in `qrom.xor_row` order: word j, bit brot-1 .. 0."""
    delta = np.asarray(delta, dtype=np.int64)
    A, J = delta.shape
    shifts = np.arange(brot - 1, -1, -1, dtype=np.int64)
    return (((delta[:, :, None] >> shifts[None, None, :]) & 1).astype(bool)).reshape(A, J * brot)


def emit_qrom_xor(b: km.CircuitBuilder, sel, rows: np.ndarray, targets: Sequence) -> None:
    """XOR rows[a] (bool, one column per target qubit) into `targets` for address a."""
    rows = np.asarray(rows, dtype=bool)
    A, width = rows.shape
    if width != len(targets):
        raise ValueError("rows must have one column per target qubit")
    n = len(sel)
    if A < 2 or (A - 1).bit_length() != n:
        raise ValueError("selection width must be ceil(log2(A))")
    anc = b.alloc_qubits(n - 1) if n > 1 else []
    msb_first = [sel[n - 1 - i] for i in range(n)]

    def xor_row(row: int, ctrl) -> None:
        for col in np.flatnonzero(rows[row]):
            b.cx(ctrl, targets[int(col)])

    def is_leaf(lo: int, hi: int) -> bool:
        if hi > A:
            return False
        if hi - lo == 1:
            return True
        return bool((rows[lo:hi] == rows[lo]).all())

    def visit(ctrl, level: int, lo: int, hi: int) -> None:
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
        b.init_and(ctrl, bit, a)
        b.x(bit)
        visit(a, level + 1, lo, mid)
        b.cx(ctrl, a)
        visit(a, level + 1, mid, hi)
        b.del_and(ctrl, bit, a)

    half = 1 << (n - 1)
    top = msb_first[0]
    b.x(top)
    visit(top, 1, 0, half)
    b.x(top)
    visit(top, 1, half, 2 * half)
    if anc:
        b.free(anc)


def emit_mbu_clear(b: km.CircuitBuilder, sel, num_addresses: int, rows: np.ndarray, qubits: Sequence) -> None:
    """Measurement-based uncompute of `qubits`, which hold rows[a] for address a."""
    rows = np.asarray(rows, dtype=bool)
    if rows.shape != (num_addresses, len(qubits)):
        raise ValueError("rows must be (num_addresses, len(qubits))")
    bits = b.alloc_bits(len(qubits))
    for i, q in enumerate(qubits):
        b.hmr(q, bits[i])
    with b.unary_iteration(sel, range(num_addresses)) as it:
        for address, match in it:
            for i in np.flatnonzero(rows[address]):
                b.push_condition(bits[int(i)])
                b.z(match)
                b.pop_condition()
    b.free(bits)


def build_mbu_section_circuit(delta: np.ndarray, brot: int, word: int, nbits: int) -> km.Circuit:
    """One ANGLE_k circuit: XOR delta (A, J) into the words, with the low `nbits`
    bits of word register `word` routed through a clean ancilla and an MBU."""
    delta = np.asarray(delta, dtype=np.int64)
    A, J = delta.shape
    n = (A - 1).bit_length()
    if not (0 <= word < J and 1 <= nbits <= brot):
        raise ValueError("bad word / nbits")
    b = km.CircuitBuilder()
    sel = b.create_quantum_register(n, SELECTION)
    word_regs = [b.create_quantum_register(brot, word_name(j)) for j in range(J)]
    anc = b.alloc_qubits(nbits)

    rows = word_bit_rows(delta, brot)  # columns: word j, bit brot-1..0
    targets = [word_regs[j][bit] for j in range(J) for bit in range(brot - 1, -1, -1)]
    # Re-route the low nbits of `word`: column for (word, bit) -> anc[bit].
    for bit in range(nbits):
        col = word * brot + (brot - 1 - bit)
        targets[col] = anc[bit]
    emit_qrom_xor(b, sel, rows, targets)
    for bit in range(nbits):
        b.cx(anc[bit], word_regs[word][bit])
    anc_rows = np.stack([((delta[:, word] >> bit) & 1).astype(bool) for bit in range(nbits)], axis=1)
    emit_mbu_clear(b, sel, A, anc_rows, list(anc))
    b.free(anc)
    return b.finish_circuit()


def build_mbu_section_family(angle_words: np.ndarray, brot: int, J: int, word: int, nbits: int) -> list[km.Circuit]:
    return [build_mbu_section_circuit(d, brot, word, nbits) for d in angle_deltas(angle_words, J)]


__all__ = [
    "build_mbu_section_circuit",
    "build_mbu_section_family",
    "emit_mbu_clear",
    "emit_qrom_xor",
    "word_bit_rows",
]

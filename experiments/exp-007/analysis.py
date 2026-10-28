"""exp-007: arithmetic for the C-012 conclusion (estimates, not verifier output).

  .venv/Scripts/python.exe -B experiments/exp-007/analysis.py

Enumerates ANGLE_k loader layouts for the reference table (A = 3976 rows, 75
words, brot = 12) under the 128-qubit cap, using the official cost model
(`dfthcsos.verify.heuristic_costs`) for the heuristic part and these per-circuit
Toffoli estimates for the ANGLES part (one pass; the verifier charges 2 passes):

- direct (lambda = 1): the segment-tree unary QROM, A - 2 (measured 3,974 in
  exp-002 for A = 3976). Width 12 + W + (n - 1), W = 12 J.
- select-swap with the target as block 0 and MBU junk uncompute (lambda >= 2):
  swap^-1 (lambda - 1) W CSWAP, unary lookup over ceil(A / lambda) rows
  (ceil(A / lambda) - 2), swap (lambda - 1) W, then a measurement-based
  uncompute of the (lambda - 1) W junk bits (which hold T(a') for the other
  a' sharing a's high part): ceil(A / k) + 2 k with a k-qubit one-hot built in
  the measured junk qubits (k a power of two <= (lambda - 1) W; Berry et al.
  lit-1902.02134 App. C Thm. 3 counts ceil(d / k) + k, +k here for the
  binary-to-unary conversion, cf. kickmix del_lookup = 119 at d = 4096, W = 96).
  Width 12 + lambda W + (ceil(log2(A / lambda)) - 1).

These are my estimates, not built circuits. Writes analysis.json.
"""

from __future__ import annotations

import json
import sys
from math import ceil, log2
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "data" / "verifiers"))
from dfthcsos.verify import heuristic_costs  # noqa: E402

A, N_ANGLES, BROT, CAP = 3976, 75, 12, 128
R, B, C, N = 65, 60, 60, 76
SEL = (A - 1).bit_length()


def mbu_cost(d: int, junk_bits: int) -> tuple[int, int]:
    best = None
    k = 1
    while k <= junk_bits:
        c = ceil(d / k) + 2 * k
        if best is None or c < best[0]:
            best = (c, k)
        k *= 2
    return best


def layout(J: int, lam: int) -> dict:
    W = J * BROT
    K = ceil(N_ANGLES / J)
    if lam == 1:
        per = A - 2
        width = SEL + W + (SEL - 1)
        parts = {"lookup": per}
    else:
        rows = ceil(A / lam)
        swaps = 2 * (lam - 1) * W
        mbu, k = mbu_cost(A, (lam - 1) * W)
        per = (rows - 2) + swaps + mbu
        width = SEL + lam * W + (ceil(log2(rows)) - 1)
        parts = {"lookup": rows - 2, "swaps": swaps, "mbu": mbu, "mbu_k": k}
    h = heuristic_costs(N, R, B, C, BROT)
    angles = 2 * K * per
    t_total = angles + h["toffoli"]
    temp = width - SEL - W
    q_total = h["persistent_qubits"] + W + max(h["temporary_qubits"], temp)
    return {"J": J, "lambda": lam, "K": K, "width": width, "within_cap": width <= CAP,
            "per_circuit_one_pass": per, **parts, "angles_both_passes": angles,
            "T_total": t_total, "Q_total": q_total, "TQ": t_total * q_total}


def main() -> None:
    ref = layout(8, 1)
    rows = []
    for J in range(1, 9):
        for lam in (1, 2, 4, 8):
            r = layout(J, lam)
            r["TQ_vs_reference"] = r["TQ"] / ref["TQ"]
            rows.append(r)
    feasible = [r for r in rows if r["within_cap"]]
    best = min(feasible, key=lambda r: r["TQ"])
    # Hypothetical (not allowed by the verifier): only reverse ANGLE_0 is a pure uncompute.
    hypo = {"reverse_angle0_del_lookup_static": 119, "saving_per_family": (A - 2) - 119,
            "saving_frac_of_angles": ((A - 2) - 119) / ref["angles_both_passes"],
            "saving_frac_of_T_total": ((A - 2) - 119) / ref["T_total"]}
    out = {"reference": ref, "layouts": rows, "best_feasible": best,
           "hypothetical_direction_specific_reverse": hypo}
    (Path(__file__).resolve().parent / "analysis.json").write_text(json.dumps(out, indent=2) + "\n")
    print("J lam K width cap per_circuit angles T_total Q_total TQ/ref")
    for r in feasible:
        print(r["J"], r["lambda"], r["K"], r["width"], r["within_cap"], r["per_circuit_one_pass"],
              r["angles_both_passes"], r["T_total"], r["Q_total"], round(r["TQ_vs_reference"], 4))
    print("best", best["J"], best["lambda"], round(best["TQ_vs_reference"], 4))
    print("hypothetical", hypo)


if __name__ == "__main__":
    main()

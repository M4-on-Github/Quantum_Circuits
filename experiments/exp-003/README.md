---
id: exp-003
title: dqi Toffoli accounting by subroutine on the sample circuit (multiplier cost, inversion share, per-shot)
task: dqi
tests: [C-006, C-005]
direction: D-001
status: planned
date: 2026-10-28
commit: pending
result: pending
---

## Hypothesis

C-006 (knowledge/claims.md) says that a 51-Toffoli GF(2^12) multiplier, used instead of the 63-Toffoli Karatsuba, cuts dqi T by up to about 12% at equal Q. Two premises open that claim:
- (i) the sample dqi circuit does not already use a 51-Toffoli multiplier;
- (ii) enough multiplies execute per shot (about 58k per lit-2510.10967 §V.2) for a 12-Toffoli saving each to matter.

C-005 needs the per-shot Toffoli share of the Forney-step inversions. lit-2610.23832 notes estimate it at about 1.44M of 5.73M (4,095 × 351).

This is an accounting experiment. No circuit is changed. The sample `dqi.kmb` (exp-001: Q 1,893, static 5,725,461, per-shot mean 5,725,108.38) is decomposed by subroutine.

## Prediction

Made before any count of the full-size sample circuit. Sources for the numbers:
- **Isolated kickmix 1.0.0 primitive costs**, built locally at degree 12:
  - `ixor_gf2_mul` / `init_gf2_mul`: 63 Toffoli.
  - Qubit-controlled `ixor_gf2_mul`: 75 (63 + 12).
  - `init_gf2_inverse_with_scaffold`: 315 (48 scaffold qubits); the matching `del_*` costs 0.
  - `init_gf2_div_with_scaffold`: 378.
  - `gf2_phase_by_product` and constant `gf2_imul`: 0.
- **A tiny generator build** (`dqi_reference_circuit.py`, m = 20, n = 6) run through `src/kmx_tag_count.py`. Every tagged `gf_mul` was 63, `c_gf_mul` 75, `gf_inverse_chain` 315, `gf_div` 378, `quotient_div` 390 and `forney_step` 351. The only conditioned Toffolis were in `forney_step`, under `PUSH_CONDITION` on a bit equal to the OR of the 12 bits of E_j.
- **Instance counts** from the generator's loops at (m, n, b) = (4095, 70, 12): 73 registers, 222 EEA steps per direction, 444 in total. In `sweep_positions` the multiply runs at all 73 positions, except position 1 at iterations 0 and 1.

The predictions assume that the sample is what the kickmix 1.0.0 generator produces.

| Quantity | Prediction (static) | Prediction (per shot, expected) |
|---|---|---|
| Toffolis per `gf_mul` instance | 63 for every instance, no 51 | same |
| `c_gf_mul` (EEA sweep, qubit-controlled) | 32,408 instances × 75 = 2,430,600 | same (not classically conditioned) |
| `quotient_div` (EEA, 2 per step) | 888 × 390 = 346,320 (`gf_div` 378 + controlled add 12) | same |
| `forney_step` | 4,095 × 351 = 1,437,345 | × 4095/4096 = 1,436,994.1 |
| `gf_inverse_chain`, all | 4,983 × 315 = 1,569,645 (27.4%) | 1,569,330.1 |
| `gf_inverse_chain`, Forney only | 4,095 × 315 = 1,289,925 (22.5%) | 1,289,610.1 (22.5%) |
| `gf_mul`, all instances (incl. 5 per inversion chain, 1 per division, 1 per `c_gf_mul`) | 32,408 + 888 + 5 × 4,983 = 58,211 × 63 = 3,667,293 (64.1%) | 58,206.0 multiplies, 3,666,978 Toffoli |
| everything else (unary iteration, cswaps, comparators, adders, swap_a_and_b) | 5,725,461 − above = 1,511,196 (26.4%) | same |
| total | 5,725,461 | 5,725,110.1 ± 1.1 (1 sd at 102,400 shots) |

How the per-shot figures work:
- The verifier draws each E_j uniformly from 0..4095 (`verify_submission_dqi.py`, `rng.integers(0, max_value, endpoint=True)`).
- A Forney step therefore runs with probability 4095/4096.
- The number of skipped positions per shot is about Binomial(4095, 1/4096).
- The predicted mean saving is 350.91 Toffoli per shot, with sd 351 × sqrt(0.9995 / 102,400) ≈ 1.10 for the verifier's 102,400-shot mean.
- The exp-001 unsalted mean (5,725,108.38) sits at z ≈ −1.6, which is consistent.

What this implies for the claims:
- **C-006.** If 51-Toffoli multiplies replace all of them, the upper bound is 12 × 58,206 ≈ 0.698M per shot, which is −12.2% T. The 0.70M figure in C-006 is therefore an upper bound that is actually available, not a double count. If only the 33,296 multiplies outside the inversion chains are replaced, the bound drops to 0.40M (−7.0%).
- **C-005.** The Forney inversions are about 1.29M per shot (22.5%), not 1.44M. The 1.44M figure includes 36 non-inversion Toffolis per position (the `init_and` and the two `flip_if_equal` with 0).

Sub-predictions:
- (a) The sample `dqi.kmb` contains kickmix's INFO_TAG subroutine marks.
- (b) The sample is identical to a fresh kickmix 1.0.0 build of `dqi_reference_circuit.py` with default arguments (Circuit `==`, and equal canonical .kmb SHA-256). Confidence is moderate.
- (c) On each of 3 salted verifier runs:
  - the per-shot mean `toffoli_count` lies within 5,725,110.1 ± 3.3 (3 sd);
  - Q is 1,893;
  - there are 0 failures.

**What refutes C-006's premise.** Either of these:
- the sample's `gf_mul` instances cost fewer than 63 Toffoli (for example 51), which would mean it already has the cheaper multiplier;
- fewer than 25,000 GF(2^12) multiplies execute per shot, which would put the 12-Toffoli saving below 0.3M (lit-2510.10967 note, Idea 1 refutation threshold).

**What refutes this experiment's prediction.** Any of these:
- instance counts or per-instance costs that differ from the table;
- conditioned Toffolis anywhere other than `forney_step`;
- a salted per-shot mean outside the ±3 sd band.

If the sample has no tags (sub-prediction (a) fails), the breakdown is taken from the fresh generator build. That is valid only if (b) holds; otherwise the result is inconclusive for the sample itself.

Expected score delta: none. No circuit is changed.

## Method

- **Baseline.** exp-001 (critic-accepted), same `data/sample_submission/dqi.kmb` (SHA-256 959471d0...4995) and unmodified `data/verifiers/dqi/`.
- **Counter.** `src/kmx_tag_count.py` streams a .kmx text circuit line by line. It attributes each CCX/CCZ/CSWAP to its enclosing INFO_TAG stack (full path and per-instance inclusive histogram) and tracks PUSH/POP_CONDITION. For each condition it records whether the bit came from an HMR measurement or from an OR of BIT_STORE1 sources (and which registers fed it). Its total is checked against `Circuit.operation_statistics().num_toffoli_like`.
- **Kaggle run.** One private CPU kernel, `experiments/exp-003/kernel/`. Defaults are as in the quantum-stack skill: no GPU, internet on, competition source attached, `pip install kickmix==1.0.0`. It never calls any submit endpoint. Each step runs in its own subprocess, with peak RSS recorded:
  1. Load the sample `dqi.kmb` and record Q and `operation_statistics`. Write it as .kmx to local disk and run the counter. Delete the .kmx.
  2. Build `build_reference_circuit(4095, 70, 12)` with the competition's `dqi_reference_circuit.py`. Compare it to the sample (`==`, canonical .kmb SHA-256, op counts).
  3. Run the official verifier on the sample 3 times, with `--salt exp003-a`, `exp003-b` and `exp003-c` (default shots 102,400, default batch, fork workers). Record `toffoli_count`, `max_toffoli_count`, Q, failures, ε+, R and score.
- **Per-shot subroutine counts.** These are computed analytically. Static count per subroutine × the probability that its condition holds, from the counter's condition definitions and the verifier's sampling distribution. The check is the verifier's measured per-shot mean.
- **Outputs.** Downloaded into `experiments/exp-003/kaggle_output/`. `results.json` is written by `experiments/exp-003/make_results.py` from those files.

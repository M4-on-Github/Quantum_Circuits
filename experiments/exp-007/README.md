---
id: exp-007
title: Can the reverse ANGLE_k use be a cheaper measurement-based uncompute? (verifier rules check)
task: dfthcsos
tests: [C-012]
direction: D-001
status: done
date: 2026-10-28
commit: 5373e1d
result: "C-012 refuted structurally (prediction held): the reverse pass re-runs the same submitted circuits, uninverted, in reverse order and charges them again; no separate uncompute circuit can be supplied (2K files rejected, extra names ignored); a direction-specific target MBU fails at reverse ANGLE_2. MBU inside ANGLE_k is legal (P1, P5 PASS; P5 official verify 124 qubits, angles 159,040 = 2 x static), conditioned Toffolis are charged per shot (implied fraction 0.4985 / 0.5057). Realistic saving at J=8, brot=12 under the cap: 0%"
---

## Hypothesis

C-012 (knowledge/claims.md): the dfthcsos verifier lets the second (reverse) ANGLE_k use be a cheaper measurement-based uncompute (MBU; lit-1905.07682 §2, lit-1902.02134 App. C Thm. 3) instead of charging the same circuit twice, so ANGLE T per circuit can fall by about 40% (lit-scout arithmetic: 7,948 → about 4,480 per circuit on the reference, i.e. forward unary lookup 3,974 + MBU uncompute ⌈3976/8⌉ + 8 = 505, 17 clean qubits, width 125).

Baseline: exp-002 (accepted). `src/angleload` rebuilds the 10 reference ANGLE_k circuits byte for byte (brot 12, J 8, A = 3,976, 119 qubits, 3,974 Toffoli each, measurement-based `del_and` at 0 Toffoli). Reference ANGLES = 79,480 Toffoli of T_total 93,237.

This is a rules check, not a circuit design.

## Prediction

Written 2026-10-28 after reading `data/verifiers/dfthcsos/verify.py`, `scoreinfra/circuits.py` and `SCORING_README.md` as code, and after measuring kickmix's own `init_lookup` / `del_lookup` gate counts in a scratch build (below). No probe circuit has been built or verified yet.

### Pre-registered answers (from the source)

1. **Forward and reverse charging.** `recover_words_from_circuits` (circuits.py lines 534-555) runs `sim.do(circuits[k])` for k = 0..K-1 and then `sim.do(circuits[k])` for k = K-1..0. The reverse pass applies the *same submitted circuit object*, uninverted, in reverse order; nothing is inverted because ANGLE_k is specified as a self-inverse XOR oracle. The Toffoli count is one `Simulator` with `counting_operations=True` accumulated over both passes (`operation_statistics().num_toffoli_like / (num_vectors * repeats)`, line 556), so each circuit is charged on both uses. The family is read only from `angle_k_<k>.(kmb|kmx)` (`_ANGLE_FILE_PATTERN` fullmatch, contiguous from 0), and exactly `ceil(75 / J)` circuits are required (lines 465-470). **A separate, cheaper uncompute circuit cannot be supplied**: an extra differently named file is ignored, and 2K files are rejected by the count check.
2. **Measurements and fix-ups.** Accepted. The only banned instruction is `Z_POW` (`_reject_rotations`); the README "Register contract" names `HMR` plus conditioned `CZ`/`CCZ`/`NEG`. `toffoli_count` is the simulator's per-shot mean of executed `CCX`/`CCZ`/`CSWAP` over both passes; a gate under a classical condition counts only on shots where the condition holds (README "Scoring"; `angles_costs` docstring). `HMR`, `CZ`, `NEG`, `BIT_*` count 0. Prediction for a probe: a Toffoli-like gate conditioned on one fresh HMR bit is charged 1/2 on average (observed fraction within ±3σ of 0.5); unconditioned gates make dynamic = static exactly.
3. **What ANGLE_k must leave, after every single use.** Checked after each circuit, forward and reverse separately (`_check_state` + `read_words`): phase unflipped on every one of the A × 64 shots; `selection` unchanged; every non-public qubit back to |0>; word registers equal to batch k (forward) or batch k-1 (reverse; all zero after reverse ANGLE_0), identical across the 64 shots. Between circuits the simulator is cleared and the words are rewritten (`reset_between_circuits`), so no ancilla, phase or measurement record can carry from the forward use to the reverse use. Inputs: forward ANGLE_k sees z = batch[k-1](a) (zero for k = 0), reverse ANGLE_k sees z = batch[k](a) (reachable-only contract, kg-753092 host ruling). Consequence: MBU of any **ancilla** whose value is a known function of the address (and of the reachable z) is legal inside a circuit. MBU of the **target** requires knowing z as a function of a, but the same circuit receives z = batch[k-1](a) forward and z = batch[k](a) reverse, so a target MBU fixed up for one direction leaves a phase error (and the wrong word) in the other unless delta_k(a) = 0 for every a.

### Pre-registered conclusion on C-012

- C-012 as stated is **structurally impossible**: the reverse use is the same circuit, charged again.
- Even if a direction-specific reverse circuit were allowed, the verifier's delta-streaming contract has reverse ANGLE_k (k ≥ 1) map batch[k] → batch[k-1], i.e. clear *and* reload. Only reverse ANGLE_0 is a pure uncompute (batch[0] → 0). The 44% arithmetic assumes every reverse use is a pure uncompute.
- Inside one circuit, MBU only saves Toffolis on ancillas that hold looked-up data (clean QROAM). At J = 8, brot = 12 the public registers take 12 + 96 = 108 qubits, leaving 20 under the 128 cap, while a clean QROAM with block factor λ ≥ 2 needs at least λ × 96 extra qubits. **Predicted realistic saving at J = 8, brot = 12: 0%** (the reference unary QROM with free `del_and` is already the cheapest form that fits).

### Scratch measurement used to design the probes (kickmix 1.0.0, static counts)

`init_lookup` over 12 address bits (table padded to 4,096) costs 4,094 Toffoli for any width. `del_lookup` (kickmix's built-in MBU of a lookup target: HMR the target, parity by conditioned `BIT_INVERT`, binary-to-unary of the low address bits into the measured target qubits, phase lookup with conditioned `CZ`) costs 119 Toffoli at A = 4,096, W = 96 (62 CCX + 57 CSWAP, 114 qubits) and 56 at A = 1,024, W = 96. In a 16-address dump its CCX/CSWAP are unconditioned; only `CZ`, `BIT_INVERT` and `NEG` are conditioned.

### Probe predictions

| Probe | What | Predicted outcome |
|---|---|---|
| P1 | Small synthetic family (A = 37, 5 angles, J = 2, brot = 4, K = 3). Each ANGLE_k = `init_lookup` delta_k into a clean 8-qubit ancilla, CX into the words, `del_lookup` the ancilla (an MBU section) | PASS on `recover_words_from_circuits`; words equal the table; dynamic Toffoli = 2 × Σ static exactly |
| P2 | P1 plus, in ANGLE_0, one HMR of a clean qubit (random bit m, no kickback) and 1,000 identity CCX pairs under `PUSH_CONDITION m` | PASS; extra dynamic count over both passes = 2 × 2,000 × (fraction of shots with m = 1) ≈ 2,000 (range 1,850-2,150), against +4,000 static |
| P3 | C-012 literal on the small table: ANGLE_k = `del_lookup`(batch[k-1]) on the words, then `init_lookup`(batch[k]) (a direction-specific "uncompute then load"; ANGLE_0 = `init_lookup` only) | FAIL at the first reverse circuit, reverse ANGLE_2 (uncorrected phase or wrong words) |
| P4 | (a) the P1 family plus K extra "uncompute" circuits as angle_k_3..5; (b) the P1 family plus an extra file `angle_k_0_dag.kmb` | (a) FAIL "5 angles in batches of J=2 need 3 circuits, got 6" before simulation; (b) the loader reads exactly 3 circuits and ignores the extra file |
| P5 | Full size, official `verify.py` CLI: the reference family from `src/angleload` (sample angle_words, brot 12, J 8) with an MBU section in every circuit: the QROM XORs delta_k with word_7 bits 0..3 masked out, and those 4 bits go through `init_lookup` into a clean 4-qubit ancilla, CX, `del_lookup` | PASS; lambda_eff = 49.301369 (same words as the reference); every circuit ≤ 128 qubits; angles_toffoli = 2 × Σ static exactly; cost above the reference (an extra lookup per circuit, about +4,100 static per circuit) |

What would refute the pre-registered answers: P1 or P5 failing (MBU inside ANGLE_k not accepted), P2's dynamic extra equal to the static +4,000 (no per-shot discount) or 0, P3 passing (direction-specific reverse accepted), P4(a) passing.

## Method

- Code: `experiments/exp-007/probes.py` (P1-P4, small, on the official checking path `dfthcsos.scoreinfra.circuits.recover_words_from_circuits` and `load_circuits`), `experiments/exp-007/build_p5.py` (P5 family to `experiments/exp-007/out/p5/`, with the sample `submission.npz` copied in), `experiments/exp-007/run_verify_p5.py` (official CLI, background, log in `logs/`). MBU-section builders in `src/angleload/mbu.py`.
- Verifier: `data/verifiers/dfthcsos/verify.py` unmodified, `python -B` from `data/verifiers/`, default salt (empty) and default 64 shots per address. Small probes use seeds 0 and 12345.
- Baseline numbers: exp-002 / SCORING_README (score 3,355,599,588.3, T_total 93,237, Q_total 730, ANGLES 79,480).

## Results

All numbers are from `results.json` (official checking path for P1-P4, official `verify.py` CLI for P5). kickmix 1.0.0, local Windows.

### Probes

| Probe | Predicted | Observed |
|---|---|---|
| P1 MBU section (init_lookup → ancilla, CX, del_lookup) | PASS, dynamic = 2 × Σ static | PASS on seeds 0 and 12345, words = table; dynamic 432.0 = static 2 × 216 |
| P2 1,000 identity CCX pairs under one fresh HMR bit | extra dynamic 1,850-2,150 vs +4,000 static | +1,994.09 (seed 0) and +2,022.80 (seed 12345); implied condition fraction 0.4985 and 0.5057 |
| P3 direction-specific "MBU-clear batch[k-1], load batch[k]" | FAIL at reverse ANGLE_2 | FAIL on both seeds: `reverse ANGLE_2: uncorrected phase (measurement kickback)`; all 3 forward circuits passed |
| P4a K forward + K uncompute circuits (6 files) | FAIL on circuit count | `load_circuits` read 6; FAIL `5 angles in batches of J=2 need 3 circuits, got 6` (0.006 s, before simulation) |
| P4b extra file `angle_k_0_dag.kmb` | ignored | 3 circuits loaded, equal to P1; PASS with the same 432.0 count |

### P5: full size, official verifier

| Metric | Baseline (exp-002, reference) | P5 (MBU section in every circuit) | Change |
|---|---|---|---|
| status | PASS | PASS | |
| max ANGLE_k width | 119 | 124 | +5 (4 ancilla + unary-iteration ladder) |
| static Toffoli per circuit | 3,974 | 7,952 | +3,978 (the MBU fix-up's unary iteration) |
| angles_toffoli (both passes) | 79,480 | 159,040 | = 2 × Σ static exactly |
| toffoli_count (T_total) | 93,237 | 172,797 | |
| num_qubits (Q_total) | 730 | 730 | 0 (ANGLE temp 16 < shared 544) |
| lambda_eff | 49.301369 | 49.30136925057438 | 0 (same words) |
| error_1 / error_2 (mHa) | | 3.185 / 18.640 | |
| score (cost) | 3,355,599,588.3 | 6,218,963,952.7 | improvement factor 0.5396 (a legality probe, not an optimization) |
| wall / peak RSS | | 580.8 s / 1.10 GB | |

The `emit_qrom_xor` builder used in P5 emits a circuit equal (`==`) to `angleload.qrom.build_qrom_circuit` for all 10 sample circuits, so P5 differs from the reference only by its MBU section.

### Layout arithmetic (estimates, `analysis.py`, not verifier output)

Per pass, the reference family costs K × (A − 2) = 10 × 3,974. A select-swap loader (target as block 0, λ blocks, MBU of the (λ − 1)·W junk bits) needs 12 + λ·12J + ladder ≤ 128, which forces Jλ ≤ 8. Its lookup term is then about 75·A/(Jλ), no better than the reference's, plus swap and MBU overhead. Best feasible T_total × Q_total relative to the reference:

| J | λ | width | per circuit (1 pass) | ANGLES (2 passes) | T_total | Q_total | T·Q / ref |
|---|---|---|---|---|---|---|---|
| 8 | 1 (reference) | 119 | 3,974 | 79,480 | 93,237 | 730 | 1.000 |
| 4 | 2 | 118 | 2,271 | 86,298 | 100,055 | 682 | 1.003 |
| 2 | 4 | 117 | 1,325 | 100,700 | 114,457 | 658 | 1.107 |
| 7 | 1 | 107 | 3,974 | 87,428 | 101,185 | 718 | 1.067 |
| 1 | 8 | 116 | 852 | 127,800 | 141,557 | 646 | 1.344 |

The hypothetical case the verifier does not allow is a direction-specific reverse circuit. Even then only reverse ANGLE_0 is a pure uncompute: kickmix `del_lookup` costs 119 static at W = 96, against 3,974. That saves 3,855 Toffoli, 4.9% of ANGLES and 4.1% of T_total, not the 44% of the C-012 arithmetic.

## Conclusion

The prediction held on every point.

1. **Charging.** The verifier runs the same K submitted circuits forward and then again, uninverted, in reverse order, and one simulator counts both passes. No separate or cheaper uncompute circuit can be supplied: 2K files are rejected by the count check, and a differently named extra file is never read (P4).
2. **Measurements and counting.** Mid-circuit `HMR` and classically conditioned fix-ups (`CZ`, `Z`, `NEG`, `BIT_INVERT`, and gates under `PUSH_CONDITION`) are accepted inside ANGLE_k (P1, P5). `toffoli_count` is per shot: a CCX under a condition bit is charged only on shots where the bit is 1, which is 1/2 for one fresh HMR bit (P2). Unconditioned gates make the dynamic count equal 2 × the static count (P1, P5).
3. **Legality of MBU.** Each use is checked on its own, and the state is cleared between uses, so nothing carries from the forward use to the reverse use. The circuit must leave phase unflipped, selection unchanged, every ancilla at |0>, and the words at batch k (forward) or batch k-1 (reverse). That makes MBU legal for an ancilla holding a known function of the address. It is not legal for the target: one circuit sees z = batch[k-1] going forward and z = batch[k] in reverse, so a target MBU that is correct in one direction leaves a phase in the other (P3).

**C-012 is structurally impossible.** The reverse use cannot be a cheaper uncompute. At J = 8, brot = 12 under the 128-qubit cap, the realistic per-circuit ANGLE saving from MBU is **0%**. Inside a circuit, MBU only pays for clean junk registers, and the 20 spare qubits cannot hold even one extra 96-bit block. The reference unary QROM with measurement-based `del_and` is already the cheapest layout that fits. By my arithmetic, a J = 4, λ = 2 select-swap loader with MBU junk uncompute is about break-even (T·Q ×1.003, estimate, not built).

Next step: the research lead can mark C-012 refuted once the critic accepts this. One lead remains open. MBU makes select-swap loaders feasible at small J, which separates ANGLE T from the J·brot qubits that Q_total charges. Whether that helps the frontier design (brot 8, J 5, heavily structured tables, about 280 Toffoli per circuit, exp-006) needs its own claim and arithmetic. It does not help the reference.

## Deviations

- 2026-10-28, P5 construction. The prediction table says the 4 routed bits "go through `init_lookup` into a clean 4-qubit ancilla, CX, `del_lookup`". kickmix 1.0.0's `del_lookup` refuses narrow targets: at 12 address bits it raises `tried to take 1 clean qubits, but only 0 were available` for W ≤ 48 and works for W ≥ 64 (scan in the quantum-stack skill). A 64-bit ancilla does not fit under the cap. So P5 fills the 4-qubit ancilla in the same QROM pass, which costs no extra Toffolis, and clears it with `angleload.mbu.emit_mbu_clear`: HMR, then a unary-iteration phase fix with Z conditioned on the measured bits. The function, the MBU nature of the section and the predicted outcomes are unchanged. The extra static cost is +3,978 per circuit, inside the predicted "about +4,100".
- The P1, P2 and P3 small probes use kickmix `init_lookup` / `del_lookup` as written, at 6 address bits and W = 8, where `del_lookup` works.

---
id: exp-002
title: Own dfthcsos ANGLE_k generator reproduces the sample loaders
task: dfthcsos
tests: [C-009]
direction: D-001
status: done
date: 2026-10-28
commit: b857178
result: PASS at cost 3,355,599,588.3155365 (local), equal to exp-001; all 10 generated angle_k .kmb are byte-identical to the sample (119 qubits, 3,974 Toffoli each); prediction held
---

## Hypothesis

C-009 (knowledge/claims.md): a generator we write can reproduce the reference dfthcsos ANGLE_k circuits so that the full sample dfthcsos submission, with our ANGLE_k files swapped in, passes verify.py at cost 3,355,599,588.3 within 0.1%.

Baseline: exp-001 (critic-accepted). The sample dfthcsos submission verifies at cost 3,355,599,588.3155375 on Kaggle (3,355,599,588.3155365 locally): T_total 93,237, Q_total 730, 10 ANGLE_k circuits, max width 119, brot 12.

## Prediction

Made before our generator has been written or run.

| Quantity | Prediction | Source of the expectation |
|---|---|---|
| verify.py status | PASS | C-009 |
| cost | 3,355,599,588.3 within 0.1% (i.e. in [3,352,244,000, 3,358,955,000]); expected exactly equal to the exp-001 value on the same platform | exp-001 |
| T_total / Q_total | 93,237 / 730 | exp-001, SCORING_README |
| n_circuits / brot / J | 10 / 12 / 8 | SCORING_README |
| per-circuit static Toffoli (`operation_statistics().num_toffoli_like`) | 3,974 for each of angle_k_0..9 (= 3976 addresses - 2) | SCORING_README ("3974 Toffolis each") |
| per-circuit width (`num_qubits`) | 119 for each (12 selection + 8 x 12 word + 11 ancilla) | SCORING_README |
| lambda_eff, Lambda, E_gap, error_1, error_2 | equal to exp-001 (49.3013692506, 308.455939733, 3.96547724429 Ha, 3.185 / 18.640 mHa) | the circuits load the same `angle_words` |
| bit-identical to sample `.kmb` | yes for all 10 files (medium confidence: we follow the same gate order, but kickmix serialization details we have not checked could differ). If they are bit-identical, `submission_sha256` and hence the seed equal exp-001's, so the verifier output must equal exp-001's local output exactly | SCORING_README says the reference script writes the same gates as the shipped files |

Refuted if: verify.py rejects the submission, or the cost differs from 3,355,599,588.3 by more than 0.1%.
A failed bit-identity prediction with an otherwise passing, equal-cost verify does not refute C-009; it is recorded as a separate finding (where the files differ).

Expected score delta: none (improvement factor 1.0). This is the generator base for C-008 / C-003 / C-007 under D-001.

## Method

- Generator: `src/angleload/qrom.py` (new, our code). Input: the `angle_words` table (3976 x 75, 12-bit words) stored in the sample `data/sample_submission/dfthcsos/submission.npz`, the same input the sample's circuits were built from. Design follows SCORING_README / `example_submission/angle_k_reference_circuit.py` as a specification: J = 8 words per circuit, K = ceil(75/8) = 10 circuits, circuit k loads delta[k] = batch[k] XOR batch[k-1]; each circuit is a balanced segment-tree unary iteration over the 12-bit `selection` register (top bit split by X without an ancilla, one `init_and` per further internal node, measurement-based `del_and` uncompute, 11 clean ancillas), with leaf / constant-segment loads as CX fan-outs into `word_0..word_7` (brot = 12 qubits each).
- Driver: `experiments/exp-002/build.py` with config `experiments/exp-002/config.json`. It writes `experiments/exp-002/out/submission/` = a byte copy of the sample `submission.npz` plus our `angle_k_0..9.kmb`; nothing else from the sample is changed. It records per-circuit Toffoli, width, SHA-256, and a byte comparison against the sample `.kmb` files to `out/build_report.json` (copied into `results.json`).
- Verify: unmodified official verifier at default seed (no `--salt`, no `--seed`), run locally in the background from `data/verifiers/`:
  `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe dfthcsos/verify.py <abs>/experiments/exp-002/out/submission`
  (local: about 6 min, about 1.1 GB per exp-001). Output JSON saved to `experiments/exp-002/logs/`.
- Platform: local Windows `.venv` (kickmix 1.0.0, numpy 2.5.4, scipy 1.18.1). Comparison is against the exp-001 local dfthcsos value (same platform) and the Kaggle value (0.1% criterion).
- Dependencies pinned in `requirements.txt` at the repo root.

## Results

All numbers are from `results.json`. It is assembled by `make_results.py` from the verifier stdout `logs/verify_stdout.json`, the run metadata `logs/run_meta.json` and the build report `logs/build_report.json`.
The verifier ran locally, unmodified, at the default seed. Command: `(cwd data/verifiers) PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe dfthcsos/verify.py <abs>/experiments/exp-002/out/submission`. Return code 0.

| Metric | Baseline exp-001 (local / Kaggle) | exp-002 (local) | Change |
|---|---|---|---|
| status | PASS | PASS | - |
| cost | 3,355,599,588.3155365 / 3,355,599,588.3155375 | 3,355,599,588.3155365 | 0 vs local; -2.8e-16 rel. vs Kaggle |
| T_total (`toffoli_count`) | 93,237 | 93,237 | 0 |
| ANGLES Toffoli (both passes) / heuristic | 79,480 / 13,757 | 79,480 / 13,757 | 0 |
| Q_total | 730 | 730 | 0 |
| lambda_eff | 49.30136925057438 | 49.30136925057438 | 0 |
| Lambda / E_gap (Ha) | 308.4559397330944 / 3.965477244291833 | same | 0 |
| error_1 / error_2 (mHa) | 3.1852 / 18.6396 | 3.1852 / 18.6396 | 0 |
| n_circuits / brot / J / max width | 10 / 12 / 8 / 119 | 10 / 12 / 8 / 119 | 0 |
| submission_sha256 | 276d464f...4002695 | 276d464f...4002695 | identical |
| verified_shots | 254,464 | 254,464 | 0 |
| improvement factor | 1 | 1.0000000000000002 | - |

The verifier's whole stdout JSON is byte-identical to exp-001's local `logs/local/dfthcsos.stdout.json` (`cmp`). Every top-level field matches.

Per circuit (static counts from `operation_statistics()`; the same values hold for the sample files):

| k | width | Toffoli | instructions | byte-identical to sample |
|---|---|---|---|---|
| 0 | 119 | 3,974 | 187,427 | yes |
| 1 | 119 | 3,974 | 186,423 | yes |
| 2 | 119 | 3,974 | 186,748 | yes |
| 3 | 119 | 3,974 | 186,857 | yes |
| 4 | 119 | 3,974 | 218,777 | yes |
| 5 | 119 | 3,974 | 218,166 | yes |
| 6 | 119 | 3,974 | 218,099 | yes |
| 7 | 119 | 3,974 | 220,382 | yes |
| 8 | 119 | 3,974 | 219,115 | yes |
| 9 | 119 | 3,974 | 218,749 | yes |

- `submission.npz` in the swapped submission is a byte copy of the sample's (SHA-256 equal).
- The generator took 4.4 s, and 4.6 s on a rebuild from the committed code b857178. The rebuild produced the same 10 SHA-256s.
- The verifier ran 1,017 s wall with a 1.11 GB peak RSS.

## Conclusion

The prediction held on every pre-registered item:
- PASS, at a cost equal to exp-001 on the same platform. The 0.1% criterion against the Kaggle value is met with a relative difference of -2.8e-16.
- T 93,237 and Q 730.
- 3,974 Toffoli and 119 qubits per circuit.
- Every metric is unchanged.
- All 10 `.kmb` files are byte-identical to the sample's.

Because the bytes are identical, `submission_sha256` and the simulator seed are identical too. So this run repeats exp-001's local verification exactly. It adds no independent sampling evidence for the circuits' correctness. What it shows is that our committed generator (`src/angleload/qrom.py`) regenerates the sample's dfthcsos circuits exactly, which is the prize-reproducibility requirement (kg-752010).

This supports C-009, pending critic review. It meets D-001's midterm check for dfthcsos (our generator reproduces 3,355,599,588.3 within 0.1%).

Next: use `src/angleload` as the base for C-008 (J = 9, brot = 11) and C-003 (reachable-only loaders). Any changed circuit gets a fresh seed, so those runs give new sampling evidence.

## Deviations

- 2026-10-28: the verifier runtime (1,017 s) was about 3x the ~6 min planned. The laptop was on battery (`BatteryStatus.Discharging` True). For the first ~11 min the verifier process got only about 98 CPU-s, after which it ran at about one core. The result is not affected.
- 2026-10-28: Kaggle was not used. The task allowed a local run, and the byte-identical files make the Kaggle result predictable from exp-001 (3,355,599,588.3155375). It was not re-measured.

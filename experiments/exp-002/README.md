---
id: exp-002
title: Own dfthcsos ANGLE_k generator reproduces the sample loaders
task: dfthcsos
tests: [C-009]
direction: D-001
status: planned
date: 2026-10-28
commit: unknown
result: unknown
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

(pending)

## Conclusion

(pending)

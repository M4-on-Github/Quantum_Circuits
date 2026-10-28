---
id: exp-001
title: Baseline - verify official sample submission on all three tasks
task: all
tests: [C-001]
direction: none
status: planned
date: 2026-10-28
commit: unknown
result: unknown
---

## Hypothesis

C-001 (knowledge/claims.md): the leaderboard's per-task reference costs equal the paper/README references:
invsqrt 260 x 7,988 ~ 2.077e6, dqi 1.19128 x 1893^2 x 5,725,461 ~ 2.444e13, dfthcsos 3,355,599,588.3.
If true, the LB score can be computed locally from verifier costs without spending submissions.

There is no baseline experiment: this experiment is the baseline.

## Prediction

Made before any run. All numbers below are what the unmodified official verifiers should report for the official sample submission.

| Task | Prediction |
|---|---|
| invsqrt | passes; Q = 260, Toffoli-equivalent = 7,988, cost = 260 x 7,988 = 2,076,880 |
| dqi | passes; Q = 1,893, T (Toffolis) = 5,725,461, R(eps+) in [1.15, 1.25] |
| dfthcsos | passes; cost = 3,355,599,588.3155365, matching to at least 6 significant figures |
| determinism | re-running the cheapest task (invsqrt) with the same seed/salt gives identical pass/fail and identical cost components |
| parity | local Windows (.venv) results for invsqrt and dfthcsos equal the Kaggle Linux kernel results |

Refuted if any of:
- any task fails verification;
- invsqrt or dfthcsos cost differs from the prediction by more than 0.1%;
- dqi Q or T differs from 1,893 / 5,725,461. Note: the literature also gives 1,885 Q and 5,717,729 T as alternative values; a match to those instead would refute this prediction and point to a version difference between the paper and the sample submission.

A Windows vs Linux mismatch, or a non-deterministic re-run, is recorded as a separate finding (tooling, not C-001) and would be noted in the quantum-stack skill.

Expected score delta: none. This establishes the reference costs (improvement factor 1.0 by construction).

## Method

Inputs: the official sample submission in `data/sample_submission/` (invsqrt, dqi.kmb, dfthcsos/) and the unmodified official verifiers in `data/verifiers/` (invsqrt/verify_submission_invsqrt.py, dqi/verify_submission_dqi.py, dfthcsos/verify.py). Nothing is generated or edited.

1. Kaggle run (primary, all three tasks). One self-contained private script kernel, `experiments/exp-001/kernel/`, with `kernel-metadata.json`:
   - `kernel_type: script`
   - `is_private: true`
   - `enable_gpu: false`
   - `enable_tpu: false`
   - `enable_internet: true`
   - `competition_sources: ["google-verifiable-quantum-circuit-compilation"]`
   - script starts with `pip install kickmix==1.0.0`
   - the kernel only runs the verifiers on the competition-provided sample submission and writes logs plus a JSON of results. It never calls any submit endpoint.
   Pushed with `kaggle kernels push`; outputs fetched with `kaggle kernels output` into `experiments/exp-001/kaggle_output/`. Kernel slug and version recorded here after the push.
2. Local run (parity check, invsqrt and dfthcsos only). Existing `.venv` (kickmix 1.0.0, numpy, scipy, psutil) on Windows 11, same verifiers, same sample files. dqi is not run locally (886 MB circuit, memory-heavy). Long runs go in the background with logs in `experiments/exp-001/logs/`.
3. Determinism: re-run invsqrt (the cheapest task) once more with the same seed/salt, on both Kaggle and local.
4. Seeds/salts: whatever the verifiers use by default (Fiat-Shamir hash of the submission plus the local salt). The exact mechanism is read from the verifier source and recorded here before running; it is not changed.
5. Recorded per task and per platform: pass/fail; every cost component the verifier reports (Q, Toffolis, T-gates, cost; dqi failures, shots, eps+, R; dfthcsos lambda_eff, Lambda, E_gap, Hamiltonian error, max width, number of circuits); wall time; peak RSS (psutil); CPU core count. All numbers are copied from verifier output, never recomputed by hand.
6. Exact verifier commands are recorded in `results.json` (`verifier_cmd`) once fixed from each verifier's CLI.

## Results

Not run yet.

## Conclusion

Not run yet.

---
id: exp-001
title: Baseline - verify official sample submission on all three tasks
task: all
tests: [C-001]
direction: none
status: done
date: 2026-10-28
commit: b50bf94
result: all 3 tasks PASS on Kaggle; invsqrt 2,076,774.23, dqi 2.4439e13 (R 1.19126, 0 failures), dfthcsos 3,355,599,588.316; dqi T as pre-registered (5,725,461) is the static max, the verifier uses the per-shot mean 5,725,108.38
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

All numbers are copied from `results.json`, which takes them from the verifier JSON outputs in `kaggle_output/exp001/` and `logs/local/`.
Kaggle kernel: `rainm4/exp-001-verify-sample-submission`, version 1 (id_no 141337889), private, CPU only. Server metadata is in `kernel/server-metadata-v1.json`, the push log in `kernel/push_v1.log`.
Input SHA-256s (all 3 verifiers, the scoreinfra modules, every sample file including dqi.kmb) are identical on Kaggle and local.

| Task | Metric | Predicted | Kaggle (Linux, 4 CPU) | Local (Windows) | Held? |
|---|---|---|---|---|---|
| invsqrt | status | PASS | PASS | PASS | yes |
| invsqrt | Q | 260 | 260 | 260 | yes |
| invsqrt | Toffoli-equivalent | 7,988 | 7,987.593206597238 | identical | yes (-0.005%) |
| invsqrt | cost | 2,076,880 (+-0.1%) | 2,076,774.233715282 | identical | yes (-0.0051%) |
| dqi | status | PASS | PASS (0 value, 0 phase errors / 102,400) | not run | yes |
| dqi | Q | 1,893 | 1,893 | - | yes |
| dqi | T | 5,725,461 | `toffoli_count` (per-shot mean, used in cost) 5,725,108.382109375; `max_toffoli_count` 5,725,461 | - | no as written (see Conclusion) |
| dqi | eps+ / R | R in [1.15, 1.25] | 8.660587e-4 / 1.1912604648115832 | - | yes |
| dqi | cost | (C-001: ~2.444e13) | 24,439,463,583,672.93 | - | - |
| dfthcsos | status | PASS | PASS | PASS | yes |
| dfthcsos | cost | 3,355,599,588.3155365 (6 sig. fig.) | 3,355,599,588.3155375 | 3,355,599,588.3155365 | yes |
| dfthcsos | T / Q | - | 93,237 / 730 | identical | - |
| dfthcsos | lambda_eff, Lambda, E_gap | - | 49.3013692506, 308.455939733, 3.96547724429 Ha | equal to <= 4e-16 rel. | - |
| dfthcsos | error_1 / error_2 | <= 20 mHa | 3.185 / 18.640 mHa | equal to <= 4e-13 rel. | yes |
| dfthcsos | max width / circuits / brot | <= 128 | 119 / 10 / 12 | identical | yes |
| determinism | invsqrt re-run | identical | identical in every output field | identical in every field (and to Kaggle) | yes |
| parity | invsqrt local vs Kaggle | equal | - | bit-identical JSON | yes |
| parity | dfthcsos local vs Kaggle | equal | - | integers identical; floats differ in the last 1-2 ulp (score rel. diff 2.8e-16, error_1 3.7e-13) | not bit-identical |

Runtime and memory (wall time per verifier process; memory sampled every 0.5 s by `kernel/exp001_verify.py`):

| Run | Wall (s) | Peak memory |
|---|---|---|
| Kaggle dfthcsos | 136.6 | 1.21 GB RSS (1 process) |
| Kaggle invsqrt | 1,502.5 | 0.71 GB summed tree RSS (parent + 4 forked workers), 0.54 GB max per-process VmHWM |
| Kaggle invsqrt re-run | 1,504.2 | 0.71 GB tree, 0.54 GB per process |
| Kaggle dqi | 448.5 | 9.53 GB max per-process VmHWM, 9.01 GB summed tree RSS (sampled), 9.61 GB system used of a 30 GiB cgroup limit |
| Local dfthcsos | 356.0 | 1.13 GB peak working set |
| Local invsqrt | 9,056.5 | 0.53 GB peak working set (single process) |
| Local invsqrt re-run | 9,055.0 | 0.54 GB peak working set |

Kaggle kernel total: 3,591.8 s of verifier time (4 runs back to back). Local: the three runs ran concurrently, each verifier single-process, on an i9-14900HX (32 logical CPUs, 31.7 GB).

## Conclusion

Mostly held, with one pre-registered criterion failing as written.

- invsqrt and dfthcsos held: both pass, costs within 0.006% and 15 significant figures of the prediction.
- dqi passes with Q = 1,893 and R = 1.19126, inside the predicted range. But the pre-registered refutation rule ("dqi Q or T differs from 1,893 / 5,725,461") is triggered. The T that enters the verifier's cost is `toffoli_count`, the mean Toffoli-like count per simulated shot: 5,725,108.38. 5,725,461 is `max_toffoli_count`, the static count of the circuit. The prediction used the static count. The alternative literature values (1,885 Q / 5,717,729 T) do not appear, so there is no sign of a paper-vs-sample version difference. The mean is below the static count presumably because MBUC-conditioned gates do not fire on every shot; this experiment did not test that, and it means the dqi cost depends on the seed.
- C-001 as stated (LB references = 260x7,988, 1.19128x1893^2x5,725,461, 3,355,599,588.3) is not settled by this experiment. Local verifiers reproduce those values only approximately for invsqrt and dqi (-0.0051% and -0.0078%), exactly for dfthcsos. Taking the C-001 values as references, the sample's local score is 1.000043. The brief says the sample scores about 1.015 on the LB (source not recorded here). The two do not agree. Possible causes are LB salts giving different invsqrt `rotation_eps` and dqi mean T, or LB references that are not these values. This needs the sample's actual LB per-task numbers to resolve.
- Determinism held on both platforms. invsqrt parity is bit-exact. dfthcsos parity holds for every integer resource count and the score to 3e-16, but float metrics are not bit-identical (numpy 2.1.3/scipy 1.16.3 on Kaggle vs 2.5.4/1.18.1 locally).
- Tooling: a full local invsqrt verify takes 2.5 h on one core because the verifiers only parallelize with `fork`. Kaggle (4 forked workers) takes 25 min. Full invsqrt verifies belong on Kaggle. dqi at full size needs about 9.5 GB on Kaggle, well within the 30 GiB limit.

Next: run dqi (and invsqrt) under 3+ `--salt` values to measure how much mean T and the invsqrt cost move with the seed, and get the sample submission's LB per-task numbers to test the reference costs in C-001 directly.

## Deviations

- 2026-10-28: the first local launch failed immediately (relative `--data-root` resolved against the child's working directory). The paths were made absolute, `logs/local/` was cleared and the runs relaunched. No verifier ran in the failed attempt.
- 2026-10-28: the three local runs (invsqrt, invsqrt re-run, dfthcsos) ran concurrently, not one after another. Local wall times are for that setting.
- 2026-10-28: before the full runs, a timing probe of the invsqrt verifier ran locally with `--max-x 65536 --shots-per-x 1` (PASS, 2.6 s). It is not a result and is not in `results.json`.

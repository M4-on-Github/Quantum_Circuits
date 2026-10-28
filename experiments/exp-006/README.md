---
id: exp-006
title: Account the public 430Q dfthcsos build (ANGLE share of T_total, widths, design)
task: dfthcsos
tests: [C-011]
direction: D-001
status: done
date: 2026-10-28
commit: 435ccbd
result: "C-011 held narrowly: PASS at cost 347,361,566, T_total 16,736 = ANGLES 8,650 (51.7%) + heuristic 8,086, Q 430 = 126 + 304, brot 8, J 5, widths 119/126; the claim's public T 16,752 and lambda_eff 48.2713 are inconsistent with the public cost and were missed; C-008 has no room (Q floor 792), C-003 is already used (sign-bit promise); secondary v11 (C60): cost 341,914,455, share 51.4%"
---

## Hypothesis

C-011 (knowledge/claims.md): in the public 430Q dfthcsos build (16,752 Toffoli, 15 ANGLE circuits), ANGLE_k loading is still at least 50% of T_total. If so, the ANGLE ideas (C-003 reachable-only loaders, C-008 repacking J/brot) apply to the frontier, not only to the reference.

Baseline: exp-002 (our generator for the reference ANGLE_k circuits, byte-identical to the sample; critic pending). In the reference, ANGLE_k is 79,480 of T_total 93,237 (85.2%).

Target build: the dfthcsos part of heliosli's release dataset `heliosli/qcc-circuits-live` (portfolio `v15b_sjmixL`, used by notebook `heliosli/the-dataset-is-now-public-now-enjoy`). Per that notebook: SomeJoint's R = 8, B = 143, C = 62 factorization, 11 of 15 angle circuits from SomeJoint (`somejoint/qcc-our-chemistry-b143-c62`), 4 angle circuits and the table weights by heliosli, cost 3.47362e8, lambda_eff 48.2713, 16,752 Toffoli, 430 qubits (kg digest 2026-10-28). None of these numbers has been verified by us yet.

## Prediction

Made on 2026-10-28, before any file of the build was downloaded or read. The only inputs are the public figures above and the official cost model. I ran `dfthcsos.verify.heuristic_costs(76, 8, 143, 62, brot)` from the unmodified verifier for brot 6..12.

What the cost model gives for R8/B143/C62:

| brot | outer + inner + Givens Toffoli | persistent qubits | heuristic temp qubits |
|---|---|---|---|
| 6 | 373 + 5,463 + 1,650 = 7,486 | 86 | 304 |
| 7 | 373 + 5,463 + 1,950 = 7,786 | 86 | 304 |
| 8 | 373 + 5,463 + 2,250 = 8,086 | 86 | 304 |
| 9..12 | 373 + 3,783 + (2,550..3,450) = 6,706..7,606 | 86 | 607 |

What the build must then look like:
- 15 circuits means J = 5, since ceil(75/J) = 15 only for J = 5.
- Q_total = 86 + J·brot + max(heuristic temp, angles temp). At brot ≥ 9 this is at least 86 + 45 + 607 = 738, so 430 forces brot ≤ 8.
- With temp 304, 86 + 5·brot + 304 = 430 gives **brot = 8**, with angles temp ≤ 304. This matches kirilltym's "11 + 5×8 + 72 = 123 qubits".
- Then the heuristic part is 8,086 Toffoli, and the ANGLE part is 16,752 − 8,086 = **8,666** Toffoli (both passes), so **ANGLE share = 51.7%**.
- That is about 289 Toffoli per circuit per pass, over 76 + 8·143 = 1,220 addresses with an 11-qubit selection register. A plain segment-tree QROM would cost about 1,218 per pass. So the loaders must already be about 4× cheaper than unary iteration over all addresses, for example a dictionary or QROAM structure, or Toffolis conditioned on measured bits that the verifier counts only on the shots where the bit is set.

Pre-registered numbers:

| Quantity | Prediction |
|---|---|
| verify.py status | PASS |
| T_total (`toffoli_count`) | 16,752 (± 1 for a non-integer shot mean) |
| Q_total | 430 |
| lambda_eff | 48.2713 (4 decimals) |
| brot / J / n_circuits | 8 / 5 / 15 |
| heuristic Toffoli | 8,086 = 373 + 5,463 + 2,250 |
| ANGLES Toffoli (both passes) | 8,666 |
| **ANGLE share of T_total** | **51.7%**; range 50 to 55% |
| max ANGLE width | ≤ 128; expected 123 (11 + 40 + 72), i.e. 5 spare |
| angles temp qubits | ≤ 304 (otherwise Q_total would exceed 430) |
| Lambda > 49.0, E_gap > 3.914898, error_1 and error_2 ≤ 20 mHa | all pass; expected close to the gates, since the build was tuned against them |

Confidence that C-011 holds: medium-low. The margin is only 1.7 points. A small error in the public 16,752 figure, or a brot other than 8, could move it.

**What refutes C-011:** the unmodified official verify.py on the downloaded files reports `resources.angles_toffoli / toffoli_count < 0.50`. Equivalently, the ANGLES Toffoli is below 8,376 at T_total 16,752. If verify.py reports a T_total other than 16,752, the share is still judged from the verifier's own figures. If verify.py rejects the build, C-011 cannot be judged from this build: the result is inconclusive.

Expected score delta: none. This is a measurement of a public artifact. It decides whether C-003 and C-008 target the frontier.

## Method

Measurement only. Nothing downloaded is submitted, copied into a submission, or reused as a circuit (knowledge/user-decisions.md; kg-752010).

1. **Download (safety rules of knowledge/user-decisions.md, 2026-10-28).**
   - List `heliosli/qcc-circuits-live` files and sizes with `kaggle datasets files` before downloading anything.
   - Download only the manifest and the dfthcsos members (`kaggle datasets download -f`) into the new empty directory `experiments/exp-006/external/heliosli-qcc-circuits-live/`.
   - Record slug, version, download date and SHA-256 of every file in `experiments/exp-006/external_manifest.json`.
   - Check any archive's members (no absolute paths, no `..`, no symlinks) before extracting. Kaggle `-f` downloads may arrive zipped, and `.xz` members are single streams.
   - Decompress with a script of ours run as `python -I` from outside the directory.
   - `experiments/exp-006/external/` is gitignored, and its hashes are recorded instead.
   - Also pull the notebook sources `somejoint/quantum-circuits-22-44-local-gm-our-chemistry` (the R8/B143/C62 origin) and, if present, the generator source in the somejoint dataset, as text, into `external/`. Read them, never run them.
2. **Static inspection (local, light).** `experiments/exp-006/inspect_build.py`, run as `.venv/Scripts/python.exe -I` with paths as arguments. It loads each `angle_k_*.kmb` only through `kickmix.Circuit.from_file`, and records:
   - `num_qubits`, `operation_statistics().num_toffoli_like` and register widths;
   - the `submission.npz` array shapes, read with `numpy.load(allow_pickle=False)`.
   Its output goes to `logs/inspect_local.json`.
3. **Official verification (Kaggle CPU kernel, private).**
   - `experiments/exp-006/kernel/exp006_verify.py`, kernel `rainm4/exp-006-account-430q-dfthcsos`, with the exp-001 defaults: script, private, CPU, internet on, competition source.
   - The dataset is attached as `dataset_sources: ["heliosli/qcc-circuits-live"]`.
   - The script reads the files as data, not code. It decompresses or copies the dfthcsos members into `/kaggle/working/run/dfthcsos/` and asserts the SHA-256 of each against our local manifest. A mismatch means a different dataset version, and the script stops.
   - It then runs the unmodified verifier at the default seed: `python -I dfthcsos/verify.py /kaggle/working/run/dfthcsos`, with cwd the competition `verifiers/` directory and `PYTHONDONTWRITEBYTECODE=1`.
   - It saves the verifier's stdout JSON and repeats the static kickmix inspection on Kaggle.
   - No submit call anywhere.
   - If Kaggle is unavailable, run locally in the background, if memory allows.
4. **Results.** `experiments/exp-006/make_results.py` builds `results.json` from the verifier JSON and inspection outputs only.
   - It records: T_total, its ANGLES/outer/inner/Givens split, the ANGLE share, Q_total with its parts (persistent, J·brot, temporary maxima), lambda_eff, Lambda, E_gap, error_1, error_2, per-circuit width, Toffoli, and spare qubits under 128.
   - Static per-circuit Toffoli is compared with the verifier's shot-mean ANGLES count.
5. **Design reading.** From the notebook text: J, brot, R/B/C, loader structure, and how Q reached 430. Then a judgment, from the measured numbers, on whether C-008 (J = 9, brot = 11) and C-003 (reachable-only loaders) still have room on this build.

Seeds/salts: default (empty salt, no seed), one run. This is an accounting measurement, so one seed suffices for T and Q. T and Q are integers, or a shot mean that is fixed for a given seed.

## Results

All numbers below are from `results.json`. `make_results.py` builds it from the official verifier's stdout JSON and the kickmix inspection logs. The verifier is the unmodified `dfthcsos/verify.py` at the default seed, run as `python -I dfthcsos/verify.py <stage>` with cwd `verifiers/`.

**Target build: `heliosli/qcc-circuits-live` dataset version 10 (manifest portfolio `v15b_sjmixL`).** Verified locally on Windows. PASS.

| Quantity | Predicted | Verifier | Held? |
|---|---|---|---|
| status | PASS | PASS | yes |
| T_total (`toffoli_count`) | 16,752 ± 1 | **16,736** | **no** (−16) |
| Q_total | 430 | 430 | yes |
| lambda_eff | 48.2713 | **48.26826** | **no** (4th decimal) |
| brot / J / n_circuits | 8 / 5 / 15 | 8 / 5 / 15 | yes |
| heuristic Toffoli | 8,086 = 373 + 5,463 + 2,250 | 8,086 = 373 + 5,463 + 2,250 | yes |
| ANGLES Toffoli (both passes) | 8,666 | **8,650** (4,325 per pass) | **no** (−16) |
| **ANGLE share of T_total** | **51.7%, range 50 to 55%** | **51.685%** | **yes** |
| max ANGLE width | ≤ 128, expected 123 | 126 | ≤ 128 yes; 123 no |
| angles temp qubits | ≤ 304 | 75 | yes |
| Lambda, E_gap, error_1, error_2 | pass the gates | 299.5156; 3.9149065 Ha; 19.9958 mHa; 19.9990 mHa | yes |

- **Cost** 347,361,565.955.
  - That is an improvement factor of 9.6603 over the reference cost 3,355,599,588.3155 (exp-002), or 2.1298× on the overall score.
  - This is not our build and it cannot be submitted.
- **Run.** Verified shots 78,080. `submission_sha256` a3720dfd…c0. Runtime 42.8 s wall, 0.86 GB peak RSS, local, on AC power.
- **Q_total 430.**
  - Persistent 126 = outer prep 42 + inner prep 44 + angle words J·brot = 40.
  - Plus a temporary maximum of 304, which is the inner state prep. The other temporaries are smaller: angles 75, outer prep 96.
  - The selection register is 11 qubits.
- **Per circuit** (kickmix static counts):
  - k = 0..3: width 119 (9 spare under 128), workspace 68, 303 Toffoli.
  - k = 4..14: width 126 (2 spare), workspace 75, 283 Toffoli.
  - 4·303 + 11·283 = 4,325, which equals the verifier's per-pass ANGLES.
  - The simulated mean Toffoli per shot equals the static count on every circuit, so no Toffoli is conditioned on a measured bit.
  - Every circuit has exactly 80 CCX from `init_and` product caches, matched by 80 HMR (`del_and`). The remaining CCX are one per paired ANF product.
  - The 4 + 11 split matches the public description: 4 circuits by heliosli, 11 by SomeJoint. Which k belongs to whom is my inference and was not traced.

**C-011 verdict: holds, narrowly.**
- ANGLES are 8,650 of 16,736, which is 51.685%.
- The threshold 0.5 × 16,736 is 8,368, so the margin is 282 Toffoli.
- Under the official cost model, the heuristic part (8,086) is fixed for R8/B143/C62 at brot ≤ 8. The share can only drop below 50% if the ANGLE loaders get cheaper.

**The public figures do not agree with each other.**
- 16,752 × 48.2713 × 430 = 347,715,552, which is not the public cost of 3.47362e8.
- The verifier's 16,736 × 48.26826 × 430 = 347,361,566 does match the public cost.
- So the "16,752 Toffoli" and "lambda_eff 48.2713" figures quoted in C-011 do not describe this file set, but the public cost does. Both predicted misses (T and lambda_eff) come from those inputs.

**Promise check (`xor_oracle_check.py`).** This is a local kickmix simulation, not a verifier. It runs all 1,220 addresses × 8 shots per mode.
- Every v10 circuit is correct (fail fraction 0) on zero inputs and on sign-canonical target words, i.e. words whose top two bits are equal.
- On uniformly random target words, 96.6% to 97.0% of shots fail, with phase errors and wrong words.
  - For comparison: if a shot fails exactly when any of the 5 registers is not sign-canonical, the rate is 1 − 2⁻⁵ = 96.9%.
  - Each circuit's fail fraction is identical to that of the same-index promise-relying circuit in v11. The same RNG stream gives the same inputs, so failure depends only on the input words.
- So all 15 v10 loaders rely on the reachable-state promise: they borrow the redundant sign bit and are not general XOR oracles.
- The verifier accepts them because its traversal reaches only sign-canonical words.

**Secondary: dataset version 11 (portfolio `v17_sjx`, C = 60, the current release).**
- **Runs.** Verified on Kaggle by kernels `rainm4/exp-006-account-430q-v10` and `rainm4/exp-006-account-430q-v11`, both version 1. Both actually ran on v11 (see Deviations). Their verifier stdout is byte-identical. PASS.
- **Cost** 341,914,455.077, which is 1.6% below v10.
- **T_total** 16,306 = ANGLES 8,376 (4,188 per pass) + inner 5,311 + Givens 2,250 + outer 369. **ANGLE share 51.37%.**
- **Q** 430: temporary max 304, angles temp 77.
- **Metrics.** lambda_eff 48.76425, Lambda 305.6626, E_gap 3.9149022, error_1 15.830 mHa, error_2 19.9988 mHa.
- **Runtime** 29.5 s and 33.5 s wall, 0.73 GB peak RSS.
- **Per circuit:**
  - k = 0..3: width 126, 302 Toffoli.
  - k = 4, 6, 8, 10, 12, 14: width 126, 280 Toffoli.
  - k = 5, 7, 9, 11, 13: width 128 (0 spare), 260 Toffoli.
- Only the five width-128 circuits pass the random-word check (fail 0). These are SomeJoint's full-XOR loaders. The other ten rely on the sign promise, as in v10.

## Design reading (from notebook text, not executed)

Source: `somejoint/quantum-circuits-22-67-local-gm-full-xor-chem`, read as text. It is the successor of the 22-44 notebook named in the plan; that one is gone.

- **Factorization.**
  - R8/B143 was pruned from B154. That takes the addresses from 1,308 to 1,220 and the inner prep from 5,981 to 5,463 Toffoli (9 sixteen-way blocks).
  - C60 in v11 lowers the inner prep to 5,311.
  - The table weights were refit for the lowest lambda_eff.
- **Loader.** Each output bit is an ANF polynomial over the 11 address bits on the 1,220 valid addresses.
  - A high-address product cache holds `init_and` products for h·16 with popcount(h) ≥ 2 and h ≤ 76, which is 69 entries.
  - A 4-bit low-address cache holds the products with popcount ≥ 2, which is 11 entries. It is computed and erased in phases.
  - 69 + 11 = 80 matches the 80 `init_and`/HMR pairs per circuit measured above. This decomposition is my arithmetic from the text, not a tag trace.
  - One CCX per paired product (an AND of two XOR combinations), between CNOT fans.
  - The words are sign-canonical. Some low delta bits are "coded" as first-order Reed–Muller (affine) per 16-address block, so they need no products.
- **How Q reached 430.**
  - brot = 8 keeps the heuristic temporary at 304. At brot ≥ 9 it jumps to 607.
  - The loader workspace (68 to 77) stays below 304.
  - So Q = 86 + 5·8 + 304.

## Conclusion

C-011 holds on the verifier's numbers: ANGLE_k loading is 51.7% of T_total on the 430Q build, and 51.4% on its C60 successor. It is still the largest single term. But it is now only about 289 Toffoli per circuit per pass, and the loaders already use the C-003 ideas.

- **C-008 (J = 9, brot = 11) has no room on this build.**
  - In the official `heuristic_costs(76, 8, 143, 62, brot)`, brot ≥ 9 raises the heuristic temporary from 304 to 607 qubits. The Q floor becomes 86 + 99 + 607 = 792, against 430 now (1.84×).
  - The heuristic T would fall only from 8,086 to 7,306, because Givens rises to 3,150 while inner prep falls to 3,783.
  - To break even, all of T would have to be below about 9,090. That leaves at most about 1,780 Toffoli for all ANGLES, both passes.
  - This is cost-model arithmetic, not a verifier run.
  - Two nearby shapes are not ruled out but are unmeasured:
    - J = 6 at brot 8: 13 circuits, Q floor 438 (+1.9%).
    - brot 7: Q floor 425, Givens 1,950. This risks accuracy on error_1 and error_2, which are already at 19.99 mHa.
- **C-003 (reachable-only loaders) is already used at the frontier.**
  - The address range is already restricted to 1,220.
  - The target-register promise (sign-bit borrowing) is used by all 15 v10 circuits and by 10 of 15 v11 circuits.
  - What remains of C-003 is incremental, for example applying the promise to the five full-XOR v11 circuits (260 Toffoli each, width 128). Its size is unmeasured.

A critic review of this experiment is pending.

## Deviations

All dated 2026-10-28 and recorded after the pre-registration commit 446dbab.

1. **The dataset moved.**
   - At download time, the latest `heliosli/qcc-circuits-live` version was 11 (`v17_sjx`, C60), not the target.
   - I identified the target by version: version 10 is `v15b_sjmixL`, with npz SHA-256 3249dbf46ee6…, the factorization hash that avazaku pins.
   - I downloaded it with `kaggle datasets download heliosli/qcc-circuits-live/10 -f ...` into `external/heliosli-qcc-circuits-live-v10/`, instead of the single planned directory.
   - The v11 download is kept in `external/heliosli-qcc-circuits-live-v11/` and measured as a secondary build.
   - All hashes are in `external_manifest.json`.
2. **The planned notebook was gone.**
   - `somejoint/quantum-circuits-22-44-local-gm-our-chemistry` returned 404. I read the successor, 22-67 (full-XOR chem), as text instead.
   - The design reading may therefore describe a later loader than the v10 circuits. The v11 full-XOR circuits come from it.
3. **The kernel pin was dropped, so the target was verified locally.**
   - Kernel slugs differ from the plan: `rainm4/exp-006-account-430q-v10` and `-v11`, not `-dfthcsos`.
   - Their `dataset_sources` were pinned to `heliosli/qcc-circuits-live/10` and `/11`. The CLI accepted the pin, but the server stripped it (see `kernel/v*/server/kernel-metadata.json`) and mounted the latest version, v11, in both kernels.
   - The script identifies files by SHA-256, so no wrong file set was labelled v10.
   - I did not re-upload the downloaded files to Kaggle, because that would redistribute them.
   - Instead, v10 was verified locally with the same unmodified `python -I dfthcsos/verify.py`, via `run_verify_local.py` in the background. Before starting I checked: 11.16 GB free, AC power.
4. **Added the XOR-oracle promise check.** `xor_oracle_check.py` is a local kickmix simulation that was not in the plan. It characterizes what the loaders assume about target words. It is not a verifier result.
5. **File names.** The inspection outputs are `logs/inspect_local_v10.json` and `_v11.json`, not `logs/inspect_local.json`. The kernel scripts are in `kernel/v10/` and `kernel/v11/`.

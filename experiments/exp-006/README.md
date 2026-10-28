---
id: exp-006
title: Account the public 430Q dfthcsos build (ANGLE share of T_total, widths, design)
task: dfthcsos
tests: [C-011]
direction: D-001
status: planned
date: 2026-10-28
commit: pending
result: pending
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

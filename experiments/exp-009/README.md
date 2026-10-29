---
id: exp-009
title: Package S-002 (sample zip with our src/invsqrt circuit) and pre-register its LB score
task: all
tests: [C-001]
direction: none
status: done
date: 2026-10-28
commit: c78fbce
result: S-002 zip experiments/exp-009/submission.zip, SHA-256 fcb9ce1d713827f485beba4efec9e130131ff010ecf5ba0347bda171f1cb7c99 (13 members; invsqrt is our ff629b09, the rest byte-identical to the sample). Fresh-salt full verify PASS, Q 92, cost 148,977.94 (predictions held). Local score 2.40681 (C-001 refs) or 2.40670 (exact sample refs); LB awaits an approved submission
---

## Hypothesis

C-001 (knowledge/claims.md): the leaderboard's per-task reference costs equal the paper/README references
(invsqrt 260 x 7,988; dqi 1.19128 x 1893^2 x 5,725,461; dfthcsos 3,355,599,588.3). If so, the public LB score of a
submission equals the score computed locally from verifier costs against those references.

This experiment prepares submission S-002. It is exp-004's zip (accepted; sample packaging, `package.py`) with one member
changed: `invsqrt.kmb` becomes our circuit from `src/invsqrt` (exp-008, accepted; code commit 46af961, config
`experiments/exp-008/config_port.json`, canonical SHA-256 `ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917`,
cost 148,977.90 at Q 92 on the default salt). `dqi.kmb` and `dfthcsos/*` stay the official sample files.

Unlike S-001 (sample only, LB factor near 1 on every task), S-002 moves one task by 13.94x. If the LB reproduces the local
score here, C-001 is tested on a submission whose invsqrt term is far from the reference, which the sample alone cannot do.

Baselines:
- exp-004 (accepted): packaging logic, member layout and order, sample member hashes.
- exp-008 (accepted): the invsqrt circuit, verified at default salt (PASS, Q 92, toffoli_count 1,303.99946, cost 148,977.90224).
- exp-001 (accepted): sample dqi cost 24,439,463,583,672.93 and dfthcsos cost 3,355,599,588.3155365.

## Prediction

Written 2026-10-28, before the rebuild, the verify and the packaging.

**1. Rebuild (local, from committed code).** `experiments/exp-008/build.py` with `config_port.json` into an empty work dir
`experiments/exp-009/out/work` gives a `.kmb` whose file and canonical SHA-256 both equal `ff629b09...5917`.

**2. Fresh-salt full verify (Kaggle; the exp-008 critic's prediction, Suggested next 2).** The unmodified
`verify_submission_invsqrt.py` on that exact file, default arguments plus `--salt exp-009-S-002` (no `--seed`, no `--max-x`,
64 shots per x, 200,540,928 shots):
- PASS, Q (`num_qubits`) 92;
- rotation_eps 2.8298390184213153e-13 and worst_error_over_tolerance 0.9999059628540141, both exactly as in exp-008
  (the phase is deterministic, so the salt cannot change them); rotation_count 44, t_count 1, max_toffoli_count 1,315;
- toffoli_count 1,304.000 ± 0.0016 (3 sigma; sigma of the mean 5.4e-4 from the critic's per-shot variance 59);
- cost 148,977.95 ± 0.15;
- `circuit_sha256` `ff629b09...5917`.
A FAIL, a different Q, eps or worst ratio, or a cost outside [148,977.80, 148,978.10] refutes it.

**3. Packaging.** `experiments/exp-009/submission.zip` has exactly exp-004's 13 members in exp-004's order, no directory
entries, ZIP_DEFLATED level 6, fixed metadata. `dqi.kmb` and all 11 `dfthcsos/*` members are byte-identical (SHA-256)
to `data/sample_submission/` and to exp-004's `manifest.json`. `invsqrt.kmb` is byte-identical to the file verified in
step 2. Two independent builds give the same zip SHA-256.

**4. Local score of S-002 (arithmetic from accepted verifier costs; nothing new is measured for dqi or dfthcsos).**
- Against C-001's rounded references: invsqrt 2,076,880 / 148,977.90 = 13.94086, dqi 1.000078, dfthcsos 1.000000,
  giving **2.40681**.
- If the LB instead uses the sample's exact verified costs as references (as public notebooks do): invsqrt 13.94015,
  others 1, giving **2.40670**. Both count as C-001 holding; the 5th decimal separates them (as in exp-004).
- The lead's figure 2.4067 is the second variant; the first rounds to 2.4068. Both are inside the window below.
- A fresh salt changes the invsqrt cost by about 1e-6 relative (prediction 2), which moves the score by about 3e-7.

**5. LB score (read by the submitter after an approved submission; not measured here).**
- **C-001 is refuted if the public LB score of S-002 falls outside [2.4043, 2.4091]** (±0.1% around 2.4067).
- Alternatives, reusing exp-004's reasoning so a refutation can be read:
  - About **2.4428 to 2.4429** (x1.015): the LB references are about 4.5% higher in product than C-001's (the brief's unsourced
    "sample about 1.015").
  - About **2.3464 to 2.3465** (x0.97494, i.e. exp-004's 0.97498 / 1.000043): the public split computes dqi eps+ from about 51,200
    shots (R 1.28553 instead of 1.19126), with the references unchanged.
  - About **0.9999 to 1.0001**, or an error: the invsqrt member was not scored as ours (for example a layout problem), or
    the LB rejects our circuit.
  - Both x1.015 and x0.975 multiply the whole score, so S-001 and S-002 should show the same ratio to their local scores
    if either applies. If S-001's ratio and S-002's ratio differ, the difference is in how the LB treats invsqrt.
- If Kaggle shows per-task values: invsqrt should read 148,977.9 ± 0.2 (or its factor 13.940 ± 0.001), dqi and
  dfthcsos as in exp-001 to within 1e-4 relative.

## Method

- **Inputs.** `src/invsqrt/*.py` and `experiments/exp-008/{build.py,config_port.json}` at commit 46af961 (checked:
  `git diff 46af961 HEAD -- src/invsqrt experiments/exp-008/config_port.json experiments/exp-008/build.py` is empty, and
  the worktree has no changes to them). `data/sample_submission/` unchanged.
- **Step 1, local rebuild.** `python -I -B experiments/exp-008/build.py experiments/exp-008/config_port.json
  experiments/exp-009/out/invsqrt.kmb experiments/exp-009/out/work` with an empty work dir, so tables and LP calibration
  are recomputed, not loaded from exp-008's cache. Then hash the file bytes and the canonical `.kmb` re-serialization
  (`km.Circuit.from_file(...).to_file(buf, 'kmb')`).
- **Step 2, Kaggle verify.** A private CPU script kernel `rainm4/exp-009-s002-invsqrt-salt-verify` (metadata defaults from
  the quantum-stack skill, no datasets). `make_kernel.py` writes it from `kernel_template.py`, embedding:
  - the base64 bytes of the local `out/invsqrt.kmb` from step 1 (the file that goes into the zip), and
  - the committed `src/invsqrt` sources and `config_port.json`.
  The kernel checks the embedded file's SHA-256 against `ff629b09...`, rebuilds the circuit from the embedded sources in an
  empty work dir as a third independent build and checks it is byte-identical, then runs
  `python -I -B invsqrt/verify_submission_invsqrt.py <embedded file> --salt exp-009-S-002` (cwd the competition
  `verifiers/` mount; 4 forked workers). The verifier is the unmodified competition copy, hashed in the kernel.
  About 13 min. The kernel never calls any Kaggle API and never submits.
- **Step 3, packaging.** `experiments/exp-009/package.py` is exp-004's `package.py` with one change: the source of
  `invsqrt.kmb` is `experiments/exp-009/out/invsqrt.kmb`. Member list and order, compression, `ZipInfo` metadata and the
  re-read checks are unchanged. Added checks: each `dqi`/`dfthcsos` member equals exp-004's manifest SHA-256, and the
  `invsqrt.kmb` member equals the SHA-256 the Kaggle verifier reported (`circuit_sha256` and the kernel's file hash).
  A second build checks the zip SHA-256 is reproducible.
- **Step 4.** `results.json` (verifier figures copied from the kernel output, local-score arithmetic), `manifest.json`
  (zip SHA-256 and per-member hashes), README Results and Conclusion.
- The zip, the circuit and downloaded work files stay out of git (`experiments/exp-009/.gitignore`).
- dqi and dfthcsos are not re-verified: their members are the sample bytes, so exp-001's costs apply.
- Nothing in this experiment submits or calls a submit endpoint. The submitter uploads only after the user approves the zip
  SHA-256 in `approvals/S-002.txt`.

## Results

All numbers come from `results.json` (written by `make_results.py c78fbce` from `kaggle_output/exp009/` and
`manifest.json`) and `manifest.json` (written by `package.py`).

**Submission file (S-002).**
- **Zip:** `experiments/exp-009/submission.zip`, 73,809,027 bytes, 13 members.
- **SHA-256:** `fcb9ce1d713827f485beba4efec9e130131ff010ecf5ba0347bda171f1cb7c99`.
- Reproducible: three builds (one before the verify finished, two after) gave this same SHA-256; the two post-verify
  manifests are identical apart from `runtime_s`. Kept out of git by `experiments/exp-009/.gitignore`.

| Member | Size (B) | Compressed (B) | SHA-256 | Equals |
|---|---:|---:|---|---|
| `invsqrt.kmb` | 288,783 | 24,551 | `ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917` | the file verified below (kernel `verified_file_sha256` and verifier `circuit_sha256`); exp-008 `out/port.kmb` |
| `dqi.kmb` | 886,118,180 | 69,819,447 | `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995` | sample, exp-004 |
| `dfthcsos/angle_k_0.kmb` | 1,671,932 | 112,922 | `7bfb3983accc6ff97d6ab41a88deae924f1d1c97cf30e60879d0bff5688a8e25` | sample, exp-004 |
| `dfthcsos/angle_k_1.kmb` | 1,662,896 | 115,853 | `a04b6d0d57ce851b123af265066aaab2ab33353ea049d26acd534727466d72b6` | sample, exp-004 |
| `dfthcsos/angle_k_2.kmb` | 1,665,821 | 116,351 | `5c1b8987bc3fa1a4b8607e470f8c8f1392c22e7a7dbcb228f0ce9ec986e18058` | sample, exp-004 |
| `dfthcsos/angle_k_3.kmb` | 1,666,802 | 117,309 | `16ac67cdcaf3e2c6abdd98c4138ff1ae8a56cfc4ae15622bcdb3d3a3ba1e22cf` | sample, exp-004 |
| `dfthcsos/angle_k_4.kmb` | 1,954,082 | 134,959 | `d21cdd4c7e94196654aab15ebcabfe10ce8d343151a5e8dc3672e76684b6628d` | sample, exp-004 |
| `dfthcsos/angle_k_5.kmb` | 1,948,583 | 133,922 | `63b8d4cba36955e6098321f3b2ef3e34401dd276fa629b2e490d043b1743880b` | sample, exp-004 |
| `dfthcsos/angle_k_6.kmb` | 1,947,980 | 133,745 | `5bf740428e661d035fda860142578f421969e35e0df2e4e024fbf01a7340b378` | sample, exp-004 |
| `dfthcsos/angle_k_7.kmb` | 1,968,527 | 135,539 | `606009582111a22bd549b795c8d115ac8bbeb124bc8da24a80380eca6d34163d` | sample, exp-004 |
| `dfthcsos/angle_k_8.kmb` | 1,957,124 | 136,948 | `57c7cc51f5922fff6e95d76e1f723d4c2d029a241da643b95684d6322157a8fe` | sample, exp-004 |
| `dfthcsos/angle_k_9.kmb` | 1,953,830 | 134,416 | `22cbe2828988ff954fc07fd971a25e6bc04a02c302bf2cc642e4c3535daaad65` | sample, exp-004 |
| `dfthcsos/submission.npz` | 4,537,436 | 2,691,533 | `14d5cc25eb3bf82a9ccb87c811db28d127bef6d28697dd190dc1e875de3bfe69` | sample, exp-004 |

Checks in `manifest.json` (all true):
- member names and order equal exp-004's; no directory entries, duplicates or zip64; `testzip` passes;
- one invsqrt and one dqi file; `angle_k_0..9` contiguous;
- npz keys present, loadable with `allow_pickle=False`, little-endian;
- every member byte-identical to its source; dqi and all 11 dfthcsos members equal both `data/sample_submission/` and
  exp-004's manifest; the invsqrt member equals the verified file; extracted files byte-identical.

Also (`results.json`): the 12 non-invsqrt deflate entries have exp-004's compressed sizes and CRCs. An independent reader
(Windows `tar.exe`, bsdtar) lists the same 13 names in order and inflates `invsqrt.kmb`, `dqi.kmb`, `angle_k_9.kmb` and
`submission.npz` to the same SHA-256s.

**Rebuild from committed code.**
- Local (`out/build.log`, gitignored): empty work dir `out/work`, LP calibration recomputed (130.1 s; worst
  0.9999059628540141, margin 73,111,258, 44 rotations), 198 s total. File and canonical `.kmb` SHA-256 both
  `ff629b09...5917`; `cmp`-identical to exp-008 `out/port.kmb`.
- Kaggle (kernel v1): the embedded local file hashed `ff629b09...` (file and canonical). An independent rebuild from the
  embedded 46af961 sources (each SHA-256-equal to `git show 46af961:src/invsqrt/<file>`) and config (equal to
  `config_port.json`) in an empty work dir took 130.4 s and was byte-identical to it. The downloaded `invsqrt.kmb` and
  `rebuilt.kmb` are `cmp`-identical to the local `out/invsqrt.kmb`.

**Fresh-salt full verify.**
- Kernel `rainm4/exp-009-s002-invsqrt-salt-verify` v1, private CPU script kernel (metadata in `kernel/kernel-metadata.json`),
  status COMPLETE.
- Command `/usr/bin/python3 -I -B invsqrt/verify_submission_invsqrt.py /kaggle/working/exp009/invsqrt.kmb --salt
  exp-009-S-002`, cwd the competition `verifiers/` mount. Verifier SHA-256 `ddef520d...`, the same as exp-008 and local.
- rc 0, stderr empty, 973.3 s wall, peak tree RSS 0.71 GB, system used 0.99 GB.
- Full stdout in `verifier.log` (identical to `kaggle_output/exp009/verify_full.json`).

| Metric | exp-008 (default salt) | exp-009 (salt `exp-009-S-002`) | Change | Pre-registered | Held? |
|---|---|---|---|---|---|
| status | PASS | PASS | | PASS | yes |
| Q | 92 | 92 | 0 | 92 | yes |
| toffoli_count | 1,303.999457656843 | 1,303.999920385329 | +0.00046 | 1,304.000 ± 0.0016 | yes |
| max_toffoli_count | 1,315 | 1,315 | 0 | 1,315 | yes |
| t_count / rotation_count | 1 / 44 | 1 / 44 | 0 | 1 / 44 | yes |
| rotation_eps | 2.8298390184213153e-13 | 2.8298390184213153e-13 | 0 | exact | yes |
| worst_error_over_tolerance | 0.9999059628540141 (x 2) | 0.9999059628540141 (x 2) | 0 | exact | yes |
| toffoli_equivalent | 1,619.3250243907166 | 1,619.3254871192025 | +0.00046 | | |
| cost | 148,977.90224394592 | 148,977.94481496664 | +0.0426 | 148,977.95 ± 0.15 | yes |
| verified_shots | 200,540,928 | 200,540,928 | 0 | 64 x 3,133,452 | yes |
| circuit_sha256 | `ff629b09...` | `ff629b09...` | | `ff629b09...` | yes |

Improvement over the exp-001 sample at this salt: 2,076,774.23 / 148,977.94 = 13.94015; score factor 2.40670.

**Local score of S-002** (`results.json` `local_score`; invsqrt from this verify, dqi and dfthcsos from exp-001's accepted
costs of the byte-identical sample members):

| | invsqrt | dqi | dfthcsos | score |
|---|---|---|---|---|
| factors vs C-001 rounded references | 13.940855 | 1.000078 | 1.000000 | **2.406806** |
| factors vs exact sample costs | 13.940146 | 1 | 1 | **2.406703** |

Both are inside the pre-registered C-001 window [2.4043, 2.4091]. On the same arithmetic, x1.015 gives 2.4428 to 2.4429
and x0.974938 (dqi half-shot eps+) gives 2.3464 to 2.3465.

LB score: **not measured.** Nothing was submitted and no submit endpoint was called.

## Conclusion

- **Every pre-registered local prediction held.**
  - The committed generator (46af961, `config_port.json`) rebuilds `ff629b09...` from an empty work dir, on Windows and on
    Kaggle.
  - The full official verify with a fresh salt passes: Q 92, cost 148,977.94481 (inside 148,977.95 ± 0.15), mean Toffoli
    1,303.99992 (inside 1,304.000 ± 0.0016). eps and the worst ratio are bit-identical to exp-008.
  - The salt moves the cost by 2.9e-7 relative.
- **S-002 is ready for the lead and the user:** `experiments/exp-009/submission.zip`, SHA-256
  `fcb9ce1d713827f485beba4efec9e130131ff010ecf5ba0347bda171f1cb7c99`. It differs from exp-004's zip only in the
  `invsqrt.kmb` member. The submitter should re-hash it against this value immediately before upload, and only after the
  user writes `approvals/S-002.txt`.
- **C-001 is still untested.** Reading the LB number back:
  - inside [2.4043, 2.4091]: C-001 holds (2.40681 means rounded references, 2.40670 exact sample costs);
  - about 2.4428: references about 4.5% higher in product;
  - about 2.3465: dqi eps+ from about half the shots on the public split;
  - about 1.000, or an error: our invsqrt member was not scored as ours;
  - compare S-002's ratio (LB / local) with S-001's. Equal ratios point to a whole-score effect (references or dqi);
    different ratios point to how the LB scores invsqrt;
  - record any per-task values Kaggle shows; invsqrt should read 148,977.9 ± 0.2.

## Deviations

- 2026-10-28: the verify took 973 s on Kaggle, against the "about 13 min" in the task and exp-008's 775 s for the same
  file at the default salt. The cause was not investigated (same kernel type, 4 CPUs; Kaggle host load unknown).
- 2026-10-28: the downloaded calibration cache `kaggle_output/exp009/work/hang_*.pkl` was deleted unloaded, as in exp-008.
  The downloaded `rebuilt.kmb` was moved to `out/kaggle_rebuilt.kmb`. Neither is an input to anything.
- 2026-10-28: a trial `package.py` run before the kernel output existed produced the same zip SHA-256 but failed its
  `invsqrt_member_is_the_verified_file` check, by design (no verify yet); its log is `out/package_pre.log`. The committed
  `manifest.json` is from the post-verify run.

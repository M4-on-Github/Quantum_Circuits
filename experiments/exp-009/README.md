---
id: exp-009
title: Package S-002 (sample zip with our src/invsqrt circuit) and pre-register its LB score
task: all
tests: [C-001]
direction: none
status: planned
date: 2026-10-28
commit: pending
result: pending
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

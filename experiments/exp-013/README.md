---
id: exp-013
title: Package S-003 (our src/invsqrt + our src/dqi port + sample dfthcsos) and pre-register its LB score
task: all
tests: [C-001]
direction: D-002
status: running
date: 2026-10-29
commit: pending
result: pending
---

## Hypothesis

C-001 (knowledge/claims.md), supported form after S-002 (exp-009, LB 2.40670 exactly as predicted): the public LB score
equals the geomean over the three tasks of (sample verified cost / our verified cost), to 5 decimals. S-002 tested it with
one task far from the reference (invsqrt 13.94x). S-003 tests it on a second file with two tasks far from the reference,
and for the first time with a dqi circuit whose failure count can be nonzero, so the dqi R(eps+) term is exercised.

Contents of S-003 (origin per task, user decision 2026-10-29):

| Member | Circuit | Origin | Our improvements |
|---|---|---|---|
| `invsqrt.kmb` | `ff629b09...5917`, byte-identical to S-002's member | ported from marsyas, "VQCC invsqrt 13.94x - full source" (Apache-2.0); our port `src/invsqrt`, built by exp-008/exp-009 | none |
| `dqi.kmb` | `b3354f60...2fd6`, built by `src/dqi` at 7645e03 on Kaggle | ported from SomeJoint (Agniv Banerjee) notebook v14 (Apache-2.0), with the design-lineage caveat in `src/dqi/NOTICE` (jday96314/QuantumAI, unlicensed, deleted) | none |
| `dfthcsos/*` | 10 `angle_k_*.kmb` + `submission.npz` | official sample, byte-identical to S-002's members | none |

Baselines:
- exp-009 (accepted): S-002 packaging (`package.py` logic and member order), the invsqrt member and its fresh-salt cost
  148,977.94481 (exp-008 default salt: 148,977.90224).
- exp-011 (accepted): `src/dqi` at 7645e03 builds `b3354f60...` on Kaggle; cost 422,346,240,055.9 (default) and
  422,346,258,963.8 (salt `exp011-a`), 0 failures in 102,400 shots at both.
- exp-008 (accepted): `src/invsqrt` and `ff629b09...`.
- exp-001 (accepted): the sample's verified costs, which are the LB references (C-001): invsqrt 2,076,774.233715282,
  dqi 24,439,463,583,672.93, dfthcsos 3,355,599,588.3155.

## Prediction

Written 2026-10-29, before the kernel push, the download and the packaging. Arithmetic in `predict.py` (output
`prediction.json`). It imports the official dqi verifier's own `clopper_pearson_upper_bound` and `repetition_overhead`
for eps+ and R at k failures; costs are read from the exp-001, exp-009 and exp-011 `results.json` files. The dqi cost at
k failures is exp-011's mean 0-failure cost times R(k)/R(0).

**1. Kaggle build.** `src/dqi/generate.py` from commit 7645e03 (`git diff 7645e03 HEAD -- src/dqi` is empty at the time
of writing) on a private CPU kernel writes a `.kmb` whose file and canonical SHA-256 are both
`b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6` (as exp-011; near certain). Q 897, static Toffoli
454,477, num_ops 55,778,145, 505,134,467 bytes. About 150 s, about 2 GB.

**2. Kaggle verify at one fresh salt `exp-013-S-003`.** PASS; mean T 440,633 ± 0.01%; failures 0 (P about 0.78),
1 (about 0.19), 2 (about 0.02), 3 or more (about 0.002) (Poisson mean 0.25, the lead's P(>=1) about 22%); cost
4.22346e11 / 4.24286e11 / 4.25937e11 at 0 / 1 / 2 failures. About 220 s, about 4.9 GB. This salt is not the LB's
salt, so its failure count does not predict the LB's; it is one more draw of the failure rate.

**3. Local re-hash.** The downloaded `.kmb` has file SHA-256 `b3354f60...`, and kickmix loads it with canonical SHA-256
`b3354f60...`, Q 897, `num_toffoli_like` 454,477.

**4. Packaging.** 13 members in exp-009's order, exp-009's zip parameters. `invsqrt.kmb` and all 11 `dfthcsos/*`
members are byte-identical to exp-009's manifest; `dqi.kmb` differs from it and equals `b3354f60...` and the file the
Kaggle verifier checked. Two builds give the same zip SHA-256.

**5. LB score (read by the submitter after an approved submission; not measured here).**

| dqi failures on the LB | R | dqi cost | dqi factor | predicted score |
|---|---|---|---|---|
| 0 | 1.19126046 | 4.223462e11 | 57.865942 | **9.30887** |
| 1 | 1.19673150 | 4.242859e11 | 57.601399 | 9.29466 |
| 2 | 1.20138806 | 4.259369e11 | 57.378137 | 9.28263 or 9.28264 (9.2826345 / 9.2826354) |
| 3 | 1.20558432 | 4.274246e11 | 57.178422 | 9.27185 |

- invsqrt factor 13.940146 (exp-009 salt; exp-008 default 13.940150: the score differs by 9e-7, below the 5th
  decimal), dfthcsos factor 1.
- **Failure sensitivity:** each dqi failure multiplies the score by about 0.99847 (x0.998474 for the first,
  x0.998706 for the second).
- **Expected LB value 9.30887** (P about 0.78 under the assumed failure rate).
- **Refutation rule for C-001 on this file:** C-001 is refuted if the public LB score lies outside
  **[9.28262, 9.30888]**, the 0 to 2 failure band widened by one unit in the 5th decimal for the LB's display rounding
  and the salt dependence of mean T (about 5e-8 relative).
  - A value at the 3-failure point 9.27185 (P about 0.002) falls outside the band and so counts as refuted under this
    rule; the readout would note that it matches the 3-failure arithmetic.
  - Sharper sub-prediction: inside the band, the score equals one of the grid points 9.30887, 9.29466,
    9.28263/9.28264 to within ±0.00001. A value inside the band but off the grid does not refute C-001 by the rule
    above, but it fails this sub-prediction and would mean the LB's dqi term is not the full-shot R(eps+) form
    (for example the public split counting failures on part of the shots).
  - About 3.08 or below (dqi factor about 1), or an error: our dqi member was not scored as ours.
- If Kaggle shows per-task values, dqi should read 4.2235e11 (0 failures; 4.2429e11 / 4.2594e11 at 1 / 2) or factor
  57.866 / 57.601 / 57.378; invsqrt 148,977.9 ± 0.2 (factor 13.940); dfthcsos as the sample.

## Method

- **Inputs.** `src/dqi` at commit 7645e03 (the code that ran in exp-011); `experiments/exp-009/out/invsqrt.kmb`
  (`ff629b09...`, the S-002 member, rebuilt from `src/invsqrt` @ 46af961 in exp-009 and verified there);
  `data/sample_submission/dfthcsos/`.
- **Kernel** `rainm4/exp-013-s003-dqi-build-verify`, private CPU script kernel with the skill defaults (internet on for
  `pip install kickmix==1.0.0`, competition source attached, no datasets). Built by `src/tools/build_kernel.py` from
  `kernel_config.json` and `kernel_template.py` (exp-011's template, trimmed): `src/dqi` from git at 7645e03 as a
  base64 zip with per-member SHA-256. Steps, each a child process with memory sampled:
  1. `unpack`: decode the zip, check member paths and hashes.
  2. `build`: `python -I -B src/dqi/generate.py /tmp/exp013/dqi.kmb` (generate.py re-checks `MANIFEST.json`).
  3. `stats`: kickmix load; file and canonical SHA-256, Q, `operation_statistics()`. The kernel stops unless both
     hashes equal `b3354f60...`.
  4. `verify_salt`: the unmodified official `verify_submission_dqi.py <abs kmb> --salt exp-013-S-003`, cwd the
     verifier's directory, as in exp-011.
  5. `export`: copy the `.kmb` to `/kaggle/working/exp013/dqi.kmb`, re-hash the copy, and write
     `verify_salt.meta.json` (salt, verified file hash) for `package.py`'s verified-file check.

  The kernel never calls a Kaggle API and never submits. Ported code runs only inside this Kaggle kernel (user decision
  2026-10-29). The ported code is exactly what exp-011 statically reviewed and ran (same commit, same launcher), so the
  kit gets no new static review; the kernel script is ours, derived from exp-011's reviewed template.
- **Download.** `kaggle kernels output` into the new empty dir `experiments/exp-013/kaggle_output/` (`*.kmb`
  gitignored). Locally, `rehash.py` (ours, `python -I -B`, path passed as an argument) hashes the file and loads it with
  kickmix only (canonical hash, Q, `num_toffoli_like`). Nothing from `src/dqi` runs locally.
- **Packaging.** `src/tools/package.py experiments/exp-013/package_config.json` (exp-009's logic and member order):
  invsqrt from `experiments/exp-009/out/invsqrt.kmb`, dqi from the downloaded file, dfthcsos from the sample;
  `compare` against exp-009's manifest (same: `invsqrt.kmb`, `dfthcsos/*`; different: `dqi.kmb`); `verified_by` for
  both circuits. A second build into a scratch path checks the zip SHA-256.
- **Provenance.** `src/dqi/NOTICE` gains James Day's statement from kg-752895 next to the lineage caveat. NOTICE is not
  in `MANIFEST.json` and not read by the build, so the build input (the 68 kit files and the launcher) is unchanged.
- **Results.** `results.json` by `src/tools/make_results.py results_config.json`; `manifest.json` by `package.py`.
- **Salt.** One fresh salt (`exp-013-S-003`), the lead's instruction. The protocol's 3 dqi salts are not run: exp-011
  already verified this exact circuit at two salts, and the purpose here is the packaging and the LB prediction.
- Nothing here submits or calls a submit endpoint. The submitter uploads only after the user writes the zip SHA-256 in
  `approvals/S-003.txt`.

## Results

Pending.

## Conclusion

Pending.

## Status
- 2026-10-29: pre-registration written (README through Method, `predict.py`, `prediction.json`). Next: commit, then
  build the kernel and push it.

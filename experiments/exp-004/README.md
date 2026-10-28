---
id: exp-004
title: Package the official sample submission as submission.zip and pre-register its LB score
task: all
tests: [C-001]
direction: none
status: done
date: 2026-10-28
commit: db682e7
result: submission.zip (13 members, SHA-256 0d28eaa55bcb6856565fd45300cf2f10219b93587046be1fcd818af2153bcf01, 73,803,082 B) byte-identical to the sample; dfthcsos re-verified from the zip identical to exp-001; LB prediction 1.00004 (refuted outside [0.999, 1.001]) awaits an approved submission
---

## Hypothesis

C-001 (knowledge/claims.md): the leaderboard's per-task reference costs equal the paper/README references
(invsqrt 260 x 7,988; dqi 1.19128 x 1893^2 x 5,725,461; dfthcsos 3,355,599,588.3).
If so, the unmodified sample submission's public LB score equals its local score.

Baseline: exp-001 (critic accepted). The sample passes all three official verifiers. Its costs are invsqrt 2,076,774.2337,
dqi 24,439,463,583,672.93 (0/102,400 failures, R 1.1912604648) and dfthcsos 3,355,599,588.3155. Against the C-001 references
that gives a three-task score of 1.000043.

This experiment changes no circuit. It builds the zip that the submitter agent will upload (only after user approval in
`approvals/S-NNN.txt`) and fixes the prediction for its LB score before any submission exists.

## Prediction

Made 2026-10-28, before the zip was built and before any submission of it.

Packaging (checked locally by this experiment):
- `experiments/exp-004/submission.zip` has exactly 13 members and no directory entries: `invsqrt.kmb`, `dqi.kmb`,
  `dfthcsos/angle_k_0.kmb` ... `dfthcsos/angle_k_9.kmb`, `dfthcsos/submission.npz`.
- Each member is byte-identical (SHA-256) to the file of the same relative path in `data/sample_submission/`, and to the
  hashes exp-001 recorded on Kaggle (`kaggle_output/exp001/summary_kaggle.json`). For example, invsqrt.kmb
  `e2bf8eb6...21e1` and dqi.kmb `959471d0...4995`.
- The official dfthcsos verifier, run on the `dfthcsos/` folder extracted from the zip, PASSes with the exp-001 local
  numbers: cost 3,355,599,588.3155375 and submission_sha256 `276d464f...2695`. Any difference means the zip altered a member.

LB score (to be read by the submitter agent after an approved submission; not measured here):
- **If C-001 holds: public LB = 1.00004** (1.000043 to 6 s.f.).
  - The LB shows 5 decimals, which also separates two ways C-001 could hold. 1.00004 means the LB uses the rounded
    paper/README references. 1.00000 means it uses the sample's exact verified costs as references, as public notebooks
    do (e.g. `REFERENCE` in nb-leoprovorov-open-circuit-crown-22-63). Both count as C-001 holding.
- **C-001 is refuted if the public LB score falls outside [0.999, 1.001].** Seeds cannot account for a deviation that large:
  exp-001's critic found a 4e-7 relative dqi cost spread over 4 seeds, and the sample has 0 dqi failures, so its eps+
  depends only on the shot count.
- Two alternatives, so a refutation can be read:
  - About 1.015. This is the brief's figure, which has no source; the nearest evidence is two LB rows at 1.01496 in
    competition.md (they are not known to be the sample). It would mean the LB references are about 4.5% higher in
    product than C-001's.
  - About 0.97498. This would mean the public LB computes dqi eps+ from about half the shots (51,200, on the "about 50%
    of test data" caveat). With 0 failures that gives eps+ 1.7314e-3 and R 1.28553 instead of 1.19126.
    Arithmetic from the verifier's own `clopper_pearson_upper_bound` and `repetition_overhead`; no verifier run.
- If the LB reports per-task values, each should match the exp-001 costs to within 1e-4 relative.

## Method

- Inputs: `data/sample_submission/` (unchanged, the same bytes exp-001 verified). Nothing is generated or edited.
- `experiments/exp-004/package.py` (config at the top of the file) does the following:
  1. Hash every sample file.
  2. Write `submission.zip` with Python `zipfile`, `ZIP_DEFLATED`, in the layout the competition page specifies
     (competition.md "Submission File": `invsqrt.kmb|kmx`, `dqi.kmb|kmx` and a `dfthcsos/` folder at the archive root).
     That is the layout public assembly notebooks use (heliosli, xhsmsuper, alexchilton: root-level `invsqrt.kmb`,
     `dqi.kmb`, `dfthcsos/<file>`, no directory entries). Fixed member timestamps (1980-01-01) and unix mode 0644 make
     the zip reproducible from the same zlib build.
  3. Re-open the zip and check the layout:
     - `testzip()` CRC check;
     - exactly one `invsqrt.*` and one `dqi.*`;
     - `angle_k_*` numbered 0..n-1 with no gaps.
  4. Stream-decompress every member, SHA-256 it, and compare it with the source file and with the exp-001 Kaggle hashes.
  5. Run the kg-751951 participant checklist items we can check: the npz arrays load with `allow_pickle=False` and
     their float dtypes are little-endian. The 699,050 max-id item is not checked; it is unsourced and the sample is the
     host's own file.
  6. Write `manifest.json`: the zip SHA-256 and size, plus per-member path, size, compressed size, CRC and SHA-256.
- Extract the zip to `out/extract/` (gitignored). Run the official dfthcsos verifier on `out/extract/dfthcsos` with
  default args, the same as exp-001's local run, logging to `logs/`.
- invsqrt and dqi are not re-verified. Their members are byte-identical to exp-001's inputs, and the verifiers seed from
  the circuit bytes, so a re-run would reproduce exp-001 exactly (2.5 h locally for invsqrt; about 9.5 GB for dqi).
- The zip is kept out of git (`experiments/exp-004/.gitignore`, ~0.9 GB). Its path and SHA-256 go in this README and
  `manifest.json`.
- Seeds/salts: verifier defaults.
- No submit endpoint is called by anything in this experiment.

## Results

Packaging (from `manifest.json`, written by `package.py`):

- **Zip:** `experiments/exp-004/submission.zip`, 73,803,082 bytes.
- **SHA-256:** `0d28eaa55bcb6856565fd45300cf2f10219b93587046be1fcd818af2153bcf01`.
- **Members:** 13, with no directory entries and no zip64.
- **Reproducible:** a second, independent build gave the same zip SHA-256 and a manifest identical apart from runtime.
- **Excluded from git:** yes, by `experiments/exp-004/.gitignore`.

| Member | Size (B) | Compressed (B) | SHA-256 | = sample file | = exp-001 Kaggle hash |
|---|---:|---:|---|---|---|
| `invsqrt.kmb` | 579,721 | 18,606 | `e2bf8eb64350a4460a271fc7f1d591ef125b1e276377e9a0f64b96ab3ca321e1` | yes | yes |
| `dqi.kmb` | 886,118,180 | 69,819,447 | `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995` | yes | yes |
| `dfthcsos/angle_k_0.kmb` | 1,671,932 | 112,922 | `7bfb3983accc6ff97d6ab41a88deae924f1d1c97cf30e60879d0bff5688a8e25` | yes | yes |
| `dfthcsos/angle_k_1.kmb` | 1,662,896 | 115,853 | `a04b6d0d57ce851b123af265066aaab2ab33353ea049d26acd534727466d72b6` | yes | yes |
| `dfthcsos/angle_k_2.kmb` | 1,665,821 | 116,351 | `5c1b8987bc3fa1a4b8607e470f8c8f1392c22e7a7dbcb228f0ce9ec986e18058` | yes | yes |
| `dfthcsos/angle_k_3.kmb` | 1,666,802 | 117,309 | `16ac67cdcaf3e2c6abdd98c4138ff1ae8a56cfc4ae15622bcdb3d3a3ba1e22cf` | yes | yes |
| `dfthcsos/angle_k_4.kmb` | 1,954,082 | 134,959 | `d21cdd4c7e94196654aab15ebcabfe10ce8d343151a5e8dc3672e76684b6628d` | yes | yes |
| `dfthcsos/angle_k_5.kmb` | 1,948,583 | 133,922 | `63b8d4cba36955e6098321f3b2ef3e34401dd276fa629b2e490d043b1743880b` | yes | yes |
| `dfthcsos/angle_k_6.kmb` | 1,947,980 | 133,745 | `5bf740428e661d035fda860142578f421969e35e0df2e4e024fbf01a7340b378` | yes | yes |
| `dfthcsos/angle_k_7.kmb` | 1,968,527 | 135,539 | `606009582111a22bd549b795c8d115ac8bbeb124bc8da24a80380eca6d34163d` | yes | yes |
| `dfthcsos/angle_k_8.kmb` | 1,957,124 | 136,948 | `57c7cc51f5922fff6e95d76e1f723d4c2d029a241da643b95684d6322157a8fe` | yes | yes |
| `dfthcsos/angle_k_9.kmb` | 1,953,830 | 134,416 | `22cbe2828988ff954fc07fd971a25e6bc04a02c302bf2cc642e4c3535daaad65` | yes | yes |
| `dfthcsos/submission.npz` | 4,537,436 | 2,691,533 | `14d5cc25eb3bf82a9ccb87c811db28d127bef6d28697dd190dc1e875de3bfe69` | yes | yes |

Checks in `manifest.json` (all true):
- `testzip` CRC check;
- exact member list;
- one invsqrt and one dqi file;
- 10 `angle_k` files, numbered 0..9 with no gaps;
- `submission.npz` present, with U, W, H2_I, H1_I, Hsym_lower and tree_edges (plus the unread `angle_words`);
- all npz arrays load with `allow_pickle=False` and are little-endian (`<f4` floats, `<i8` ints);
- files extracted to `out/extract/` are byte-identical to the sample.

Official dfthcsos verifier on the zip-extracted `out/extract/dfthcsos` (`logs/dfthcsos_from_zip.stdout.json`, local Windows, default args, 512 s wall):

| Metric | exp-001 (local) | exp-004 (from zip) | Change |
|---|---|---|---|
| status | PASS | PASS | none |
| cost | 3,355,599,588.3155365 | 3,355,599,588.3155365 | 0 |
| lambda_eff | 49.30136925057438 | 49.30136925057438 | 0 |
| Toffoli / Q | 93,237 / 730 | 93,237 / 730 | 0 |
| circuits / max width | 10 / 119 | 10 / 119 | 0 |
| verified shots | 254,464 | 254,464 | 0 |
| submission_sha256 | `276d464f...2695` | `276d464f...2695` | identical |

All fields of the verifier output (`status`, `score`, `resources`, `metrics`, ...) are identical to exp-001's local run (`results.json`, `dfthcsos_identical_to_exp001_local`).

invsqrt and dqi were not re-verified. Their members are byte-identical to the files exp-001 verified, so exp-001's costs apply
unchanged: invsqrt 2,076,774.2337, dqi 24,439,463,583,672.93.

LB score: **not measured**. Nothing was submitted.

## Conclusion

- **Packaging prediction held.** The zip has the predicted 13-member layout. Every member is byte-identical to the sample
  file and to the exp-001 Kaggle hashes, and the official dfthcsos verifier reproduces exp-001 exactly from the extracted folder.
- **C-001 is still untested.** The LB part of the prediction waits on a submission.
- The submitter agent can use `experiments/exp-004/submission.zip` (SHA-256 `0d28eaa5...cf01`) once the user approves it in
  `approvals/S-NNN.txt`. It should check the file against this hash first.
- Reading the LB number back:
  - 1.00004 means C-001 holds with the rounded references;
  - 1.00000 means C-001 holds with the sample's exact costs as references;
  - outside [0.999, 1.001], C-001 is refuted. About 0.97498 points to half-shot dqi eps+ on the public split, and about 1.015 to
    different references.
  - The submitter should also record any per-task values Kaggle shows.

## Deviations

- 2026-10-28: the Method guessed the zip at "~0.9 GB". Deflate actually gives 73.8 MB (dqi.kmb compresses 12.7x). The zip is still
  gitignored, since a 74 MB binary does not belong in git and it rebuilds byte-identically from `package.py`.
- 2026-10-28: the first rebuild (reproducibility check) failed on the final rename with WinError 32, because the file was briefly
  locked by another process. Its finished `.partial` file had the same SHA-256 as the first build. `package.py` now retries the
  rename, and the clean rerun gave the same SHA-256 again. Neither event changed any zip content.

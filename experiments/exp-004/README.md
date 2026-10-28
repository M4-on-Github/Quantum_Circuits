---
id: exp-004
title: Package the official sample submission as submission.zip and pre-register its LB score
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

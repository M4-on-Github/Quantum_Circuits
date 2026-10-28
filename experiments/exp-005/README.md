---
id: exp-005
title: Toffoli accounting of the best public 897Q dqi decoder (multiplier cost and multiply share of T)
task: dqi
tests: [C-010]
direction: D-001
status: planned
date: 2026-10-28
commit: pending
result: pending
---

## Hypothesis

C-010 (knowledge/claims.md): the public 897-qubit, 0-failure dqi decoder (about 432,740.56 mean Toffoli per shot, kaggle/digests/2026-10-28.md) spends most of its T on GF(2^12) multiplies at 63 Toffoli each. So a 51-Toffoli multiplier (C-006) would cut its T by at least 8%.

Baseline: exp-003 (critic pending). In the reference decoder, 64.1% of T sits in 58,211 static multiplies (58,206 per shot) of 63 Toffoli each, from kickmix 1.0.0 `gf_mul`. The 897Q decoder uses about 13x fewer Toffolis, so it is a different algorithm. Whether its T is still multiply-dominated is the open question.

This experiment only takes measurements. The downloaded circuit is never submitted, copied into a submission, or used as the base of one (knowledge/user-decisions.md, kg-752010).

## Prediction

Made on 2026-10-28, before downloading the circuit or the generator notebook. Only the dataset's file listing has been seen so far (`dqi.kmb.xz`, 9,144,688 B).

Definitions. All per-shot numbers are means over the verifier's input distribution.
- **T** is the official verifier's `toffoli_count`, the per-shot mean Toffoli-like count.
- **Multiply** means a general (variable × variable) GF(2^12) multiply. That covers kickmix `gf_mul`, its qubit-controlled form `c_gf_mul`, or any custom block that computes a field product of two quantum registers.
- Constant multiplies (0 Toffoli in kickmix) and `gf2_phase_by_product` are not multiplies here.
- **M63** is the per-shot number of multiplies whose core costs exactly 63 Toffoli. For a 75-Toffoli controlled multiply, the core is 63 and the control adds 12.
- **Multiply share s** is the Toffolis inside multiplies (including control overhead) divided by T.
- **Projected 51-Toffoli saving** = 12 × M63 / T. This is the drop-in saving at equal Q if every 63-core multiply became a 51-core one.

C-010 is judged on these numbers:
- **Holds** if s ≥ 50%, every multiply has a 63-Toffoli core, and 12 × M63 / T ≥ 8%.
- **Refuted** if 12 × M63 / T < 8%. That can happen because the share is lower, because the multiplier is already cheaper than 63 (51 or less, so the swap saves nothing), or because the multiplier has some other cost structure.
- **Refuted as stated, with a note,** if s ≥ 50% but the core is not 63 and a 51-Toffoli swap would still save ≥ 8% (core > 63). I would report that separately.
- **Inconclusive** if the circuit has no usable tags and the multiply structure cannot be recovered from the gate stream or the generator source.

My own expectations. Confidence is low throughout, since I have not seen the design.

| Quantity | Prediction |
|---|---|
| Q (verifier `num_qubits`) | 897 |
| T per salt (3 salts) | 432,740.56 ± 1%, that is 428,413 to 437,068. The default-salt figure is from the digest, and the per-shot spread is unknown |
| static `max_toffoli_count` | ≥ T |
| failures per 102,400-shot run | 0 to 2. kg-753424 reports 22 failures in 10.24M shots of the 897Q, about 2.1e-6 per shot, so the Poisson mean is 0.22 per run. P(at least one failure across 3 runs) ≈ 0.48 |
| kickmix's own `@enter:gf_mul`-style tags present | P ≈ 0.6 |
| general multiplies are kickmix's 63-Toffoli `gf_mul` | P ≈ 0.5 |
| multiply share s | point estimate 50%, 80% interval 20% to 75% |
| C-010 holds (per the rule above) | P ≈ 0.35 |

Reasoning for the share prior. 432,740 / 4,095 ≈ 106 Toffoli per code position. That leaves no room for the reference's per-position Forney inversion (315) or for one multiply per position per EEA step. So the decoder must restructure the Chien and Forney work: batching, a different key-equation solver, or shared inversions. Multiplies could still dominate if about one multiply per position remains, or they could be a minority if comparators and unary-iteration machinery dominate.

The dataset was updated at 2026-10-28 15:57 UTC, after the digest. If the downloaded `dqi.kmb` does not have Q = 897, or its salted T is more than 1% from 432,740.56, I will add a Deviation and report on the circuit actually downloaded.

Expected score delta: none, since no circuit is changed. If C-010 holds, a 51-Toffoli build at equal Q would give a dqi improvement factor of T / (T − 12 × M63) over this decoder. That build is a later experiment.

## Method

Downloads (rules from knowledge/user-decisions.md, 2026-10-28):
- **Destination.** Each download goes in its own new directory under `experiments/exp-005/external/`.
  - Circuit: dataset `heliosli/qcc-circuits-live`. Download `dqi.kmb.xz`, `QCC_RELEASE_MANIFEST.json`, `CREDITS.md` and `LICENSE.md` into `external/heliosli-qcc-circuits-live/`.
  - Generator source: notebook `somejoint/quantum-circuits-22-34-local-gm-897-qubit-dqi` via `kaggle kernels pull -m`, into `external/somejoint-897q-dqi-notebook/`. This notebook is credited as the source in the heliosli notebook, cell 8.
- **Records.** I record slug, version (or lastUpdated where the CLI shows no version number), download date and the SHA-256 of every file in `external/SOURCES.md`.
- **Never executed.** Notebooks are read only as text, with `tools/nbtext.py` run under `python -I` from outside `external/`. The `.xz` is a single-stream file, not an archive with member paths. It is decompressed with stdlib `lzma`, and the result is checked against the manifest SHA-256.
- **Not committed.** `*.kmb`, `*.xz` and the external binaries are gitignored (`experiments/exp-005/.gitignore`). Text files such as the notebook source and the manifest stay out of git too. Only hashes are committed.

Measurement runs on one private CPU Kaggle kernel, `rainm4/exp-005-dqi-897q-accounting`.
- **Inputs.** The dataset `heliosli/qcc-circuits-live` is attached as a dataset source, along with the competition data.
- **Kernel defaults.** As in the quantum-stack skill: no GPU, internet on, `pip install kickmix==1.0.0`.
- **No submit.** The kernel calls no Kaggle API and never submits.
- **Identity checks.** The kernel decompresses `dqi.kmb.xz` and checks that its SHA-256 equals both the manifest entry and my local download.

The kernel steps, each in a child process with peak RSS recorded:
1. **count.** Load the circuit with `km.Circuit.from_file` and record Q, `operation_statistics` and canonical SHA-256. Dump it to .kmx and run `src/kmx_tag_count.py`. This gives static Toffolis by tag path, per-instance histograms, and conditioned Toffolis with their condition-bit definitions. The total must equal `num_toffoli_like`. If the circuit uses Toffoli-like ops the counter does not know, that check fails, and I extend the counter.
2. **segsim**, the empirical per-shot breakdown (new tool `src/kmx_segment_sim.py`).
   - Cut the .kmx into segments at tag enter/exit boundaries where the condition stack is empty.
   - Simulate the segments one after another on one `km.Simulator(counting_operations=True)`, with `use_same_registers_as(circuit)`, clearing the counters between segments. This gives the executed Toffolis of each segment.
   - Inputs: shots drawn with the official verifier's own `sample_shots` under a fixed seed (8,192 shots).
   - Attribution: Toffolis go to tag paths in proportion to static counts within a segment. This is exact for segments whose Toffolis share one condition set. The Toffolis in mixed segments are reported.
   - Checks: the segment sum must equal a whole-circuit `sim.do` count on the same inputs, and the value and phase checks must agree.
3. **verify** with the unmodified official verifier on the downloaded circuit, 3 salts: `--salt exp005-a`, `exp005-b`, `exp005-c`. Default shots 102,400, default batch, fork workers. I record T, `max_toffoli_count`, Q, failures, eps+, R and cost.

The multiplier and its cost are taken from:
- the tag names and per-instance histograms, if tags exist;
- otherwise, the generator notebook source read as text, matched to repeated gate-pattern blocks in the .kmx.

Outputs are downloaded into `experiments/exp-005/kaggle_output/`. `results.json` is built by `experiments/exp-005/make_results.py`.

## Results

## Conclusion

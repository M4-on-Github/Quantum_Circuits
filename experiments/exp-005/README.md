---
id: exp-005
title: Toffoli accounting of the best public 897Q dqi decoder (multiplier cost and multiply share of T)
task: dqi
tests: [C-010]
direction: D-001
status: done
date: 2026-10-28
commit: 70659bf
result: C-010 refuted. The released decoder is Q 889, mean T 440,563.80, with no 63-Toffoli kickmix multiplier anywhere (M63 = 0, projected 51-Toffoli saving 0%). Its products are 42-Toffoli GF(2^12) and 99-Toffoli GF(2^24) kernels, which make up 57-76% of T.
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

All numbers come from `results.json`, which `make_results.py` builds at commit 70659bf. The circuit is `dqi.kmb` from `heliosli/qcc-circuits-live`, manifest portfolio `v17_sjx`, canonical .kmb SHA-256 `4ee7a17b…6da4`. It is an external public circuit, measured only.

### Official verifier (unmodified `verify_submission_dqi.py`, Kaggle, 102,400 shots per salt)

| Metric | Prediction | exp-005-a | exp-005-b | exp-005-c | Mean |
|---|---|---|---|---|---|
| Q (`num_qubits`) | 897 | 889 | 889 | 889 | 889 |
| T (`toffoli_count`, mean per shot) | 428,413 to 437,068 | 440,563.99 | 440,563.79 | 440,563.62 | 440,563.80 |
| `max_toffoli_count` (static) | ≥ T | 454,507 | 454,507 | 454,507 | |
| failures (value + phase) | 0 to 2 per run | 1 (0 + 1) | 0 | 0 | |
| ε+ | | 9.1042e-4 | 8.6606e-4 | 8.6606e-4 | 8.8085e-4 |
| R | | 1.19673 | 1.19126 | 1.19126 | |
| cost (`score`) | | 4.16686e11 | 4.14781e11 | 4.14781e11 | 4.15416e11 |
| status | | PASS | PASS | PASS | |

Against the reference decoder (exp-003, cost 2.44395e13), this circuit is 58.83× cheaper on dqi (score factor 3.89). It is not our circuit, so this is context, not a gain. Each verifier run took 216 s wall with a 4.86 GB peak per process.

### Where T goes, by top-level tag (per shot, 8,192 verifier-distributed shots, segmented simulation)

The segmented simulation matched a whole-circuit run on the same inputs in all four workers: equal Toffoli count, phase and qubits, and 0 value and 0 phase errors. The mean was 440,563.77 per shot. Toffolis under a classical condition are 14,524 static, and per shot they execute at fractions of 0.499 (unconvert), 0.015 (unsynthesis) and 0.181 (unextract).

| Stage | Static | Per shot | Share of T |
|---|---|---|---|
| extract | 65,881 | 65,881.0 | 14.95% |
| synthesis | 33,317 | 33,317.0 | 7.56% |
| convert | 68,160 | 68,160.0 | 15.47% |
| scan | 44,275 | 44,275.0 | 10.05% |
| unconvert | 69,343 | 69,262.8 | 15.72% |
| unsynthesis | 54,408 | 41,930.9 | 9.52% |
| unextract | 119,123 | 117,737.1 | 26.72% |

Jet inversions:
- The tags name 56 forward jets (`extract/inverse24 …` + `multiply v`, 269 Toffoli each) and 56 reverse jets (`unextract/reverse …`, 389 Toffoli each).
- That is 36,848 Toffoli per shot, or **8.36% of T**.
- The relabelled Toffoli skeleton of each jet-only sub-kernel (`inverse12 norm`, `inverse12 products`, `inverse24 products`, `reverse start inverse with flag`, `reverse cached phase inverse`) occurs exactly 56 times in the whole circuit, so no untagged copies of these jets exist.

### Multiplier identity and cost

The only tags are the seven stage names, four 0-Toffoli setup tags (`mask_projection`, `initial`, `uninitial`, `restore_masks`), 14 jet sub-kernel names, and a 0-Toffoli `gf_iadd` tag (8,050 instances of X gates adding constants). That makes 26 names in all, and none of them is `gf_mul` or any other multiplier. Two independent analyses of the exported .kmx text support the findings below (Method addendum in Deviations).

- **kickmix 63-Toffoli multiplier.** The relabelled Toffoli skeleton of kickmix 1.0.0's `ixor_gf2_mul` (63) occurs **0** times in the 454,507-gate stream, and its controlled form (75) also 0 times. Controls: the same search finds 2 in a two-multiply kickmix build, and the 63-gate core once inside the controlled build. So **M63 = 0**, and the projected 51-Toffoli saving 12 × M63 / T = **0%**.
- **Semantic classification** (`analysis/kernel_semantics.py`). Every Toffoli's two controls are tested as functions of the segment-start state: whether each is affine, and which qubits it depends on. The affine × affine gates are then 2-coloured into bilinear maps between operand sets A and B. Controls on kickmix builds:
  - `gf_mul` gives one 12 × 12 map;
  - controlled `c_gf_iadd` gives 1 × 12;
  - a 12-bit zero test gives only 1 × 1 maps or non-affine controls;
  - two chained multiplies give two 12 × 12 maps in `restart` mode.
- **Every bipartite product component with both operands at least 12 bits has a Toffoli count that is an exact multiple of 42 or of 99.** In `restart` mode there are 5,040 GF(2^12)-product units of 42 and 1,242 units of 99, and no other size. No component of exactly 63 exists, and no 12 × 12 component exceeds 51 Toffoli.

| Product kernel | Operand widths | Toffoli | Instances (restart mode) |
|---|---|---|---|
| GF(2^12) × GF(2^12), the generic multiplier (template = `reverse norm`) | 12 × 12 | 42 | 1,265 (12 × 12), plus 42-unit pieces of wider components |
| GF(2^12) scalar × GF(2^24) (`reverse scale u/v`) | 12 × 24 | 84 = 2 × 42 | 616 + 56 (12 × 25) + 50 (13 × 24) |
| GF(2^24) × GF(2^24) (`multiply v` and untagged) | 24 × 24 (+1 to 5 extra qubits) | 99 | 662 (24 × 24) + 112 (tagged) |
| GF(2^24) via 3 × 42 | 24 × 24 | 126 | 10 over all widths (4 at exactly 24 × 24) |
| scalar × polynomial folds (synthesis, unsynthesis, convert, unconvert) | 24 × 108…396 | 42 · k | for example 16 × 42 = 672 |

- **Field test** (`analysis/field_test.py`). The test evaluates the kernel text with this script's own Boolean model, with the other inputs fixed at random values, and computes B(a, b) = F(a,b) ⊕ F(a,0) ⊕ F(0,b) ⊕ F(0,0). Results on pure bilinear kernels:
  - **12 × 12 42-Toffoli kernels** (6 tagged-template instances and 3 untagged): B is bilinear and independent of the other inputs, and for every one of the 4,095 nonzero a the map b ↦ B(a, b) has rank 12. So there are no zero divisors, as a GF(2^12) multiplication requires.
  - **84-Toffoli 12 × 24 kernels:** rank 24 for every sampled nonzero scalar and rank 12 for every sampled nonzero vector (256 samples per side).
  - **99-Toffoli and 126-Toffoli 24 × 24 kernels:** rank 24 from both sides.
  - Exceptions among the pure kernels: in 2 of the 84-Toffoli kernels and 1 of the 42-Toffoli 13 × 12 kernels, the sampled minimum rank was 0 on the side whose component has extra qubits. In the one 126-Toffoli convert kernel, the sampled minimum was 12. Those operand sets include qubits outside a 12- or 24-bit core, so a sample can fall where the core part is 0.
  - 36 tested segments that also contain non-bilinear gates give no valid field test and are listed only in `out/field_test.json`.
  - Controls: kickmix `gf_mul` passes. A truncated 12 × 12 polynomial product fails (2,047 zero divisors), and so does a truncated 24 × 24 product (rank down to 16).

### Multiply share of T (per shot)

| Gate class (`results.json` c010.class_table_*) | restart mode | plain mode (no restarts, conservative) |
|---|---|---|
| GF(2^12) × GF(2^12) products (12 × 12) | 53,130 (12.06%) | 52,500 (11.92%) |
| wider field products (12 × 24, 24 × 24, scalar × polynomial) | 281,508 (63.90%) | 196,641 (44.63%) |
| **all field products, s** | **75.96%** | **56.55%** |
| bilinear with an operand under 12 bits (flags, GF(64) pieces, scan) | 54,112 (12.28%) | 5,221 (1.18%) |
| quadratic forms (norms, overlapping supports) | 28,857 (6.55%) | 35,572 (8.07%) |
| non-affine control (chained products, AND trees, inversions) | 0 | 119,522 (27.13%) |
| constant control | 0 | 8,152 (1.85%) |
| CSWAP | 22,104 (5.02%) | 22,104 (5.02%) |
| CCZ | 852 (0.19%) | 852 (0.19%) |

- In plain mode, the inputs of a long untagged run are fixed at the run's start, so a product that consumes an earlier product's output shows up as non-affine.
- `restart` mode starts a new sub-segment at such a gate. Its extra product gates still come out as exact 42- and 99-multiples.
- The scan stage (44,275 = 4,025 × 11) contains no products in either mode.

## Conclusion

**C-010 is refuted** by the pre-registered rule: 12 × M63 / T = 0 < 8%.

- The premise that the frontier decoder spends its T on 63-Toffoli GF(2^12) multiplies is false, even though most of its T is multiplies (s = 57 to 76%, so s ≥ 50% holds).
- Its generic GF(2^12) multiplier already costs 42 Toffoli, below the 51-Toffoli multiplier of C-006.
- Its GF(2^24) products cost 99 Toffoli. That is less than three 42-Toffoli multiplies (126) and far less than four 51-Toffoli ones.
- So dropping in a 51-Toffoli GF(2^12) multiplier saves nothing here. Swapping it in for the 42s would add about 9 × 5,040 ≈ 45k Toffoli per shot, roughly +10% T.
- This is the "multiplier is already cheaper than 63" branch of the refutation rule.

Against the predictions:
- Q (897) and the ±1% T band (432,740.56) both missed. The downloaded release is a newer 889-qubit variant with T 1.81% higher, as the Prediction's dataset-update caveat anticipated.
- Failures (1, 0, 0) fell within the predicted 0 to 2.
- I gave P ≈ 0.5 that the multiplies are kickmix `gf_mul`. They are not.
- My share estimate (50%, 80% interval 20 to 75%) was in the right range: 57% conservative, 76% with restarts.

The scout's notebook reading, checked against the measurements:
- **Confirmed:** Q 889 and mean T ≈ 440.6k (440,563.80).
- **Confirmed:** a confluent-Hermite-style design whose jets cost 269 forward and 389 reverse Toffoli. The tagged sub-kernels sum to exactly these.
- **Confirmed:** 99-Toffoli GF(2^24) product kernels.
- **Refuted for this release:** "289 jet inversions at about 39% of T". There are 112 jets (56 forward, 56 reverse) at 8.36% of T. The 289 and 39% figures likely describe Gluzdov's 883Q, ~468k build, not this file.
- **Partly confirmed:** "24-bit product kernels of 99, 105 or 126". 99 and 126 occur (126 = 3 × 42, 10 instances). No 105-Toffoli product kernel exists in this circuit.

Next steps:
- For the research lead: dqi T on the frontier is dominated by 42-Toffoli GF(2^12) and 99-Toffoli GF(2^24) bilinear kernels. Each Toffoli saved per GF(2^12) product unit is worth about 5,040 / 440,564 ≈ 1.1% of T. Each Toffoli saved per GF(2^24) product is worth 1,242 / 440,564 ≈ 0.28%.
- C-006's 51-Toffoli multiplier is only relevant to decoders built on kickmix's 63-Toffoli `gf_mul`, like the reference.
- A follow-up claim would have to be about beating 42 (or 99) through lower bilinear rank, or about fewer products.

## Deviations

- **2026-10-28, interruption.** The previous experimenter run was cut off by an API rate limit after kernel `rainm4/exp-005-dqi-897q-accounting` v1 had finished and its outputs were downloaded into `kaggle_output/`.
  - This run resumed from the files on disk and re-ran nothing from v1. All v1 outputs (prepare, count, 4 segsim workers, 3 salted verifier runs) were complete and internally consistent: counter total = `num_toffoli_like`, and every segsim check passed.
  - The pre-registration (Hypothesis through Method) was committed in 16bb91a at 15:21 local time, before kernel v1 was pushed (about 15:30).
  - `src/kmx_segment_sim.py`, `tools/test_segsim.py` and `tools/xz_sha.py` come from the interrupted run. The in-kernel equality checks validate `kmx_segment_sim`. Whether `test_segsim.py` was ever run locally is unknown.
- **Circuit differs from the prediction's target.** The release is Q 889 (manifest `v17_sjx`), not the 897Q in the digest, and its T is 1.81% above 432,740.56. As pre-registered, this experiment reports on the circuit actually downloaded.
- **Generator source unavailable.** The notebook slug named in the Method, `somejoint/quantum-circuits-22-34-local-gm-897-qubit-dqi`, no longer resolves. The previous run pulled `somejoint/quantum-circuits-22-67-local-gm-full-xor-chem` instead (`external/SOURCES.md`). It embeds no DQI generator, so the multiplier structure was recovered from the gate stream alone.
- **Method addendum, the second kernel and local text analysis.** The tags turned out to be coarse: 26 names covering stages and jets only. The Method's fallback, "repeated gate-pattern blocks in the .kmx", needed the full gate text.
  - Second private kernel, `rainm4/exp-005-dqi-kmx-dump` v1 (`kernel_dump/`). It checks the dataset's `dqi.kmb.xz` SHA-256 against the exp-005 download, loads it with kickmix only, writes the .kmx (SHA-256 `61a4305d…`) and xz-compresses it to 16.6 MB (`kaggle_output_dump/exp005dump/dqi.kmx.xz`, gitignored). It never calls the Kaggle API or submits.
  - Local analysis parses that text with our own scripts under `python -I`, and nothing in it is executed: `analysis/kmx_skeleton.py`, `patterns.py`, `fingerprint_search.py`, `kernel_semantics.py` (plain and `restart` modes) and `field_test.py`.
  - The pre-registered definitions (M63, s, the 51-swap saving) are unchanged.
  - The "multiply" class is made operational as a bipartite bilinear component with both operands ≥ 12 bits. Pure kernels are spot-checked as field-type products.
  - `restart` mode was added after the plain-mode run showed chained products being counted as non-affine. Both modes are reported.

---
id: exp-011
title: Apache-2.0 port of SomeJoint's 897-qubit dqi generator (src/dqi), built and verified on Kaggle
task: dqi
tests: [C-016]
direction: D-002
status: running
date: 2026-10-29
commit: pending
result: pending
---

## Hypothesis
C-016 (knowledge/claims.md): a generator we write reproduces the cost of SomeJoint's public 897-qubit dqi decoder within 1% on the unmodified official verifier, with 0–2 failures in 102,400 shots. That cost is about 4.22346e11 at Q 897 and mean T 440,633. The generator is either a properly licensed port of SomeJoint's own generator or our re-implementation of its design.

## Source and licence (found before pre-registration; details in `external/SOURCES.md`)
- **The generator.** It is embedded as a 73-entry `SOURCES` dict in **version 14** of SomeJoint's notebook (`somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi/14`, id 140675727, title "22.34 Local GM: 897-Qubit DQI"). The ipynb SHA-256 is `b7e42f52…43ff`.
  - Its `blocks/dqi/pro-q2-897/source/build_897.py` states its output: SHA-256 `b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6`.
  - The v14 text states Q 897, mean T 440,633.0, at most 454,477, 0 failures at the default seed, and cost 4.22346e+11 (57.8659×).
- **Licence: Apache-2.0.** It is stated twice:
  - an embedded `LICENSE` file with the full Apache-2.0 text, byte-identical to the competition's `kickmix/LICENSE.txt`;
  - the credits cell: "the notebook code is Apache-2.0".

  The decoder files carry no per-file headers.
- **Provenance caveat**, recorded here and in `src/dqi/NOTICE`. The design lineage runs through jday96314/QuantumAI on GitHub.
  - That repository states no licence, and it now returns HTTP 404.
  - Alex Chilton's 883-qubit decoder was "rebuilt from their code".
  - SomeJoint describes its own decoder as "rebuilt from scratch" from Chilton's design and licenses it Apache-2.0.

  So the code we port has a clear open-source licence from its author, and the lead's porting rule applies. The unlicensed upstream is a design-lineage risk that we could not check textually.
- **The v15 file is a different circuit.** heliosli/qcc-circuits-live v15's `53d8b2ed…` is SomeJoint's **v20** decoder (team-1028-stream), not the v14 one. Its build.py states `53d8b2ed…` and its notebook states mean T 430,822.9 and cost 4.12943e+11.
- **Independent rebuild.** saurabhkumar234's notebook states a byte-identical rebuild of `build_897.py` (`b3354f60…`, Q 897, T_static 454,477, num_ops 55,778,145).

## Prediction
Written before any build or verify.

1. **Bytes.** The `.kmb` that `src/dqi` writes with PyPI kickmix 1.0.0 on a Kaggle CPU kernel is **byte-identical to `b3354f60…`** (confidence about 80%).
   - It is **not** byte-identical to the v15 file `53d8b2ed…` (certain: different design and different T).
   - If the bytes differ, the gate-level circuit should still have Q 897 and static T 454,477.
2. **Static figures.** Q **897**, static Toffoli (`max_toffoli_count`) **454,477** and num_ops **55,778,145**. These are exact if the bytes match.
3. **Default salt.** With identical bytes, the seed is the same as SomeJoint's run, so the result is fixed:
   - mean T 440,633.0 (± 0.1);
   - failures **0**, eps+ 8.6606e-4, R 1.19126;
   - cost **4.22346e11** (± 0.001%).
4. **Fresh salt `exp011-a`.**
   - Mean T 440,633 ± 0.01%. exp-005's spread over three salts was ±0.0001%.
   - Failures: 0 (P about 0.7), 1 (about 0.25) or 2 (about 0.05). The basis is SomeJoint's 1, 0, 0, 1 failures at four seeds and kg-753424's 1 in 100,000 to 500,000.
   - Cost **4.2235e11** at 0 failures, 4.2429e11 at 1 and 4.2594e11 at 2.
   - The R values come from the verifier's own `clopper_pearson_upper_bound` and `repetition_overhead`: R = 1.19126, 1.19673, 1.20139 and 1.20558 for 0 to 3 failures.
5. **Score impact** if it holds: the dqi improvement factor is 2.44395e13 / 4.22346e11 = **57.87**, so ×3.87 on the three-task score.
6. **Kernel anatomy**, by exp-005's analysis tools run on our `.kmx`:
   - 0 copies of kickmix's 63- and 75-Toffoli multiplier templates;
   - product kernels of the same two skeleton families as exp-005's 889Q measurement, the 42-Toffoli GF(2^12) and 99-Toffoli GF(2^24) units;
   - restart-mode unit counts within ±3% of exp-005's 5,040 (42) and 1,242 (99). heliosli's 889Q circuit appears to be a narrowing of this decoder: static 454,507 against 454,477.
7. **Resources.**
   - Build: about 1–3 min on Kaggle CPU, peak RSS about 5 GB (the authors' README says about 5 GB).
   - Each verify: 370–450 s and about 9.5 GB peak (exp-001, exp-003).

**Refutation rule (fixed now).** C-016 is refuted if either verify run:
- reports FAIL;
- or reports a cost outside 4.22346e11 ± 1%, that is [4.18123e11, 4.26569e11]. At this T, 3 or more failures (+1.20%) fall outside.

A byte mismatch with `b3354f60…` alone doesn't refute C-016, because the claim is about cost. It would be reported as a failed prediction 1.

## Method
- **Baselines**
  - exp-001 (accepted): the sample dqi, Q 1,893, cost 2.44395e13.
  - exp-005 (accepted): the anatomy of heliosli's 889Q modification, and the analysis tools in `experiments/exp-005/analysis/`.
- **Port: `src/dqi/`**
  - `src/dqi/pro_q2_897/` holds the 69 files of v14's `blocks/dqi/pro-q2-897/source/`, copied verbatim with unchanged bytes. Each file's SHA-256 equals v14's `SOURCE_HASHES` entry and is listed in `src/dqi/MANIFEST.json`.
  - Our own files:
    - `src/dqi/LICENSE` (the Apache-2.0 text);
    - `src/dqi/NOTICE` (attribution, lineage and the provenance caveat);
    - `src/dqi/__init__.py`;
    - `src/dqi/generate.py`, our launcher.
  - The launcher checks the manifest, then does what `build_897.py` does:
    - it maps the kit's `circ` module to kickmix;
    - it loads `final_decoder/decode.py` by file spec;
    - it allocates S0..S69 (12 qubits each) and E0..E4094 (12 bits each);
    - it calls `decode(b, S, E)` and prepends the REGISTER metadata;
    - it writes `.kmb` and a build record (SHA-256, Q, T_static, num_ops, num_bits, seconds).
  - We never run the downloaded `build_897.py`.
  - The kit's directory layout is kept unchanged, because its modules resolve bare-name imports (`kernels`, `scalar`, `common`, …) through `sys.path` entries relative to their own files.
- **Local work** (small memory only): file hashes, the manifest check, and an import of the kit modules without calling `decode` (smoke test). The full build needs about 5 GB, so it runs on Kaggle.
- **Kaggle kernel** `rainm4/exp-011-dqi-897-port-verify`: a private CPU script kernel with internet on and `pip install kickmix==1.0.0` pinned. `src/dqi` ships inside the script as base64 and is hash-checked after decoding. The steps run as child processes, with memory sampled by the parent:
  1. `build`: build with `src/dqi/generate.py`, recording time and peak RSS.
  2. `stats`: load the `.kmb` with kickmix, then record `num_qubits`, `operation_statistics()`, the canonical SHA-256 (the verifier's `_circuit_sha256`) and the file SHA-256. Compare them with `b3354f60…` and `53d8b2ed…`.
  3. `dump`: `to_file(kmx)`, then compress with lzma preset 6, as in exp-005, for the local anatomy.
  4. `verify_default`: `python verify_submission_dqi.py <abs .kmb>`, the unmodified official verifier with no salt.
  5. `verify_salt`: the same with `--salt exp011-a`.
- **No downloaded circuit goes in.** Only the circuit our code builds is measured or verified. The kernel never calls any Kaggle API and never submits. The built `.kmb` stays in `/tmp` and is not written to the kernel output.
- **Local anatomy.** Run on the downloaded `.kmx.xz` under `python -I -B`:
  - `experiments/exp-005/analysis/kmx_skeleton.py`, `fingerprint_search.py` and `kernel_semantics.py` (restart mode);
  - `src/kmx_tag_count.py` (tag-attributed Toffoli totals).

  Compare the results with exp-005's `results.json`.
- **Salts.** The default and `exp011-a`. This is the lead's instruction (default plus one fresh salt), fewer than the protocol's 3 salts for dqi.

## Results
(pending)

## Conclusion
(pending)

---
id: exp-011
title: Apache-2.0 port of SomeJoint's 897-qubit dqi generator (src/dqi), built and verified on Kaggle (reproduction, not our design)
task: dqi
tests: [C-016]
direction: D-002
status: done
date: 2026-10-29
commit: 7645e03
result: prediction held. Our port of SomeJoint v14 (Apache-2.0) builds byte-identical b3354f60 on Kaggle; official verify PASS, Q 897, static T 454,477, mean T 440,633.0, 0 failures at default and exp011-a, cost 4.22346e11 both (57.87x the sample). A reproduction of SomeJoint's design, not ours
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
All numbers come from `results.json` (built by `make_results.py` from `kaggle_output/exp011/` and `anatomy/compare.json`). Verifier output: `verifier.log`.

**What was run.**
- Kernel `rainm4/exp-011-dqi-897-port-verify` v1 (id 141513052): private CPU script kernel, internet on, competition source attached, no datasets.
  - Pushed 2026-10-29 13:44 UTC and COMPLETE at 13:59 UTC; 871 s of steps.
  - Machine: Python 3.13.15, 4 CPUs, numpy 2.1.3, kickmix 1.0.0 (pinned).
  - The pulled kernel code equals `kernel/exp011_verify.py` apart from CRLF line endings.
- Verifier: the unmodified `verify_submission_dqi.py`, SHA-256 `f14274bc…5e65`, the same as the local `data/` copy and exp-005.
- The kit ran only inside the kernel. Nothing from `src/dqi` was executed locally.

**Build and verify, against the pre-registered prediction**

| Metric | Prediction | Default salt | Salt `exp011-a` |
|---|---|---|---|
| `.kmb` SHA-256 (file and canonical) | `b3354f60…` (about 80%) | `b3354f60…` for both: **byte-identical** | same circuit |
| Equal to v15 `53d8b2ed…` | no | no | no |
| Status | PASS | PASS | PASS |
| Q | 897 | 897 | 897 |
| Static Toffoli (`max_toffoli_count`) | 454,477 | 454,477 | 454,477 |
| num_ops | 55,778,145 | 55,778,145 | 55,778,145 |
| Mean Toffoli (`toffoli_count`) | 440,633.0 ± 0.1 (default); ± 0.01% (salt) | 440,632.998 | 440,633.018 |
| Failures (value + phase) | 0 (default); 0 to 2 (salt) | 0 (0 + 0) | 0 (0 + 0) |
| eps+ | 8.6606e-4 at 0 failures | 8.66059e-4 | 8.66059e-4 |
| R | 1.19126 at 0 failures | 1.191260 | 1.191260 |
| Cost (`score`) | 4.22346e11 ± 0.001% (default); 4.2235e11 at 0 failures (salt) | **422,346,240,055.9** | **422,346,258,963.8** |
| Inside the refutation window [4.18123e11, 4.26569e11] | | yes | yes |

The mean over the two salts is 4.223462e11. The two costs differ by 4.5e-8 relative.

**Against the baselines** (these are factors for the ported circuit, not for anything of ours)

| Baseline | Its cost | This circuit | Factor |
|---|---|---|---|
| exp-003 / exp-001, sample dqi (reference decoder, Q 1,893) | 2.44395e13 | 4.22346e11 | **57.87 improvement**, so ×3.868 on the three-task score |
| exp-005 critic run, heliosli's public 889Q circuit, default salt | 4.14781e11 | 4.22346e11 | **1.0182 more expensive**: Q 897 vs 889 gives (897/889)² = 1.0180, and mean T 440,633.0 vs 440,564.0 adds the rest |

**Resources** (Kaggle, peak VmHWM sampled over each child's process tree)

| Step | Prediction | Wall | Peak memory |
|---|---|---|---|
| build (`src/dqi/generate.py`) | 1 to 3 min, about 5 GB | 153.5 s | 2.07 GB |
| stats (load, canonical hash) | | 6.0 s | 2.05 GB |
| dump (`to_file(kmx)` 9.2 s, lzma 250.6 s) | | 260.1 s | 0.53 GB |
| verify, default salt | 370 to 450 s, about 9.5 GB | 222.7 s | 4.86 GB |
| verify, `exp011-a` | 370 to 450 s, about 9.5 GB | 222.1 s | 4.86 GB |

- Build time held. Build memory and both verify figures came in lower than predicted.
- The verify figures match exp-005's 889Q runs (216 s, 4.86 GB). The prediction had wrongly carried over the sample circuit's figures.

**What the kit actually ran** (`build.json`, recorded by our launcher inside the kernel)
- The manifest check passed: all 68 kit files equal `MANIFEST.json`.
- 58 kit modules were imported: every kit `.py` except `build_897.py`. All 58 are covered by the static review.
- Third-party modules imported during the build: only `kickmix` (plus its alias `circ`, which the launcher sets).
- stdlib modules first imported during the build: `argparse`, `base64`, `datetime`, `email`, `gettext`, `importlib`, `ipaddress`, `quopri`, `urllib`, `_sysconfigdata…`.
  - No kit file imports `urllib`, `email`, `ipaddress`, `base64`, `quopri` or `datetime` (static review, `kit_import_tops`). So these came from kickmix or from stdlib internals. Which one exactly was not determined.
- Every bare-name kit import resolved to a kit file. None came from site-packages.

**Kernel anatomy.** Run locally on the exported `.kmx` text only (`dqi.kmx.xz`, SHA-256 `fcb7e53e…`; decompressed `.kmx` SHA-256 `a29b01cb…`). We used our own scripts under `python -I -B` (`tools/run_anatomy.sh`; outputs in `anatomy/`).

| Measure | Prediction | exp-011 (897Q, this build) | exp-005 (889Q) |
|---|---|---|---|
| kickmix 63-Toffoli `ixor_gf2_mul` template copies | 0 | 0 | 0 |
| kickmix 75-Toffoli controlled template copies | 0 | 0 | 0 |
| GF(2^12) 42-Toffoli product units (restart mode) | 5,040 ± 3% | **5,040** | 5,040 |
| GF(2^24) 99-Toffoli product units (restart mode) | 1,242 ± 3% | **1,242** | 1,242 |
| `kmx_tag_count` total (must equal `num_toffoli_like`) | | 454,477 (equal) | 454,507 |
| Static conditioned Toffoli | | 14,326 | 14,524 |
| Static T by top tag: convert / unconvert / unextract | | 68,352 / 69,535 / 118,709 | 68,160 / 69,343 / 119,123 |
| Static T by top tag: extract, synthesis, scan, unsynthesis | | 65,881, 33,317, 44,275, 54,408 | identical |
| Restart-mode components 12×24 of 84 / 12×12 of 42 | | 584 / 1,329 | 616 / 1,265 |

- The two circuits have the same product-unit inventory.
- They differ by 30 static Toffoli and 8 qubits, all in convert (+192), unconvert (+192) and unextract (−414).
- In the 889Q circuit, 32 of the 84-Toffoli 12×24 components are split into 64 42-Toffoli 12×12 components (32 × 84 = 64 × 42).
- This is consistent with exp-005's reading that heliosli's 889Q circuit is a narrowing of this decoder. The anatomy shows where the two differ, not how the narrowing was done.

## Conclusion
**The prediction held, and C-016 is not refuted.** Every pre-registered circuit and cost prediction came out as stated:
- the build is byte-identical to `b3354f60…`;
- Q 897, static T 454,477, num_ops 55,778,145;
- mean T 440,633.0 at the default salt;
- 0 failures at both salts;
- cost 4.22346e11 at both salts, well inside the ±1% window;
- the anatomy, with 0 kickmix multiplier copies and exactly 5,040 / 1,242 product units.

The only misses were the resource estimates. The verify took 222 s at 4.86 GB, not 370 to 450 s at 9.5 GB, and the build peaked at 2.07 GB, not 5 GB. Two salts were run, not the protocol's three (lead's instruction, see Method). C-016 moves only if the critic accepts this experiment.

**This is a reproduction of SomeJoint's design, not our design.**
- The circuit, its decoder and all 68 kit files are the work of SomeJoint (Agniv Banerjee) and the contributors credited in `src/dqi/NOTICE`.
- They are used under Apache-2.0, with the design-lineage caveat about the unlicensed, now-deleted jday96314/QuantumAI repository.
- Our part is only the launcher (`src/dqi/generate.py`), the manifest, the `.gitattributes`, and the Kaggle build-and-verify harness.

**What it gives us.** We now have a regenerable, licensed baseline for dqi at cost 4.22346e11, a factor of 57.87 over the sample. Being regenerable means the circuit can be rebuilt from committed code, which the winner-code rule requires.
- Any submission using it must say "ported from SomeJoint v14 under Apache-2.0" (user decision of 2026-10-29).
- It is still 1.8% more expensive than heliosli's public 889Q narrowing of the same decoder, which is also not ours.

**Next steps**
- Critic review of this experiment.
- Any improvement is a later experiment, with its own pre-registration and its measured delta against this ported baseline (cost 4.22346e11, Q 897, mean T 440,633).
- Where to look: the 8-qubit and 30-Toffoli difference to the 889Q circuit sits in convert, unconvert and unextract. Q enters squared, so each qubit saved is worth about 0.22% of cost.

## Deviations
- **2026-10-29, file count.** The kit has **68** files, not 69 as written in the Method above. v14's 73 `SOURCES` entries are 4 notebook helpers, `LICENSE` and 68 files under `pro-q2-897/source/`. `src/dqi/MANIFEST.json` lists all 68, and each one's hash equals v14's `SOURCE_HASHES` entry.
- **2026-10-29, build blocked by the permission system.** The local import-only smoke test (`python -I -B src/dqi/generate.py --import-only ...`) was denied by Claude Code's auto-mode classifier, reason "Code from External".
  - Building on a Kaggle kernel would run the same third-party code, so it was not pushed either.
  - Done without running the kit:
    - source located, with its licence recorded (`external/SOURCES.md`);
    - port with a hash manifest (`src/dqi/`);
    - parse-only static review (`static_review.json`);
    - kernel prepared but not pushed (`kernel/`).
  - No build, verify or anatomy result exists yet.
  - The predictions above stand unchanged until the user decides whether the ported code may run.
- **2026-10-29, permission granted, Kaggle only.** The user approved running ported open-source generator code in private Kaggle kernels only (`knowledge/user-decisions.md`, section of 2026-10-29). The status changed from "blocked" to done.
  - `src/dqi` was never run locally, and the local block was not worked around.
  - The planned local import-only smoke test was dropped, and nothing replaced it locally.
  - Locally we only parsed files (`ast`) and checked hashes.
- **2026-10-29, static review extended before the push.** The first review (`static_review.json`) had five gaps:
  - it covered only the kit, not our launcher or the kernel script;
  - its watch-list missed network and subprocess *imports*, `sys.path` / `sys.modules` / `globals()` mutation, `__code__` / `__globals__` access, and `open()` write modes;
  - it gave no reachability for write sites;
  - it had no check that bare-name imports resolve inside the kit;
  - it said nothing about the non-`.py` files.

  `tools/static_review_run.py` → `static_review_run.json` closes those gaps. It covers all 59 kit `.py` files, `src/dqi/generate.py` and `kernel/exp011_template.py`, in five categories: imports, file writes, network, subprocess and dynamic loading. Findings for the kit:
  - **Network and subprocess.** None. No kit file imports socket, http, urllib, requests, subprocess, multiprocessing or os.
  - **File writes.**
    - `build_897.py`, which we do not run.
    - `exp/confluent_extract/model.py:199`, inside `main()`, which is called only under `if __name__ == '__main__'`.
    - `exp/decoder/safe_bridge.py:24`, under its `__main__` guard.
    - The three `audit.py` hits are `list.copy()`, which are false positives.
    - So importing the kit writes no file.
  - **Dynamic loading.**
    - 40 `sys.path.insert` calls and 3 `sys.path[:0]` assignments, all of kit-relative directories derived from `__file__`.
    - 13 `types.FunctionType` clones of kit functions with rebound globals (`fn.__code__` of kit functions; no code from strings).
    - `importlib`, `exec_module` and `sys.modules` writes only in `build_897.py`.
    - No `exec`, `eval`, `compile`, `__import__`, `pickle`, `marshal` or `ctypes` anywhere.
    - 9 `json.loads` reads of the kit's own `.json` data files.
  - **Bare-name imports.** Every one resolves to a kit file or package (none unresolved), and no kit name shadows a stdlib module.

  Our files: the launcher writes only `OUT.kmb` and its `.build.json`, and loads `final_decoder/decode.py` by file spec. The kernel uses `subprocess` for `pip install kickmix==1.0.0` and its own child steps, and writes only under `/tmp/exp011` and `/kaggle/working/exp011`. The kernel record (`build.json`) confirmed at run time which kit modules ran (58) and that the only third-party module was kickmix.
- **2026-10-29, `src/dqi` changes before the push** (commit 7645e03). The 68 kit files were not touched.
  - Removed our docstring-only `src/dqi/__init__.py`, so our additions are exactly the launcher `generate.py`, `MANIFEST.json` and `.gitattributes`, as the lead directed. Nothing imported `src/dqi` as a package.
  - Rewrote `NOTICE` to quote the lineage evidence: jday96314/QuantumAI states no licence and now returns 404; Chilton "Rebuilt it from their code"; SomeJoint "rebuilt from scratch". It also lists our modifications and says what is whose.
  - `generate.py` now also records the stdlib and third-party modules imported during the build.
  - The kernel docstring now says the circuit is SomeJoint's.
  - The Method's reference to `src/dqi/__init__.py` and its "our own files" list are superseded by this.
- **Prediction 7, resources, missed.** See Results.
- **`verifier.log`.** The kernel saved each verifier's stdout separately (`kaggle_output/exp011/verify_*.stdout.txt`). `verifier.log` joins the two, with each command line, cwd, return code and wall time from `runs.json`. Both stderr logs are empty.
- **The built `.kmb` was not downloaded**, as planned. Only the lzma-compressed `.kmx` text (16.6 MB, gitignored) left the kernel, and it was used for text analysis only. The circuit is rebuilt from `src/dqi/generate.py`.

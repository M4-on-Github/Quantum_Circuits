---
id: exp-008
title: Our own invsqrt generator against the public 63-qubit frontier (C-014)
task: invsqrt
tests: [C-014]
direction: D-002
status: done
date: 2026-10-28
commit: 46af961
result: C-014 refuted for this generator. Our src/invsqrt port passes the full official verify at Q 92, cost 148,977.90 (13.940x vs exp-001), 1.451x the 63Q frontier's 102,664.24. It is byte-identical to marsyas's stated ff629b09, not to the frontier. Pre-registration 1 held on every figure.
---

## Hypothesis

C-014 (knowledge/claims.md): a generator we write reproduces the public invsqrt frontier, 63 qubits at cost 102,664.24 (Toffoli-equivalent C about 1,629.6 per shot, about 1,334.5 mean Toffoli; busyaprime lineage, the 172-AND variant), within 1% on the unmodified official verifier.

Baseline: exp-001 (accepted). The sample invsqrt passes at Q 260, C 7,987.59, cost 2,076,774.23.

## What the public design study found (before any build)

All downloads are in `experiments/exp-008/external/` (gitignored), listed with SHA-256, version and licence in `provenance.json`. Code was read as text only (`nb_to_text.py` dumps notebook JSON; nothing downloaded was imported or run). The one downloaded circuit was loaded only through kickmix (`analyze_public.py`) and the kickmix `.kmx` text it wrote (`src/kmx_value_sim.py`, our lane simulator). All Python ran with `-I -B`.

**The frontier circuit** (`invsqrt.kmb`, SHA-256 `07314803...`, busyaprime/33-qcc-v8-members v4, Apache-2.0), measured by us:
- Q 63; static Toffoli-like 1,402 (1,159 CCX, 194 CSWAP, 49 CCZ); 41 fine rotations (`num_z_pow` level 4), 1 T; 45,722 instructions; 951 HMR; 128 conditioned blocks.
- Lane simulation over 193,606 sampled legal x (`src/kmx_value_sim.py`): mean executed Toffoli 1,334.496; x restored, scratch clean. With the stated cost 102,664.24 this gives C = 1,629.59, so rotations are about 295 Toffoli-equivalents (41 x 28.8 T / 4 at eps about 2.4e-13).
- 63 qubits are nonzero on some lane continuously from line about 4,000 to 37,000 of 45,722. The width is not one bottleneck stage; every stage is packed to the cap.
- Structure: normalization (about 91 Toffoli), an 8-bit coefficient lookup synthesized as an AND network, an H/L output split with the high word phased first (Z_POW block at lines 16,711-17,090) and the low word phased after the Horner rows (lines 27,125-27,380), then uncompute.

**Lineage and generators.** The frontier is not produced by any from-source generator:
- busyaprime's file is mrmeows' 63-qubit file (`0766a111...`, 20.0565x) with the 186-AND main lookup re-synthesized to 172 ANDs; "everything outside that region is his, byte for byte" (dataset README, NOTICE).
- mrmeows' reproducer (`invsqrt_20p056505_complete/generate.py`, read as text) takes a bundled frozen circuit (`input/recovered_20p032119.kmx`) and applies a five-line CCX rewrite; its `--replay-upstream` path starts from a "bundled frozen round9 source", and "the yet-earlier ancestral stages before that frozen round9 input are preserved but are not asserted to be replayed" (its README).
- So reproducing the 63-qubit file from that chain means embedding a downloaded circuit, which the safety rules forbid. The rest of the lineage (Gluzdov 84Q, Phuc Thai 82Q, busyaprime 78Q, mrmeows 76 to 63Q) is described in prose as about fifteen rounds of gate-level storage, uncomputation and phase rewrites.
- The closest true from-source ancestor is marsyas (Houssem Alayet), "VQCC invsqrt 13.94x - full source" (Kaggle notebook, Apache-2.0 stated in its text): it fits the tables, calibrates the angles by LP, builds the circuit and runs an exact-domain post-pass, all from code. Its own figures (not ours): Q 92, mean Toffoli 1,304, 44 rotations, cost 148,978.

**Licence path.** marsyas's code is Apache-2.0, so we port it with attribution (notice in the docstrings, like `src/angleload`) to `src/invsqrt/`, and then change it ourselves. No downloaded circuit enters any output.

## Prediction

Written 2026-10-28, before any generator code exists.

1. **Port.** Our port of the marsyas pipeline (`hsplit` path: F0 28, FT 19, F2 8, G0 1, sd, dropA 5, LB 21, S 20, mdel, nested windows 17:11,10;15:9,8;13:7,6;11:5,4;9:3,2;7:1,0) builds a circuit that passes. Predicted: Q 92, mean Toffoli 1,304 ± 5, 44 rotations, cost 148,978 ± 1%. It is byte-identical to marsyas's stated output SHA-256 `ff629b09...` only if PyPI kickmix 1.0.0 and our scipy 1.18.1 (LP angle calibration) give the same gate sequence and angles. We predict it is not byte-identical (about 60%), because the LP solver version differs.
2. **Our changes on top** (width cuts that trade Toffolis for qubits at about 26 Toffolis per qubit, see Method). Predicted final build: Q 70 to 88, cost 115,000 to 145,000.
3. **C-014.** Predicted refuted by this experiment (about 95%). The 63-qubit frontier is the product of about fifteen published rounds of gate-level rewrites, and we don't expect to reproduce them all in one experiment.
4. **Byte identity with the frontier.** Predicted not byte-identical (more than 99%). Our generator never reads the downloaded circuit.

**Refutation rule (C-014, fixed now).** C-014 holds for this experiment only if our generator's circuit gets PASS on the full official verify (default 64 shots per x, no `--max-x`) with cost ≤ 1.01 × 102,664.24 = 103,690.88. A cost below the frontier counts as holding. A FAIL, or any cost above 103,690.88, refutes it for this generator.

Exact predicted Q, mean Toffoli, rotation count, eps and cost for the build that goes to the full verify will be added below as a dated pre-registration before that verify starts, from local probes of our own circuit.

## Method

- **Generator.** `src/invsqrt/` (new): port of marsyas's model, fit, LP calibration, H/L-split build, nested windows, measurement-based unlookup and exact-domain post-pass, with an Apache-2.0 attribution notice. The configuration lives in `experiments/exp-008/config*.json`, not CLI flags. Output goes to `experiments/exp-008/out/` (gitignored).
- **Development checks (local, our circuit only).**
  - Exact integer model check over all 3,133,452 x (the phase model passes the tolerance).
  - kickmix simulation of the built circuit against the model on sampled x.
  - `src/kmx_value_sim.py` over all legal x: x restored, scratch clean, executed Toffoli mean.
  - Small official-verifier probes: `verify_submission_invsqrt.py <ours> --max-x N` (fewer x, same checks).
- **Width levers we will try**, each measured by the official verifier before it is kept:
  - in-place (Cuccaro-prefix) adders where the carry ancillas set the peak (the `qcap` option);
  - smaller lookup targets;
  - parking flags in freed slots;
  - freeing the H word early.
- **Full verify.** `python -I -B verify_submission_invsqrt.py invsqrt.kmb` (default 64 shots per x, default salt, no seed), on a private CPU Kaggle kernel with 4 forked workers. Full stdout, wall time, kernel slug and version are recorded.
- **Byte identity.** We compare the SHA-256 of our `.kmb` with the frontier's `07314803...` and with marsyas's stated `ff629b09...`.
- **Safety.** We never submit and never call a submit endpoint. Downloaded code is never executed. No downloaded circuit is copied into any output.

### Pre-registration 1 (2026-10-28, before the first full verify): the port, `config_port.json`

Local facts about our build (`build.py config_port.json`, 140 s locally):
- Canonical `.kmb` SHA-256 `ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917`. This equals the output hash marsyas's notebook states, so the port is byte-identical to marsyas's circuit (prediction 1's "about 60% not byte-identical" failed).
- Q 92, static Toffoli-like 1,315.
- Exact model over all 3,133,452 x: worst error/tolerance 0.9999059628540141, min margin 73,111,258 units of 2^-64 turns.
- Lane simulation over all x (`src/kmx_value_sim.py`): x restored, scratch clean, mean executed Toffoli 1,303.999. The only conditioned Toffolis are 22 static ones in the un-normalization, at p = 1/2 each, so the expectation is 1,304.0.
- Official verifier probe, `--max-x 20000` (1,280,000 shots, 30 s locally): PASS, toffoli_count 1,304.003, rotation_eps 2.8298390184213153e-13, cost 148,978.24.

Predicted full official verify (default arguments, Kaggle):
- PASS, Q 92;
- toffoli_count 1,304.000 ± 0.001;
- t_count 1;
- rotation_count 44;
- rotation_eps 2.8298390184213153e-13, exact (the phase is deterministic, so the verifier's min margin is the model's);
- worst_error_over_tolerance 0.9999059628540141;
- toffoli_equivalent 1,619.326 ± 0.001;
- cost 148,977.95 ± 0.1;
- ratio to the reference 13.940.

Against C-014's rule (≤ 103,690.88) this build is a refutation by construction. It is the baseline for our own changes.

## Results

All numbers come from `results.json`, built by `make_results.py kaggle_output 46af961` from the downloaded kernel output in `kaggle_output/exp008/`.

**Run.**
- Kernel `rainm4/exp-008-invsqrt-port-verify` v1. Private CPU script kernel, metadata in `kernel/port/kernel-metadata.json`, status `KernelWorkerStatus.COMPLETE`.
- The kernel embeds `src/invsqrt` as committed in 46af961: every downloaded `kaggle_output/src/invsqrt/*.py` has the same SHA-256 as `git show 46af961:src/invsqrt/<file>`. `kaggle_output/exp008/config.json` equals `config_port.json`.
- Kaggle built the circuit from scratch: the work dir started empty, the tables were fitted and the LP calibration ran in the kernel. Build rc 0 in 113.3 s, on numpy 2.1.3 and scipy 1.16.3.
- It then ran the unmodified verifier. SHA-256 `ddef520d...` is the same as the local `data/verifiers/invsqrt/verify_submission_invsqrt.py`.
- Command: `/usr/bin/python3 -I -B invsqrt/verify_submission_invsqrt.py /kaggle/working/exp008/invsqrt.kmb`, cwd `/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/verifiers`. Default salt, no seed, 64 shots per x, 4 forked workers.

**Full verifier output** (`kaggle_output/exp008/verify_full.json`, verifier stdout; stderr is empty):

```json
{
  "status": "PASS",
  "score": 148977.90224394592,
  "toffoli_equivalent": 1619.3250243907166,
  "toffoli_count": 1303.999457656843,
  "max_toffoli_count": 1315,
  "t_count": 1.0,
  "rotation_count": 44.0,
  "rotation_eps": 2.8298390184213153e-13,
  "num_qubits": 92,
  "reaction_depth": 205,
  "num_ops": 39084,
  "verified_shots": 200540928,
  "worst_error_over_tolerance": 0.9999059628540141,
  "worst_x": 2,
  "circuit_sha256": "ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917"
}
```

**Runtime and memory.**
- Verifier subprocess: 774.9 s wall on Kaggle. Peak summed tree RSS 0.70 GB, peak system used 0.97 GB.
- Whole kernel: about 902 s, made up of the 113.3 s build, the verify, and the HTML render.
- For comparison, exp-001's sample invsqrt took 1,503 s on the same kernel type.

| Metric | exp-001 baseline (sample) | public frontier (63Q) | this (our port) | change vs baseline |
|---|---|---|---|---|
| status | PASS | not run by us | PASS | |
| Q | 260 | 63 | 92 | -168 |
| toffoli_count (mean per shot) | | 1,334.496 (our lane sim, not the verifier) | 1,303.99946 | |
| toffoli_equivalent C | 7,987.59 | 1,629.59 (implied by the stated cost) | 1,619.32502 | |
| rotations | | 41 (+1 T) | 44 (+1 T) | |
| cost | 2,076,774.23 | 102,664.24 (busyaprime dataset README, not re-verified here) | 148,977.90 | improvement factor 13.940 |
| score factor on invsqrt alone | 1 | | 13.940^(1/3) = 2.4067 | |

- C-014 rule: the threshold is 1.01 x 102,664.24 = 103,690.88. Our cost is 148,977.90, which is 1.4511 x the frontier. **C-014 does not hold for this generator.**
- Byte identity:
  - Our canonical `.kmb` has SHA-256 `ff629b09...`. It is the same for the Kaggle build, the local build `out/port.kmb`, and the verifier's `circuit_sha256`. It equals the hash marsyas's notebook states for its output. We never downloaded marsyas's circuit file, so the comparison is against the stated hash only.
  - It is **not** byte-identical to the frontier `07314803...` (busyaprime v4).
  - It is also not byte-identical to mrmeows' `0766a111...`.
- Cross-platform:
  - The Kaggle build (numpy 2.1.3, scipy 1.16.3) and the local build (numpy 2.5.4, scipy 1.18.1) give the same circuit bytes and the same calibration cache bytes (SHA-256 `7ad3da69...` for both `hang_*.pkl`).
  - The table `.npy` is identical (`41f9d90f...`).
  - The two `ref.npz` files differ in bytes; their contents were not compared.
  - The generator reports are identical apart from timing.

**Pre-registration 1 vs measured.**

| Predicted (before the push) | Measured | Held? |
|---|---|---|
| PASS, Q 92 | PASS, Q 92 | yes |
| toffoli_count 1,304.000 ± 0.001 | 1,303.99946 | yes |
| t_count 1, rotation_count 44 | 1, 44 | yes |
| rotation_eps 2.8298390184213153e-13 exactly | 2.8298390184213153e-13 | yes |
| worst_error_over_tolerance 0.9999059628540141 | 0.9999059628540141 (worst_x 2) | yes |
| toffoli_equivalent 1,619.326 ± 0.001 | 1,619.32502 | yes (0.00098 below centre, inside the band) |
| cost 148,977.95 ± 0.1 | 148,977.90 | yes |
| ratio to reference 13.940 | 13.940 | yes |

**Original predictions (commit 7272591, before any generator code).**
1. Port passes at Q 92, mean Toffoli 1,304 ± 5, 44 rotations, cost 148,978 ± 1%. Held. The guess "about 60% not byte-identical to `ff629b09`" was wrong: it is byte-identical, on two different scipy versions.
2. Our width changes on top give Q 70 to 88, cost 115,000 to 145,000. **Not reached and not tested by the official verifier.**
   - The one lever tried was in-place adder prefixes under a qubit cap (`qcap`). It was swept locally with `sweep.py`, exact pass off. The output is `out/sweep_qcap.jsonl`, the generator's self-reported cost from sampled kickmix simulation, which is not a verifier number.
   - At qcap 88, Q was 89 and the cost rose to 155,065. At qcap 84, 80, 76 and 72, Q stayed 92 because the peak moved to another `B add` stage, and the cost rose to 149,806 to 166,175.
   - No lever beat the port, so nothing went to a verify.
3. C-014 refuted (about 95%). Held.
4. Not byte-identical to the frontier (over 99%). Held.

**Licence and provenance** (from `provenance.json`; downloads in `external/`, gitignored).
- Ported source, only one: marsyas (Houssem Alayet), notebook `marsyas/vqcc-invsqrt-13-94x-full-source`. Our copy's ipynb SHA-256 is `4da93524...`, and its last run was 2026-10-24 15:12:04 UTC. The Kaggle CLI does not report its version number.
  - Licence: Apache-2.0. The only statement is one sentence in the notebook text, "License: Apache 2.0." There is no LICENSE file.
  - The code was re-typed from the text dump `out/nb-marsyas.txt` and never executed.
- Our notice: the `src/invsqrt/__init__.py` docstring names the source, author, URL, read date and ipynb hash. It says the original copyright stays with its author and is used under Apache-2.0, with the licence URL, and it lists the people marsyas credits for ideas.
  - Each module docstring says "Ported from marsyas's Apache-2.0 notebook (...)". `generate.py` says "The pipeline structure follows marsyas's Apache-2.0 run.py/hsplit.py main".
  - Changes from the original are marked "change:".
- **Flag, licence compliance gap:** `src/invsqrt` carries a notice and the licence URL but no copy of the Apache-2.0 licence text, and the repository has no LICENSE or NOTICE file. Apache-2.0 §4(a) requires giving recipients a copy of the licence on redistribution. This must be added before any public release or prize code delivery. Nothing has been redistributed yet: the kernel is private.
- **Flag, upstream unknown:** marsyas credits ideas to Sumit Chongder, kozykappa, anazemcev, Dmitrii Gluzdov, Artem, auqib92, mizeroluckygall, lightningv08 and rudrabhaskar. Whether marsyas's notebook contains code copied from those authors' notebooks, and under what licences, is `unknown`. We did not download or check those notebooks.
- Sources without a licence statement: the busyaprime notebook `lb-22-33981...` and the zongaobian notebook. Both were read for design and lineage only. **Nothing from either was ported.** No source without a licence was ported.
- Downloaded circuits (frontier `07314803...` and mrmeows `0766a111...`, both Apache-2.0 datasets) were only loaded through kickmix for measurement. Our generator never reads them, and no downloaded circuit is in any output.

**Safety checks.**
- Pickles: `out/work/hang_28_19_8_1_sd_tc_a5_b_r63_L21_S20_d1.pkl` was written by our `src/invsqrt/generate.py` (`pickle.dump` of the LP calibration result) during the local build:
  - `port_build.log` shows the calibration computed fresh (63 s, from 22.4 s to 85.5 s into the build), not loaded.
  - The file mtime, 18:58:03, matches the build start (18:56:37, from `ref.npz` at 18:56:40) plus 85.5 s.
  - No `.pkl` exists anywhere under `external/`.
  - The Kaggle kernel's independent build wrote a byte-identical pickle (`7ad3da69...`).
  - That downloaded copy in `kaggle_output/exp008/work/` was deleted unloaded. Note that `generate.py` loads the cache whenever the file exists, so its work dir must never point at a downloaded directory.
- All Python ran with `-I -B`. Nothing was submitted, and no submit endpoint was called.

## Conclusion

- **C-014 is refuted for this generator.**
  - Our own from-source generator (`src/invsqrt`, an attributed Apache-2.0 port of marsyas) passes the full official invsqrt verify: 200,540,928 shots, Q 92, cost 148,977.90.
  - That is 13.940x the exp-001 sample, a 2.407x score factor on its own.
  - It is 45.1% above the 63-qubit frontier's 102,664.24, far outside the 1% band.
- Pre-registration 1 held on every figure, and the build is bit-reproducible across platforms and scipy versions.
- The planned width work (prediction 2) produced nothing that beat the port. The only lever tried, qcap adder prefixes, cost more Toffolis than it saved and mostly did not move the peak.
- The width gap is 29 qubits (92 vs 63). Q enters the cost linearly, so even at our Toffoli-equivalent count, 63 qubits would give about 102,000. Width alone is the lever, and per the design study the frontier has every stage packed to the cap rather than one bottleneck.
- Next step, for the research lead: a new experiment on per-stage width reduction of the port. Start from the live-qubit profile of `out/port.kmx` (`src/kmx_value_sim.py`) and take each lever to `--max-x 20000` and then a full verify.
- Before any public release of this code, add the Apache-2.0 licence text and a NOTICE to `src/invsqrt`.

## Deviations

- **2026-10-28, interruption.** The previous experimenter run hit an API rate limit after it had:
  - committed pre-registration 1 (46af961, 19:06:19 -0400);
  - generated `kernel/port/` (files at 19:06:27);
  - pushed kernel v1 (`push_v1.log` at 19:06:30);
  - written `make_results.py` (19:08:49).

  So the prediction predates the kernel push by 11 s, and the pushed code is the committed `src/invsqrt`, checked file by file through SHA-256. `kernel/port/` and `make_results.py` were not committed before the push; they are committed now.

  This session found the kernel `COMPLETE` with verifier rc 0 and downloaded its output. **No re-push** was needed, and none was made.
- **Prediction 2 and the Method's width levers were not carried out** beyond the local qcap sweep. Smaller lookup targets, parking flags and freeing the H word early were never tried. None went to the official verifier. This experiment closes on the port result alone, and the width work is left to a new pre-registered experiment.
- `make_results.py` was edited after the output was seen, to add `kernel_version`, plus `runtime_note` with the in-kernel build time parsed from `kernel.log`. No metric field changed.
- From `kaggle_output/` only the small files are committed: verifier JSON and meta, logs, build stdout, report, config and runner. The duplicated `src/` copy, `work/` (50 MB `ref.npz` and the table) and `invsqrt.kmb` are left uncommitted, and the downloaded pickle was deleted, as described above.
- The frontier cost 102,664.24 is busyaprime's stated official figure. We did not run the verifier on the frontier file in this experiment. The verdict does not depend on it unless that figure were off by more than 45%.

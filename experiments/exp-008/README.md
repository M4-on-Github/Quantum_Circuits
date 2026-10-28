---
id: exp-008
title: Our own invsqrt generator against the public 63-qubit frontier (C-014)
task: invsqrt
tests: [C-014]
direction: D-002
status: running
date: 2026-10-28
commit: pending
result: pending
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

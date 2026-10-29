---
id: exp-010
title: Width ledger of the src/invsqrt port and the public 63-qubit invsqrt circuit (C-015 diagnostic)
task: invsqrt
tests: [C-015]
direction: D-002
status: running
date: 2026-10-28
commit: pending
result: pending
---

## Hypothesis

C-015 (knowledge/claims.md): shortening register lifetimes in the `src/invsqrt` port, so that T, C2, the window
counters and the adder carries are not all live at the step-B peak, cuts Q from 92 to at most 72 while raising C by at
most 2%.

Baseline: exp-008 (accepted). The port (code 46af961, `experiments/exp-008/config_port.json`, SHA-256 `ff629b09...`)
passes the full official verify at Q 92, C 1,619.325, cost 148,977.90. The public frontier file (busyaprime `07314803...`,
derived from mrmeows `0766a111...`) has Q 63 and an implied C of about 1,629.6 (exp-008 critic).

This experiment is diagnostic and local. It answers the exp-008 critic's Analysis questions:
1. a per-register width ledger of the port at every stage;
2. the same ledger for the frontier, measured from its `.kmx` only;
3. which of the critic's four explanations, (1) register lifetimes, (2) narrower words, (3) adder carries,
   (4) gate-level rewrites, accounts for the 29-qubit gap, and how many qubits each could save in the port.

No full official verify is planned. Any lifetime change that turns out cheap may be built and probed with the official
verifier at `--max-x` only (pass/fail plus the generator's own C estimate). A full Kaggle verify is a later experiment.

## Prediction

Written 2026-10-28 before any ledger measurement. What I had already seen when writing it, so the predictions are scored
fairly:
- the exp-008 critic's stage table (92 / 89 / 84) and its coarse live-qubit profiles;
- the text of `src/invsqrt/build.py`;
- the Z_POW lines of the frontier `.kmx` (H block about lines 16,711-17,090 with 15 fine angles from 2^-17 half-turns
  plus 0.25; L block lines 27,125-27,380 with 26 fine angles from 2.9e-11 to 2^-10 half-turns);
- the first ~130 lines of the frontier L block as text, without counting its qubits;
- mrmeows' README (read as text): "main lookup (35 outputs of the 8-bit address)", "retain ten derivative seed bits",
  "the local live bound is below the global 63-qubit peak".

**P1. Port ledger (instrumented build, exact).**
- The step-B peak is 92 = x 22 + flags 4 + L 21 + T 18 + C2 7 + guard 1 + carries 19, at the big rows (`B add n=21`).
- Not only the two big rows: every step-B row add reaches 92, because each inner window is 2 bits narrower (2 fewer
  carries) while 2 more counter qubits are live. So the B stage is a plateau of 14 row adds at 92, forward and inverse.
- The L phase is 89 = 22 + 4 + 21 + 18 + 7 + guard 1 + counters 12 + ext 3 + temp 1.
- Idle (no gate touches them in the stage) at the B peak: C2 (7), guard (1), flags (4). At the L phase: x (22), T (18),
  C2 (7), guard (1), counters (12), 60 of 89 qubits.
- The instrumented build emits the same circuit: raw SHA `c97569f5...` with the exact pass off, `ff629b09...` with it on.

**P2. Frontier L word.** The phased L word, counted as the distinct data qubits (not flags, not borrowed x bits) XORed
into temp q40 across the L block, is 17 bits (range 16-19), about 3-4 narrower than our 20 phased L bits (L[1:21]).
Reason: 26 positions against our 29 under a positions = width + 10 - dropped rule.

**P3. Frontier persistent words.** At its L phase the frontier's 63 qubits split as x 22, shift flags 3-5, at most 7
table-only (function of the 8-bit address) qubits, and 29-34 arithmetic qubits (L word plus everything else).
Its arithmetic+table total is at least 15 below our 66 (L 21 + T 18 + C2 7 + guard 1 + counters 12 + ext 3 + temp 1 +
flags 4 minus nothing), i.e. the frontier stores less, not just for a shorter time.

**P4. Decision between the explanations (port side).**
- (1) Lifetimes alone, with the same words and no recomputation, cannot get the port below 89, because every word idle at
  the L phase (T, C2, guard, counters) is needed by B^-1 or A^-1 and can only be freed by recomputing it. The absolute
  lifetime floor is 73 (x + flags + L + T + C2 = 72, plus one phase temp) even if every transient vanished, so 72 is out
  of reach by lifetimes alone. Freeing the counters (wide rows instead of windows) costs about +130 Toffolis (+8% C);
  freeing C2 needs a second lookup (about +250 Toffolis, +15% C).
- (3) Carries: reducing the B plateau from 92 to 89 costs about 3 Toffolis per row add, about +80-115 Toffolis
  (+5-7% C) over 28 row adds, consistent with the exp-008 qcap 88 row. Not worth it on its own: at Q 92 the break-even
  is 17.6 Toffoli-equivalents per qubit, and that row pays about 38.
- (2) Narrower words account for most of the gap: the frontier keeps fewer and narrower words (35 lookup outputs
  against our 53 = L 21 + H 7 + T 18 + C2 7).
- (4) Gate-level rewrites: a few qubits at most (for example, borrowing the zero low bits of the normalized x as phase
  delay storage instead of 3 clean ext qubits).

**Refutation rule for C-015 (fixed now).** C-015 is refuted if the ledger shows that changing lifetimes alone, with the
port's words and widths unchanged, cannot reach Q <= 72 at <= +2% C. That holds if the floor of words that must be live
at some stage, plus the minimal transients there, exceeds 72, or if every schedule reaching 72 needs recomputation
costing more than 2% of C (about 32 Toffoli-equivalents). C-015 is supported only if I exhibit a lifetime-only schedule
reaching Q <= 72 at <= +2% C (I do not expect to). My prediction is that it is refuted, with the lifetime-only floor at
89 and the absolute floor at 73.

## Method

Port side (`experiments/exp-010/port_ledger.py`):
- Wraps the kickmix builder used by `src/invsqrt/build.build_hsplit` in a recording proxy. The proxy forwards every
  call unchanged, names each allocation by its call site (x, flags, L, H, T, C2, pad, const, ext, guard, carry, counter,
  phase temp, thermometer, one-hot, unnorm ancillas), and logs per stage label the live qubits per register, the peak,
  and which registers any gate touched. kickmix-internal ancillas (the lookup's) are the difference between
  `num_allocated_qubits` and the named total.
- Uses the cached tables and calibration from `experiments/exp-008/out/work` (our own build's cache, not a download).
- Builds with the exact pass off and on and compares SHA-256 with `c97569f5...` and `ff629b09...`.

Frontier side (`experiments/exp-010/kmx_ledger.py`, our code, reading the `.kmx` as text):
- Input: `experiments/exp-008/out/public/invsqrt.kmx`, written by kickmix's own loader from busyaprime `invsqrt.kmb`
  (`07314803...`). No downloaded code is run.
- A lane value simulation (the `src/kmx_value_sim.py` semantics) over all x in [1, 3,133,452]. At checkpoints (each
  Z_POW, each local maximum of the live count, and stage boundaries) every live qubit is classified by what it is a
  function of: x register, constant, shift t only (flags), the 8-bit address a = (p, top 7 bits of x_n) only (table),
  (a, t) only, or general arithmetic.
- The L word: the distinct qubits feeding q40 through CX/CCX/CSWAP data operands in lines 27,090-27,390, split into
  controls (classified as flags) and data.
- The same classifier is run on our `port.kmx` as a cross-check against the instrumented ledger.

Decision (P4) from the two ledgers plus Toffoli counts per stage, with arithmetic shown in the Results.

Run with `.venv/Scripts/python.exe -I -B`. No verifier run is needed for P1-P4.

**Pre-registration review (2026-10-29, before any measurement).** The text above was written on 2026-10-28 by an
attempt that was cut off by an API rate limit before committing. At review `experiments/exp-010/out/` was empty and no
exp-010 script existed, so no ledger number had been seen. The predictions P1-P4 and the refutation rule are kept
unchanged. Two operational clarifications, fixed now:
- P2 is scored by one rule applied to both circuits: the set of distinct qubits that are CX/CCX/CSWAP sources feeding the
  phase temp during the L block, minus flag qubits and x qubits. That raw set is reported for both, then split into
  persistent word qubits (allocated before the L block and live after it) and phase-only qubits (allocated for the L
  phase and released after it, our 3 `ext`). P2's "17 (16-19) against our 20" compares the persistent-word parts.
- "Lifetime-only" in the refutation rule means: same words, same widths, same tables and calibration, only the order of
  computation, the moment each register is freed, and recomputation of a word from data already in the circuit. Any
  recomputation is charged at its measured Toffoli count against the 2% budget (2% of C 1,619.325 = 32.4 Toffoli-equivalents).

## Results

## Conclusion

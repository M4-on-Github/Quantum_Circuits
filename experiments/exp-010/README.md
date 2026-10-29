---
id: exp-010
title: Width ledger of the src/invsqrt port and the public 63-qubit invsqrt circuit (C-015 diagnostic)
task: invsqrt
tests: [C-015]
direction: D-002
status: done
date: 2026-10-28
commit: 3884639
result: "C-015 refuted: lifetime-only reordering saves 0 qubits at the port's 92-qubit B plateau (28/28 row adds at 92), the floor of its words is 73, the cheapest recomputation is +254 Toffoli (+15.7% C); the frontier phases a 20-bit L word like ours and gets its 26 fewer L-phase qubits from erasing table words (8), reusing the x address qubits (8) and fewer non-L words (10)"
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

All numbers are from `results.json` and the committed ledger outputs in `ledger/` (copies of the gitignored `out/`
files). No official verifier was run. The port's Q, C and cost are the exp-008 verifier values (Q 92, C 1,619.325).
Break-even at Q 92: C/Q = 17.60 Toffoli-equivalents per qubit.

Commands (cwd repo root unless noted, all `.venv/Scripts/python.exe -I -B`):
- `experiments/exp-010/port_ledger.py experiments/exp-008/config_port.json experiments/exp-010/out/work experiments/exp-010/out`
  (`out/work` is a byte-identical copy of our own exp-008 cache; 35.9 s).
- `experiments/exp-010/to_kmx.py <kmb> <kmx>` for the frontier `.kmb` (`07314803...`, Q 63, 1,402 Toffoli-like) and the
  ledger build. The outputs equal exp-008's `.kmx` files (SHA-256 `17019b15...` and `15f037f9...`).
- From `experiments/exp-010`: `kmx_ledger.py out/port.kmx out/port_kmx_ledger.json --every=250` and
  `kmx_ledger.py out/public/frontier.kmx out/frontier_ledger.json --every=250` (946 s and 737 s wall, run concurrently).
- `experiments/exp-010/table_injectivity.py experiments/exp-008/config_port.json experiments/exp-010/out/work`,
  `src/kmx_tag_count.py experiments/exp-010/out/port.kmx ...`, then `experiments/exp-010/make_results.py 3884639`.

### 1. Port ledger (P1)

The instrumented build emits the same circuit: raw SHA-256 `c97569f5...`, final `ff629b09...`, generator peak
`(92, 'B add n=21')`. Registers by stage (the instrumented build; the lookup row is the `.kmx` ledger, because
kickmix-internal lookup ancillas are invisible at the call boundary):

| Stage | Peak | Live at the peak | Idle in the stage, at the peak | Toffoli (raw build) |
|---|---|---|---|---|
| thermometer | 48 | x 22, f1 1, flags 4, thermo 21 | none | 20 |
| normalize | 27 | x 22, f1 1, flags 4 | | 79 |
| lookup (`.kmx`) | 87 | x 22 (21 xn + p), flags 4, outputs 53 (L 21, H 7, T 18, C2 7), kickmix internal 8 | | 254 |
| H phase | 84 | x 22, flags 4, L 21, H 7, T 18, C2 7, const 1, ext 3, temp 1 | x, L, T, C2 (68) | 64 |
| A | 83 (7 row adds) | x 22, flags 4, L 21, T 18, C2 7, guard 1, carries 10 | L, flags (25) | 108 |
| **B** | **92 (all 14 row adds)** | x 22, flags 4, L 21, T 18, C2 7, guard 1, carries 19 (big rows); window rows trade 2 carries for 2 counters per level | C2, guard, flags (12) | 214 |
| L phase | 89 | x 22, flags 4, L 21, T 18, C2 7, guard 1, counters 12, ext 3, temp 1 | x, T, C2, guard, counters (60) | 134 |
| B^-1 | 92 (all 14 row adds) | mirror of B | C2, guard, flags (12) | 214 |
| A^-1 | 83 | mirror of A | L, flags (25) | 108 |
| unlookup | 72 | x 22, flags 4, L 21, T 18, C2 7 (before measurement) | | 28 |
| un-normalize | 41 | x 22, f1 1, flags 4, 14 ANDs | | 101 (22 conditioned) |

- 28 of 28 step-B row adds (forward and inverse) peak at exactly 92. The window rows confirm the trade: at window level k
  the add has 19 - 2k carries and 2k counter qubits.
- Bit level (`.kmx` ledger): across steps A and B (the `mid` segment, max 92) the only qubits never touched are
  x[14..21], the 8 address qubits. They sit idle from the end of the lookup until the unlookup.
- Executed Toffolis by width: 82.8% at >= 72 live qubits, 53.3% at >= 84, 15.0% at >= 89, 4.3% at 92. These are the
  exp-008 critic's figures, with a gate's width taken as max(live before, live after).

### 2. Frontier ledger (P2, P3)

Classes: `xn` = a bit of the normalized input, `flag` = a function of the shift t only, `table` = a function of the
8-bit address only, `arith_p` = a function of (p, xn), `arith` = needs t as well. "x-reg" means the qubit is one of
the 22 x-register qubits.

| Frontier phase (line ranges read off its timeline) | Lines | Max live | Static Toffoli | Composition at the widest timeline point |
|---|---|---|---|---|
| normalize | 1-250 | 48 | 71 | |
| main lookup | 251-16,710 | 63 | 179 | x-reg 22 (16 xn, 4 xn+flag, 1 flag, 1 table), table 40, flag 1 |
| H phase | 16,711-17,090 | 63 | 60 | x-reg 22 (17 xn, 3 xn XOR a (t, address) value, 2 flag), table 38, table_t 1, flag 2 |
| table/address step | 17,091-22,000 | 63 | 47 | x-reg 22, table 37, flag 4; by line 20,501, 5 of x[14..20] are 0 |
| arithmetic | 22,001-27,124 | 63 | 364 | x-reg 22 (**11 xn**, 3 xn+flag, **8 arith_p**), arith_p 39, flag 2, **table 0** |
| L phase | 27,125-27,380 | 63 | 90 | x-reg 22 (11 xn, 3 dump, 6 arith_p, 2 flag), arith_p 34, flag 2, phase scratch 5 |
| arithmetic uncompute | 27,381-31,750 | 63 | 288 | x-reg 22 (8 arith_p), arith_p 36, flag 2 |
| table recompute and uncompute | 31,751-36,250 | 63 | 184 | table 23 + 7 in x-reg, arith_p 16 + 1, flag 2 |
| measured-unlookup phase fix | 36,251-43,250 | 63 | 12 | table 13, 7 address copies outside x, arith_p 15 + 6 |
| restore and un-normalize | 43,251-45,745 | 52 | 107 | |

Totals: x restored on all lanes, 1,402 static and 1,334.504 mean executed Toffolis. 28.1% of executed Toffolis run at
63 live qubits and 61.0% at >= 59 (the exp-008 critic had 28.0% and 60.8% from a 193,606-lane sample).

L-phase window (temp q40, lines 27,110-27,380, 26 Z_POW on q40). Qubits feeding the temp:
- 20 L-word data qubits (class `arith_p`): **15 outside x, 5 in x-register qubits q15-q18, q20**;
- 4 flags (q14, q21 in x, q23, q56 outside x);
- 3 xn bits (q0, q2, q3), used as CSWAP dump space and restored;
- 4 scratch qubits that are zero at the window start and at its end (phase-only), plus the temp itself.

Persistent across the L window (live at its start and after its end), against the port:

| Group | Port | Frontier |
|---|---|---|
| x-register qubits | 22 (21 xn + p) | 22 (14 xn, 5 L-word bits, 1 other arithmetic, 2 flags) |
| flags outside x | 4 | 2 |
| L word outside x | 21 (20 phased + L[0]) | 15 (20 phased in all) |
| other arithmetic words outside x | 30 (T 18 + counters 12) | 19 (20 with the one in x) |
| table words | 8 (C2 7 + guard 1) | 0 |
| **persistent total** | **85** | **58** |
| phase-only (ext / scratch + temp) | 4 | 5 |
| L-phase peak | 89 | 63 |

So the 26-qubit L-phase gap splits as: table words not held 8, address qubits of x reused 8 (2 flags, 5 L bits,
1 other), fewer non-L arithmetic qubits 10 (30 against 20), L width 1, phase-only -1.

Lookup words of the port: u (L init) and C1 (T init) each take 256 distinct values over the 256 addresses, so each
determines the address. H takes 128 values and C2 takes 75.

### 3. Decision between the critic's explanations, quantified for the port

| Explanation | Qubits it could save at the port's peak | Cost | Evidence |
|---|---|---|---|
| (1) lifetimes, reorder only | **0** | none | every register live at the 28 row adds at 92 is an operand (L, T, carries/counters, an x control) or a word a later stage needs that nothing in the circuit regenerates (C2, guard for A^-1, flags for the L phase and un-normalization, x[14..21] for the unlookup). The words idle at the L phase (T, C2, guard, counters) are inputs to B^-1 and A^-1 |
| (1') lifetimes with recomputation (frontier-style: erase C2 and guard after A, reload them before A^-1) | 8 at B and L; Q goes to 87, bound by the lookup | +254 Toffoli (one more 8-bit lookup at the measured 254), C +15.7%. Cost about 163.0k (+9.4%) at Q 87 | estimate from measured parts, not built |
| (2) narrower words | 0 from the L word (the frontier phases 20 bits, like the port); 1 if L[0] goes | | the frontier's non-L arithmetic is 20 qubits against the port's T 18 + counters 12. The counters (12) are not on the 92 plateau |
| (3) adder carries | up to 19 at B; then the L phase (89) binds | at least 1 Toffoli per carry per row add, so >= 28 Toffoli per qubit at the 28 row adds. Break-even is 17.6. exp-008's qcap 88 paid about 38 per qubit | ledger plus exp-008 (not re-measured) |
| (4) rewrites: reuse x's address qubits, flags in x's zero low bits | up to 8 (x[14..21], idle across A and B) plus up to 4 (flags) | not measured | the frontier does both (table above) |

Absolute floor with the port's words: x 22 + flags 4 + L 21 + T 18 + C2 7 + guard 1 = **73** qubits, live from step A
through A^-1 even if every adder carry, counter and phase ancilla were removed.

### Predictions against results

| Prediction | Result | Verdict |
|---|---|---|
| P1: B peak 92 = 22+4+21+18+7+1+19; all 14 row adds at 92, forward and inverse; L phase 89 = 22+4+21+18+7+1+12+3+1; idle at the B peak C2, guard, flags; idle at the L phase x, T, C2, guard, counters (60); same SHA | all as predicted (28/28 row adds at 92; idle 12 and 60; `c97569f5` / `ff629b09`) | held |
| P2: frontier phased L word 17 (16-19), by the rule "distinct data feeders of q40, minus flags and x qubits, persistent part" | 15 under that rule. 5 more L-word bits sit in x-register qubits, so 20 phased L bits in all, equal to the port's 20 | **failed** (15 is below the range; 20 is above it) |
| P3: at the L phase, x 22, flags 3-5, table <= 7, arithmetic 29-34; at least 15 fewer non-x qubits than the port | x-register 22, but only 14 hold xn; flags 4 (2 in x); table 0; arithmetic outside x 34 persistent, 39 at the 63 peak (40 / 45 counting the x-register ones); non-x 41 against the port's 67 (26 fewer) | partly held (flags, table and "stores less" held; arithmetic was 34 at the window start and 39 at the peak; the pre-registration did not foresee x-register reuse) |
| P4 (1): lifetimes alone can't go below 89; lifetime-only floor 89; absolute floor 73; freeing C2 needs a second lookup (+~250, +15%) | lifetimes alone can't move the 92 peak at all, so the floor is 92; absolute floor 73 (with the guard, not a phase temp, as the 73rd qubit); the second lookup is 254 measured, +15.7% | the 89 figure failed (the floor is 92); the rest held |
| P4 (2): narrower words explain most of the gap; frontier 35 lookup outputs against 53 | 35 table qubits at the end of its lookup, against the port's 53. The L word is not narrower, though. The gap is table words not held (8), x-register reuse (8) and fewer non-L words (10) | failed as stated |
| P4 (3): 92 to 89 costs about +80-115 Toffoli | >= 84 (3 per row add over 28 adds); exp-008's qcap 88 paid +114 | held |
| P4 (4): rewrites are worth a few qubits at most | x-register reuse is worth 8 qubits at the frontier's L phase | failed |
| Refutation rule: C-015 refuted if lifetime-only changes can't reach Q <= 72 at <= +2% C | lifetime-only savings at the peak are 0, the cheapest recomputation costs +15.7% C, and the floor of the port's words is 73 | **C-015 refuted** (as predicted) |

## Conclusion

**C-015 is refuted.** Lifetimes cannot get the port to Q <= 72 at <= +2% C:
- Reordering alone saves 0 qubits at the 92-qubit plateau. All 28 step-B row adds sit at 92, and every register live
  there is either an operand or a word that a later uncompute needs.
- The cheapest real lifetime change recomputes the table words (C2 and guard), as the frontier does. That costs one
  more lookup, about +254 Toffoli (+15.7% C), and only gets to Q 87.
- Even with every transient removed, the port's own words need 73 qubits from step A to A^-1.

**The frontier's width.** It does not come from a narrower L word (it phases 20 bits, like ours), nor from carries.
At its L phase it holds 27 fewer persistent qubits than the port, for three reasons:
- It holds no table words (8): it erases them during the arithmetic and recomputes them in the uncompute.
- It reuses the 8 address qubits of the x register (x[14..21]) for L-word bits and flags. It appears to erase the address
  against its table words first (inferred: those qubits go to 0 while only table words hold the address), and it keeps
  flag information in x's zero low bits.
- It holds fewer non-L arithmetic qubits: 20 against our T 18 + counters 12.

In the critic's terms this is a mix of (1) with recomputation, (2) for the non-L words, and (4) x-register reuse.

**Next step (for the lead).** The port's x[14..21] are idle across steps A and B, and u and C1 each determine the
address. A model-only count of the Toffolis needed to erase the address against u or C1 (and to restore it before the
unlookup) would price the 8-qubit x-register reuse. That is the one lever here not ruled out by its Toffoli cost.
Reaching 72 also needs the 12 window counters and the lookup peak (87) handled, so a narrower-design generator looks
more promising than patching the port. No lifetime change was cheap enough to build, so no `--max-x` probe was run.

## Deviations

- 2026-10-29: the pre-registration was written on 2026-10-28 by an attempt that a rate limit stopped before it
  committed. It was reviewed and committed (4fe572b) before any measurement, with two clarifications of how to score
  P2 and what "lifetime-only" means. Its prediction text is unchanged.
- The Method planned classification "at each Z_POW, each local maximum of the live count, and stage boundaries". It
  was implemented as:
  - the maximum of each of 5 segments cut at the two Z_POW groups;
  - the start, first Z_POW and end of each phase window;
  - a timeline every 250 lines.
  The frontier phase table's line ranges were chosen by reading that timeline.
- P2's pre-registered rule excludes x-register qubits, on the expectation that they are "borrowed x bits". In the
  frontier, 5 of them hold L-word data (class `arith_p`), so both counts are reported (15 and 20). Neither is in
  16-19.
- Our port's 3 `ext` qubits count as "persistent" in the `.kmx` window ledger, because the f2/f4 shift fills them
  before the temp's last reset. They are counted as phase-only in the tables above, using the instrumented
  register ledger.
- The first `kmx_ledger.py` runs measured a Toffoli's width before the gate. This was changed to max(before, after),
  the exp-008 convention. A first timeline run was stopped for being slow; the packed-lane classifier replaced it.
  All reported numbers come from the final runs.

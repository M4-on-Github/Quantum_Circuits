---
name: quantum-stack
description: How to build, simulate and verify kickmix circuits for this competition - environment, data, verifiers, file formats, runtimes.
user-invocable: false
---

# Quantum stack

> The experimenter maintains this skill. `SKILL.md` holds only verified facts that every run needs; `reference/` holds the details, read on demand:
> `reference/runtimes.md` (verifier runtimes and memory), `reference/kaggle-cli.md` (CLI behaviour, kernel machine, datasets, auth), `reference/packaging.md` (submission zip), `reference/housekeeping.md` (Windows, Bash tool, git and permission pitfalls).
> Prune a note when a later fact supersedes it.
> Anything marked (unverified) must be checked against the verifier source before you rely on it.

## Environment

- Python 3.13 in `.venv/` at the repo root. Dependencies are pinned in `requirements.txt` (added exp-002: kickmix 1.0.0, numpy 2.5.4, scipy 1.18.1, psutil 7.2.2, the versions of the working `.venv`). The venv's base interpreter is the user's miniconda Python 3.13.12 (`sys.version` from `.venv/Scripts/python.exe`, exp-002).
- Commit messages: a user-level hook (`~/.claude/hooks/block_claude_trailer.py`) blocks any `git commit` whose message has a Claude co-author trailer or "Generated with" line. Commit without attribution lines (exp-002).
- `pip install kickmix` installs the host's PyPI wheels (Windows x86_64 supported).
- Use the PyPI version, not `data/kickmix/kickmix.so`, which is Linux-only and being phased out.
- Docs: the kickmix section of Google's Qualtran docs (circuit file format, instruction set, Python API).
- kickmix 1.0.0 (verified exp-001, Windows and Kaggle Linux): `kickmix.__version__` reports `0.1` even though `pip show kickmix` / `importlib.metadata.version('kickmix')` says 1.0.0. Check the version with `importlib.metadata`, not `__version__`.
- Windows has only the `spawn` start method. The invsqrt and dqi verifiers parallelize only when `'fork'` is available (`_run_parallel`), so on Windows they run serially on one core. dfthcsos (`scoreinfra`) never uses multiprocessing.
- Set `PYTHONDONTWRITEBYTECODE=1` when running verifiers, so no `__pycache__` is written into `data/` (or the read-only Kaggle input).
- In the Bash tool, bare `python` resolves to `C:\Users\moemy\miniconda3\python.exe`, not the venv. Always call `.venv/Scripts/python.exe`. `python -` (script from stdin) hangs even with `< /dev/null` and has to be killed with `Stop-Process` (exp-004).
- Large heredocs (~150 lines of Python) passed through the Bash tool can fail with `unexpected EOF while looking for matching '`, even with a quoted `'EOF'` delimiter. Write long scripts with the Write tool (exp-004).
- `python -I` implies `-E`, so it ignores `PYTHONIOENCODING`. On Windows, printing a non-cp1252 character (emoji, Greek letters from notebook text) then raises `UnicodeEncodeError`. Call `sys.stdout.reconfigure(encoding="utf-8")` in the script instead (exp-008).
- `multiprocessing` with `get_context('spawn')` works under `python -I -B`: the children inherit the `-I -B` flags and the parent's `sys.path`. A script that inserts `REPO/src` at module top level must keep its work under `if __name__ == '__main__':` (`src/invsqrt/fit.py`, exp-008).

## Data

`kaggle competitions download -c google-verifiable-quantum-circuit-compilation -p data/`, then unzip into `data/`. It is 1.04 GB, gitignored, and needs the user's OK the first time.

| Path under `data/` | Use |
|---|---|
| `verifiers/invsqrt/verify_submission_invsqrt.py`, `nr_reference_circuit.py` | invsqrt verifier and reference (Newton–Raphson) circuit |
| `verifiers/dqi/verify_submission_dqi.py`, `dqi_reference_circuit.py` | dqi verifier and reference decoder |
| `verifiers/dfthcsos/verify.py`, `SCORING_README.md`, `scoreinfra/` | dfthcsos verifier, contract, cost model |
| `verifiers/dfthcsos/FeMoCo76o113e.fcidump` | FeMoCo Hamiltonian (128 MB) |
| `verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py` | Reference angle loader |
| `sample_submission/` | Reference submission (score ≈ 1.015). `dqi.kmb` is 886 MB |

The dfthcsos starter kit is a separate Kaggle dataset ("Verifiable Circuit Compilation Starter Kit").

## Circuits

- `.kmb` is binary and `.kmx` is text. Both are accepted for submission.
- kickmix instructions are reversible classical gates, phase gates, and measurement-based uncomputation (measure an ancilla holding a∧b, then fix the phase classically).
- The simulator runs one bit string per lane, 64–512 inputs per CPU instruction.
- Verifiers check that inputs are restored, ancillas end at |0⟩, and the phase is correct on every shot.
- dfthcsos ANGLE_k generator: `src/angleload` (`build_family(angle_words, brot, J)`, `write_family(circuits, dir, "kmb")`). From the sample `submission.npz` `angle_words` at brot 12, J 8, it rebuilds all 10 sample `angle_k_*.kmb` byte for byte in about 4.5 s locally (exp-002). `src/angleload/qrom.py` is a port of the official Apache-2.0 `data/verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py` (lineage notice in its docstring). The official script alone (`--brot 12 --batch-size 8 --format kmb`) also writes the same 10 files in about 4.5 s. The port's one functional difference is a row-wise constant-segment leaf test, which never fires on the sample table; on tables with runs of identical rows it emits fewer Toffolis than the reference (exp-002 critic probe). `Circuit.to_file(path, format="kmb")` is deterministic across builds, so an identical gate sequence gives identical bytes and thus the same `submission_sha256` and seed.
- `operation_statistics().num_toffoli_like` counts `init_and` as 1 Toffoli and `del_and` (measurement uncompute) as 0. A segment-tree QROM over A addresses with the top bit used as a free control is A − 2 = 3,974 per circuit for A = 3,976 (exp-002).
- kickmix 1.0.0 GF(2^12) Toffoli costs, from isolated builds (exp-003):

  | Operation | Toffoli |
  |---|---|
  | `ixor_gf2_mul` / `init_gf2_mul` | 63 |
  | qubit-controlled `ixor_gf2_mul` | 75 |
  | `init_gf2_inverse_with_scaffold` (Itoh–Tsujii = 5 multiplies, 48 scaffold qubits) | 315 |
  | `del_gf2_inverse_with_scaffold` | 0 |
  | `init_gf2_div_with_scaffold` (60 scaffold qubits) | 378 |
  | `gf2_phase_by_product`, constant `gf2_imul` / `gf2_idiv` | 0 |
  | 12-bit `init_and`, `flip_if_equal(x, 0)`, `cswap`, controlled `gf2_iadd` | 12 each |
- kickmix itself emits `INFO_TAG "@enter:/@exit:<name>"` marks for its subroutines (`gf_mul`, `c_gf_mul`, `gf_inverse_chain`, `gf_div`, `unary_iteration`, `flip_if_lt`, ...), on top of `builder.mark(...)`. The sample `dqi.kmb` carries them (exp-003).
- In `.kmx` each instruction is one line. In the dqi circuits each CCX/CSWAP line is one gate, and Toffoli-like = CCX + CSWAP (+ CCZ).
- .kmx operand order (exp-005): `CX c t` (control first), `CCX c1 c2 t`, `CSWAP c x y`, `HMR q b` (X-basis measure of q into bit b, q reset), `R q`. Phase ops carry a classical condition: `CZ q q if b`, `Z q if b`, `NEG if b`, `BIT_INVERT b if b`. Registers are declared as `APPEND_TO_REGISTER qN rK` lines followed by `REGISTER rK "name"`. Checked by evaluating kickmix's own `ixor_gf2_mul` .kmx with this convention: it gives a bilinear 12 x 12 map with no zero divisors.
- kickmix 1.0.0 qubit-controlled `ixor_gf2_mul` is the uncontrolled 63-Toffoli `gf_mul` core (identical Toffoli skeleton) plus a 12-Toffoli controlled `c_gf_iadd` (exp-005).
- `src/kmx_tag_count.py <circuit.kmx> <out.json>` streams a .kmx and attributes Toffolis to the tag stack (full path and per-instance histogram). It also tracks `PUSH_CONDITION` bit definitions (HMR-measured, or an OR of `BIT_STORE1` sources). Its total equals `num_toffoli_like` on the dqi sample (exp-003).
- The sample `dqi.kmb` is identical (`Circuit ==`, canonical .kmb SHA-256) to a kickmix 1.0.0 build of `data/verifiers/dqi/dqi_reference_circuit.py` with default arguments (exp-003). The build takes 9.1 s on Kaggle.
- The dqi verifier JSON's `shot_operation_counts` is summed over all shots. Divide by `verified_shots` for per-shot figures.
- In `operation_statistics()` an `init_and` shows up as one CCX, and its `del_and` as one HMR plus one CZ. So HMR count = CZ count = number of measurement-uncomputed ANDs (exp-006, public dfthcsos loaders).
- Checking an ANGLE_k loader as an XOR oracle in the simulator: `km.Simulator(batch_size=A*S, counting_operations=True)`, `sim.use_same_registers_as(c)`, `write_across_shots` the selection bits and the target words from `dfthcsos.scoreinfra.circuits.register_layout(circuits)`, `sim.do(c)`, then read phase (`read_phase_flipped_across_shots`), selection, workspace and words. `experiments/exp-006/xor_oracle_check.py` does this for 15 circuits × 1,220 addresses × 8 shots × 3 input modes in about 6.5 s locally.
- dfthcsos verifier rules for ANGLE_k (read in `scoreinfra/circuits.py` and probed in exp-007):
  - The reverse pass runs the *same* K circuits, uninverted, in reverse order, and one simulator counts both passes. So `angles_toffoli` = 2 × Σ static when no gate is conditioned (P5: 159,040).
  - No separate uncompute circuit is possible. Exactly `ceil(75/J)` files `angle_k_<k>` are required (2K files fail with "need K circuits, got 2K"), and differently named files such as `angle_k_0_dag.kmb` are never read.
  - Every use is checked separately: phase, selection, workspace at 0, and words. Between circuits the simulator is cleared (`clear_for_shot`) and the words are rewritten.
  - `HMR` and conditioned `CZ`/`Z`/`NEG`/`BIT_INVERT`/`PUSH_CONDITION` blocks are accepted.
  - A Toffoli-like gate under `PUSH_CONDITION b` is charged only on shots where b = 1. One fresh HMR bit gives half (P2: implied fractions 0.4985 and 0.5057 over 4,736 shots).
  - kickmix has no Z-basis measurement. Classical bits come only from `HMR` (uniform random) or constants.
- `recover_words_from_circuits(circuits, num_vectors=A, num_angles=n, seed=s)` (from `dfthcsos.scoreinfra.circuits`) runs the official ANGLE_k check on any small synthetic table. It takes about 0.03 s at A = 37 (`experiments/exp-007/probes.py`).
- kickmix 1.0.0 lookups (exp-007):
  - `init_lookup(table=, address=, target=)` needs `len(table) == 2**len(address)`, so pad with zeros. Over 12 address bits it costs 4,094 Toffoli at any target width.
  - `del_lookup` is a built-in measurement-based lookup uncompute (HMR target, parities by conditioned `BIT_INVERT`, one-hot built in the measured target qubits, phase lookup with conditioned `CZ`). Its CCX/CSWAP are unconditioned. Static cost: 119 at n = 12 address bits, W = 96 (6 extra qubits); 56 at n = 10; 25 at n = 8.
  - `del_lookup` raises `tried to take 1 clean qubits, but only 0 were available` when the target is narrow. At n = 12 it works only for W ≥ 64; at n = 10 for W ≥ 24; at n = 8 for W ≥ 8.
  - `unary_iteration(sel, range(3976))` costs 3,978 Toffoli when used for a full phase fix-up pass.
- invsqrt generator `src/invsqrt` (exp-008): an Apache-2.0 port of marsyas's "VQCC invsqrt 13.94x - full source", with an attribution notice.
  - Run it with `python -I -B experiments/exp-008/build.py experiments/exp-008/config_port.json <out.kmb>`.
  - It fits the tables (8 spawn workers), runs the LP angle calibration (both cached in `experiments/exp-008/out/work/`), builds the circuit and runs the exact pass. About 140 s locally the first time (exp-008); 198 s with an empty work dir passed as the third argument, calibration 130 s of it, machine load not recorded (exp-009). The third argument `<work_dir>` selects the cache dir; an empty one forces a full refit and recalibration.
  - The output is byte-identical (SHA-256 `ff629b09...`) to the hash marsyas's notebook states, so PyPI kickmix 1.0.0 + scipy 1.18.1 reproduce a Kaggle build.
  - A fresh build on a Kaggle CPU kernel (numpy 2.1.3, scipy 1.16.3, empty work dir) gives the same `ff629b09...` bytes and a byte-identical calibration cache `hang_*.pkl` in 113 s, so the build is reproducible across these numpy/scipy versions (exp-008, kernel `rainm4/exp-008-invsqrt-port-verify` v1).
  - `generate.py` loads `<work>/hang_*.pkl` with `pickle.load` whenever it exists. Never point its work dir at a downloaded directory (exp-008).
  - Q 92, static Toffoli 1,315, mean 1,304.0, 44 rotations.
- `src/kmx_value_sim.py <c.kmx> <out.json> --lanes=all|N` (exp-008): a value-only lane simulator for .kmx (one basis input per lane, random HMR outcomes, condition masks; phases ignored). It reports x restored, dirty scratch, static and mean executed Toffoli, and the live-qubit profile (qubits nonzero on some lane).
  - On the public 63Q invsqrt: mean 1,334.496 over 193,606 lanes in 4.5 s.
  - On our 92Q port over all 3,133,452 x: about 70 s, mean 1,303.999.
  - The REGISTER line's id (`r0`) is not a q/b operand. Map it from the raw tokens.
- kickmix 1.0.0 builder internals (exp-010 probe):
  - A `km.q` has `.id`, the qubit index.
  - `alloc_qubits` reuses freed indices (free q3, q4, then alloc 1, and you get q4).
  - `num_allocated_qubits` is the current live count.
  - Qubits that kickmix allocates inside its own calls (for example `init_lookup`) are not visible from outside the call.
- Width ledger of the `src/invsqrt` build (exp-010):
  - `experiments/exp-010/port_ledger.py` replaces `invsqrt.build.B`, in-process only, with a subclass whose builder is a forwarding proxy. It names every allocation by its call site.
  - The build stays byte-identical: raw `c97569f5...`, final `ff629b09...`. It takes 36 s with a copy of the exp-008 cache.
  - The port's `init_lookup` costs 254 Toffoli. It peaks at 87 qubits, 8 of them kickmix-internal.
- `experiments/exp-010/kmx_ledger.py <c.kmx> <out.json> [--every=N]` is a bit-packed value simulation over all 3,133,452 x, run as two independent HMR draws.
  - It classifies each live qubit as `const`, `random`, `x`/`xn` bit, `flag` (a function of t), `table` (a function of the 8-bit address), `arith_p` (a function of (p, xn)) or `arith`.
  - It reports per-segment maxima and the feeders of each Z_POW group's temp.
  - About 90 s without `--every`. With `--every=250`: 737 s on the 63Q frontier and 946 s on the 92Q port, two runs at once. Memory not measured.
  - It takes a Toffoli's width as max(live before, live after). That reproduces the exp-008 critic's profile (frontier 28.1% of executed Toffolis at 63, port 82.8% at >= 72).
- `km.Circuit.from_file(kmb).to_file(kmx)` (`experiments/exp-010/to_kmx.py`) is deterministic: the regenerated frontier and port `.kmx` have the same SHA-256 as exp-008's (exp-010).
- invsqrt verifier `--max-x N` runs the same checks on x = 1..N only (64 shots each). `--max-x 20000` (1.28M shots) takes 30 s locally, serially. Its `rotation_eps` comes from the min margin over x ≤ N only, so it equals the full-run eps only when the worst-margin x is ≤ N (true for the exp-008 port, which is calibrated against all x).
- `src/angleload/mbu.py`: `emit_qrom_xor(b, sel, rows, targets)` is the qrom.py segment tree on a caller's builder, with arbitrary target qubits and a freed ladder. With the word bits as targets it gives `==` the reference circuit for all 10 sample circuits. `emit_mbu_clear` measures out qubits holding `rows[a]` (HMR plus a unary-iteration phase fix). `build_mbu_section_family` is the exp-007 P5 legality probe (official verify PASS, width 124, 580.8 s local, 1.10 GB).

## Kaggle notebooks

Run experiments as private Kaggle script kernels pushed with `kaggle kernels push`.
- `kernel-metadata.json` defaults:
  - `kernel_type: script`
  - `is_private: true`
  - `enable_gpu: false`
  - `enable_tpu: false`
  - `enable_internet: true`
  - `competition_sources: ["google-verifiable-quantum-circuit-compilation"]`
- Use one self-contained script per experiment, and pin `pip install kickmix==1.0.0` at the top.
- Record the kernel slug, version and metadata in the README. Save the downloaded outputs (`kaggle kernels output`) under `experiments/exp-NNN/`.
- Experiment code and kernels never submit to the competition.
- Kaggle CLI behaviour, kernel machine specs, dataset versioning and auth: `reference/kaggle-cli.md`.

## Running

- Generate circuits from code into `experiments/exp-NNN/out/`, which is gitignored. Never hand-edit a circuit.
- Run any verify step longer than about 2 minutes in the background with a log file in the experiment dir. dqi and dfthcsos are the slow ones, and dqi is memory-heavy at full size.
- Record the verifier's own reported Q, T (Toffolis), T-gates, ε+ / failures, Λ, E_gap, and cost. Never recompute them by hand when the verifier reports them.
- Seeding (verified from verifier source): invsqrt and dqi seed with `int(SHA-256 of the circuit's canonical .kmb serialization, hex)`. With `--salt S` it becomes `int(sha256(f"{hash}{S}"))`, and `--seed N` overrides both. dfthcsos does the same with `submission_sha256` over circuits, factorization and tree (`scoreinfra.circuits.initial_seed`). Vary `--salt` to get fresh tests. With no salt or seed, re-runs are bit-identical (exp-001: invsqrt on both platforms).
- dqi with 0 failures: eps+ = -expm1(log2_delta·ln2/N) depends only on N. At 102,400 shots that gives eps+ = 8.6606e-4 and R = 1.19126 (exp-001), the floor.
- dqi T in the cost is `toffoli_count`, the mean Toffoli-like count per simulated shot (seed-dependent). `max_toffoli_count` is the static circuit count. Sample: mean 5,725,108.38 vs static 5,725,461 (exp-001).
- `python -I dfthcsos/verify.py <abs stage dir>` (cwd `verifiers/`) works: verify.py puts its own repository root on `sys.path`, so isolated mode needs no PYTHONPATH (exp-006, Windows and Kaggle).
- Cross-platform parity (exp-001): invsqrt output is bit-identical between Windows and Kaggle Linux. dfthcsos integer resources (T, Q) and pass/fail are identical, but float metrics differ in the last 1–2 ulp (score rel. diff 3e-16, error_1 4e-13) because numpy/scipy versions differ.
- Runtimes and memory for every verifier and circuit measured so far: `reference/runtimes.md`. Read it before choosing local vs Kaggle.
- Submission zip layout and the packager: `reference/packaging.md`.
- Windows, Bash tool, git and permission pitfalls: `reference/housekeeping.md`. Read it before writing long scripts or listing processes.

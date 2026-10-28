---
name: quantum-stack
description: How to build, simulate and verify kickmix circuits for this competition - environment, data, verifiers, file formats, runtimes.
user-invocable: false
---

# Quantum stack

> The experimenter maintains this file. It holds verified, reusable tooling facts only.
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
- `src/kmx_tag_count.py <circuit.kmx> <out.json>` streams a .kmx and attributes Toffolis to the tag stack (full path and per-instance histogram). It also tracks `PUSH_CONDITION` bit definitions (HMR-measured, or an OR of `BIT_STORE1` sources). Its total equals `num_toffoli_like` on the dqi sample (exp-003).
- The sample `dqi.kmb` is identical (`Circuit ==`, canonical .kmb SHA-256) to a kickmix 1.0.0 build of `data/verifiers/dqi/dqi_reference_circuit.py` with default arguments (exp-003). The build takes 9.1 s on Kaggle.
- The dqi verifier JSON's `shot_operation_counts` is summed over all shots. Divide by `verified_shots` for per-shot figures.
- In `operation_statistics()` an `init_and` shows up as one CCX, and its `del_and` as one HMR plus one CZ. So HMR count = CZ count = number of measurement-uncomputed ANDs (exp-006, public dfthcsos loaders).
- Checking an ANGLE_k loader as an XOR oracle in the simulator: `km.Simulator(batch_size=A*S, counting_operations=True)`, `sim.use_same_registers_as(c)`, `write_across_shots` the selection bits and the target words from `dfthcsos.scoreinfra.circuits.register_layout(circuits)`, `sim.do(c)`, then read phase (`read_phase_flipped_across_shots`), selection, workspace and words. `experiments/exp-006/xor_oracle_check.py` does this for 15 circuits × 1,220 addresses × 8 shots × 3 input modes in about 6.5 s locally.

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
- Verified working (exp-001, kernel `rainm4/exp-001-verify-sample-submission` v1, 2026-10-28): the defaults above with Kaggle CLI 2.2.5 and `kaggle kernels push -p <dir>`. `kaggle kernels status <slug>` reports `KernelWorkerStatus.RUNNING` / `COMPLETE`. `kaggle kernels output <slug> -p <dir>` downloads `/kaggle/working` contents plus `<slug>.log`. The server renames `code_file` to `<slug>.py` and adds `docker_image` and `machine_shape: "None"` (see `kaggle kernels pull <slug> -m`).
- The Kaggle CLI is the miniconda one on PATH (`kaggle`, at `/c/Users/moemy/miniconda3/Scripts/kaggle`). It is not in `.venv` (exp-003).
- Auth: the CLI authenticates with `KAGGLE_API_TOKEN`. It is set at Windows user scope, but the Bash tool's shell may not inherit it. Load it without printing: `export KAGGLE_API_TOKEN="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('KAGGLE_API_TOKEN','User')" | tr -d '\r\n')"`.
- Kaggle CPU kernel machine (exp-001): Python 3.13.15, 4 CPUs (`cpu.max` 400000/100000), cgroup `memory.max` 32212254720 B (30 GiB), `fork` available, numpy 2.1.3, scipy 1.16.3, psutil 5.9.5 preinstalled. `pip install kickmix==1.0.0` works with internet on.
- Competition data mounts at `/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/` (same layout as the zip: `verifiers/`, `sample_submission/`, ...), not `/kaggle/input/<slug>/`. Search for a marker file instead of hard-coding the path. The files there are byte-identical (SHA-256) to the local `data/` copy.
- Pass absolute paths when a runner starts a verifier with a different `cwd`. Relative paths then resolve against the child's cwd and fail.
- Kaggle datasets (CLI 2.2.5, exp-006): a specific version is addressed as `owner/slug/N` for `kaggle datasets files owner/slug/N` and `kaggle datasets download owner/slug/N -f <file>`. `owner/slug/versions/N` is rejected as invalid. `kaggle datasets status` returns not-found for other users' datasets. `datasets files` takes `--format`, not `-o`.
- Kernel `dataset_sources` version pins do not work: `"owner/slug/N"` is accepted by `kaggle kernels push`, but the server strips the version (see `kaggle kernels pull -m`) and mounts the latest version. Identify attached files by SHA-256 inside the kernel (exp-006).
- Attached datasets mount at `/kaggle/input/datasets/<owner>/<slug>/` (exp-006).

## Running

- Generate circuits from code into `experiments/exp-NNN/out/`, which is gitignored. Never hand-edit a circuit.
- Run any verify step longer than about 2 minutes in the background with a log file in the experiment dir. dqi and dfthcsos are the slow ones, and dqi is memory-heavy at full size.
- Record the verifier's own reported Q, T (Toffolis), T-gates, ε+ / failures, Λ, E_gap, and cost. Never recompute them by hand when the verifier reports them.
- Seeding (verified from verifier source): invsqrt and dqi seed with `int(SHA-256 of the circuit's canonical .kmb serialization, hex)`. With `--salt S` it becomes `int(sha256(f"{hash}{S}"))`, and `--seed N` overrides both. dfthcsos does the same with `submission_sha256` over circuits, factorization and tree (`scoreinfra.circuits.initial_seed`). Vary `--salt` to get fresh tests. With no salt or seed, re-runs are bit-identical (exp-001: invsqrt on both platforms).
- dqi with 0 failures: eps+ = -expm1(log2_delta·ln2/N) depends only on N. At 102,400 shots that gives eps+ = 8.6606e-4 and R = 1.19126 (exp-001), the floor.
- dqi T in the cost is `toffoli_count`, the mean Toffoli-like count per simulated shot (seed-dependent). `max_toffoli_count` is the static circuit count. Sample: mean 5,725,108.38 vs static 5,725,461 (exp-001).
- `python -I dfthcsos/verify.py <abs stage dir>` (cwd `verifiers/`) works: verify.py puts its own repository root on `sys.path`, so isolated mode needs no PYTHONPATH (exp-006, Windows and Kaggle).
- Cross-platform parity (exp-001): invsqrt output is bit-identical between Windows and Kaggle Linux. dfthcsos integer resources (T, Q) and pass/fail are identical, but float metrics differ in the last 1–2 ulp (score rel. diff 3e-16, error_1 4e-13) because numpy/scipy versions differ.

## Verifier runtimes and memory (sample submission, default args, exp-001, 2026-10-28)

| Verifier | Kaggle CPU kernel (4 workers via fork) | Local Windows 11, i9-14900HX, 32 logical CPUs, 31.7 GB (serial) |
|---|---|---|
| invsqrt (200,540,928 shots) | 1,503 s wall; 0.54 GB per process, 0.71 GB summed tree RSS | 9,056 s wall (2.5 h, ~94% of one core); 0.54 GB peak working set; no stdout until it finishes |
| dqi (102,400 shots) | 449 s wall; 9.5 GB peak per-process, 9.6 GB system used | not run |
| dqi with `--salt` (exp-003, 3 runs) | 366–371 s wall; 9.53 GB peak per-process, ≤ 9.95 GB system used | not run |
| dfthcsos | 137 s wall; 1.2 GB | 356 s wall; 1.1 GB |
| dfthcsos, public 15-circuit 430Q build (1,220 addresses, about 280 Toffoli per circuit; exp-006) | 29.5 and 33.5 s wall; 0.73 GB | 42.8 s wall; 0.86 GB (alone, AC power) |

- dqi accounting pipeline on Kaggle (exp-003):
  - Loading the sample `dqi.kmb` takes 3.8 s.
  - `to_file(format='kmx')` takes 14.3 s and writes 1.54 GB (86.1M lines).
  - The streaming `kmx_tag_count` takes 111 s.
  - Peak memory is 3.57 GB per process.
  - Generator build, sample load, `==`, plus the count: 4.47 GB peak.
- So run full invsqrt verifies on Kaggle. The dqi CLI's "~6 GB per worker" estimate did not hold: the whole forked tree stayed under 10 GB.
- The local figures come from three verifiers running concurrently.
- A local dfthcsos verify of the sample took 1,017 s wall with a 1.11 GB peak RSS (exp-002). For the first ~11 min it got only about 98 CPU-s, then about 1 CPU-s/s. It was mostly alone, but exp-004's dfthcsos verify overlapped its last ~69 s. The laptop was on battery (`BatteryStatus.Discharging` True); that this caused the slowdown is untested. Two concurrent runs of the same verifier in the exp-002 review took about 330 s each (1.04 GB). Expect 5.5–17 min locally.
- Waiting on a background job: `powershell.exe -NoProfile -Command "Wait-Process -Id <pid> -Timeout 590"` works. If it exceeds the Bash tool's 600 s limit, the call moves itself to the background (exp-002).
- The machine runs at about 92% commit charge with the user's normal apps open (Edge alone about 14 GB private). Check `Win32_OperatingSystem` free memory before starting dqi locally.

## Submission packaging

- `experiments/exp-004/package.py` builds a submission zip with Python `zipfile`, `ZIP_DEFLATED` level 6.
  - Layout: `invsqrt.kmb` and `dqi.kmb` at the root, then `dfthcsos/angle_k_0..n-1.kmb` and `dfthcsos/submission.npz`. No directory entries and no wrapping folder.
  - It then re-reads every member and checks its SHA-256 against the source.
  - This is the competition page layout, and the one public assembly notebooks use.
  - (unverified) That the LB accepts it. This is settled once a submission of it is scored.
- Deflate shrinks the sample a lot (exp-004): `dqi.kmb` goes from 886,118,180 B to 69,819,447 B, and the whole zip is 73,803,082 B. Building and checking takes about 45 s locally.
- Fixed member metadata makes the zip SHA-256 reproducible between runs on the same Python/zlib build (verified for 3.13.12 / zlib 1.3.1, exp-004): `ZipInfo` date_time (1980,1,1,0,0,0), `create_system=3`, mode 0o100644, sorted members.
- Verifier seeds hash member contents (canonical kmb bytes and npz arrays), not the zip bytes, so the packaging doesn't change which tests run.
- Windows: renaming a just-written zip can fail with `PermissionError` WinError 32 because something else briefly holds the file. Retry the rename (exp-004).
- dfthcsos `verify.py` accepts a folder extracted from the zip (`verify.py <extract>/dfthcsos`). Its output was bit-identical to exp-001 local: 512 s wall against 356 s in exp-001. Machine load is unknown: exp-002 and exp-003 were running at the same time.

## Process housekeeping

- Git: a user hook (`block_claude_trailer.py`) rejects commit messages that carry a Claude `Co-Authored-By` trailer, so commit without it (exp-003).
- Bash tool: one long command that wrote several files through `<<'EOF'` heredocs failed with ``unexpected EOF while looking for matching `''`` and wrote nothing. The cause was not determined. Writing the files with the Write tool worked (exp-003).

- To list processes from Git Bash, call PowerShell CIM. Escape every `$` as `\$` inside the double-quoted `-Command`:
  `powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -match '^(python|bash|powershell|kaggle)(\.exe)?$' } | Format-List ProcessId,ParentProcessId,CreationDate,CommandLine"`
- Each Claude Code background job shows up as a tree: `bash.exe` (Git\bin), then `bash.exe` (usr\bin), then the command. A `.venv\Scripts\python.exe` launcher shim spawns a second python (the real interpreter), so each python job appears twice. Subprocess verifiers repeat that pair. The CPU and memory sit only on the innermost python.
- Background jobs from every agent in a session share one `claude.exe` parent. To tell experiments apart, use the command line (script path, `--tag`), not the parent PID.
- `browser-use.exe --cli-mcp` pythons under `uv\cache` are Claude Code MCP plugin servers, not experiment processes.

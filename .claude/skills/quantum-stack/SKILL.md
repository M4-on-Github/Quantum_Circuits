---
name: quantum-stack
description: How to build, simulate and verify kickmix circuits for this competition - environment, data, verifiers, file formats, runtimes.
user-invocable: false
---

# Quantum stack

> The experimenter maintains this file. It holds verified, reusable tooling facts only.
> Anything marked (unverified) must be checked against the verifier source before you rely on it.

## Environment

- Python 3.13 in `.venv/` at the repo root. Dependencies are pinned in `requirements.txt`.
- `pip install kickmix` installs the host's PyPI wheels (Windows x86_64 supported).
- Use the PyPI version, not `data/kickmix/kickmix.so`, which is Linux-only and being phased out.
- Docs: the kickmix section of Google's Qualtran docs (circuit file format, instruction set, Python API).

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

## Running

- Generate circuits from code into `experiments/exp-NNN/out/`, which is gitignored. Never hand-edit a circuit.
- Run any verify step longer than about 2 minutes in the background with a log file in the experiment dir. dqi and dfthcsos are the slow ones, and dqi is memory-heavy at full size.
- Record the verifier's own reported Q, T (Toffolis), T-gates, ε+ / failures, Λ, E_gap, and cost. Never recompute them by hand when the verifier reports them.
- Local verifier salt (unverified): find how the verifier seeds its tests. Use the same mechanism to vary the salt when estimating dqi ε+ spread.

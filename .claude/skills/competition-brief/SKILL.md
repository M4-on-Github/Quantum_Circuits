---
name: competition-brief
description: Facts about the Google Quantum AI Verifiable Quantum Circuit Compilation Kaggle competition - tasks, cost formulas, score, limits, rules, deadlines.
user-invocable: false
---

# Competition brief

Kaggle slug: `google-verifiable-quantum-circuit-compilation`. Full scrape: `competition.md`.
Companion paper: Khattar et al., arXiv:2610.23832 (also `data/verifiable_circuit_compilation.pdf`).
The verifiers in `data/verifiers/` are the authoritative spec. When this brief and a verifier disagree, the verifier wins.

## Score

Score = (∏ over 3 tasks of cost_ref / cost)^(1/3), the geometric mean of improvement factors. Higher is better.
A 2x cost cut on one task multiplies the score by 2^(1/3) ≈ 1.26, whichever task it is. Effort goes where the cheapest factor is.

| Task | What the circuit does | Cost (lower is better) |
|---|---|---|
| invsqrt (Benchmark I) | \|x⟩\|0⟩ → e^{2πi/√x}\|x⟩\|0⟩ for x = 1..3,133,452 in the 22-qubit register `x`. Phase error ≤ 2^-24/√x turns; every x tested 64 times | Q × (Toffolis + T/4), with rotations priced in T |
| dqi (Benchmark II) | Reversible RS(4095, 4025) syndrome decoder over GF(2^12). Syndromes S0..S69, record M in E0..E4094; restore syndromes, apply phase (−1)^{Σ popcount(e_j ∧ M_j)}. 102,400 shots; failures allowed | R(ε+) × Q² × T, where R(ε) = ln2 / (−ln(1/2 + 2√ε)), R(0) = 1, and ε+ is an upper confidence bound on the failure rate |
| dfthcsos (Benchmark III) | Angle-loading (QROM) circuits `angle_k_0..n-1` + factorization and Givens tree in `submission.npz` for FeMoCo | λ_eff × T × Q over the whole block encoding, λ_eff = √(E_gap(2Λ − E_gap)) |

Q = qubits, T = Toffolis, both per shot.
- dfthcsos rejection rules: any circuit wider than 128 qubits, Hamiltonian error above 20 mHa, Λ ≤ 49.0, or E_gap ≤ 3.914898 Ha. Contract: `data/verifiers/dfthcsos/SCORING_README.md`.
- dqi: Q enters squared, so width cuts are worth twice as much as Toffoli cuts.
- Fiat–Shamir: tests are seeded by a hash of the submission plus a secret salt. Any change gives fresh tests. Local verification and the leaderboard use different salts, so dqi's ε+ can differ slightly between them.

## Submission

A zip containing `invsqrt.kmb|kmx`, `dqi.kmb|kmx`, and `dfthcsos/` (`angle_k_0..`, numbered with no gaps, plus `submission.npz` with U, W, H2_I, H1_I, Hsym_lower, tree_edges).
- Scoring takes about 45 min.
- 5 submissions per day; 2 final picks.
- The public LB uses about 50% of the test draws.
- Only the user submits. No agent runs `kaggle competitions submit`.

## Where things stand (2026-10-28)

- The sample submission scores about 1.015.
- Public notebooks reach about 22.6.
- The top of the LB is 26.14.
- Public notebooks and discussion threads are a moving baseline. Know what they do before claiming novelty.

## Rules that matter

- External data, models and tools are allowed if they're publicly and freely accessible (Reasonableness Standard). LLM and AI-agent use is explicitly expected.
- No private code sharing outside the team. Public sharing on Kaggle forums or notebooks is fine.
- Winners license their submission and generating code under Apache 2.0 and must deliver code that reproduces it. So every submitted circuit must be regenerable from committed code.
- Prizes:
  - Mid-competition milestone: best public LB on 2026-11-20, requires a public notebook.
  - Longest leader: through 2027-01-04.
  - Single-task: $10k per task for the best selected submission on that task.
- Deadlines: entry and team merger 2027-01-13. Final submission 2027-01-20, 23:59 UTC.
- Kaggle access: use the Kaggle CLI/API, not page scraping.

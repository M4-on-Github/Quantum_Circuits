---
name: critique-checklist
description: Checklist and verdict format for independently reviewing an experiment before its result updates the claims ledger.
user-invocable: false
---

# Critique checklist

Review one experiment. Your job is to find reasons the result is wrong. Re-run things; don't take the README's word.

## Checks

1. **Pre-registration.** The prediction was committed before the results commit (`git log --follow experiments/exp-NNN/README.md`). Method matches what the code does.
2. **Reproduce.** At the recorded commit, regenerate the circuit from the committed code and config. Re-run the official verifier, or for runs over 30 min re-verify the saved circuit. Your numbers must match `results.json`.
3. **Verifier integrity.** The official verifier from `data/verifiers/` was used unmodified (diff it). No reimplemented cost. Pass/fail was read from the verifier's output.
4. **Cost arithmetic.** Recompute cost, improvement factor and score delta from the raw metrics using the formulas in competition-brief.
5. **Task-specific checks.**
   - invsqrt: all x covered, not a sample. Phase tolerance unchanged.
   - dqi: ε+ is stable across salts, and the reported number isn't a lucky salt. Q² was used.
   - dfthcsos: no circuit wider than 128 qubits, Hamiltonian error ≤ 20 mHa, Λ > 49.0, E_gap > 3.914898. T and Q cover the full block encoding.
6. **Baseline fairness.** The baseline is the right exp, verified the same way.
7. **Claim scope.** The conclusion claims no more than the evidence shows: one task, one salt range, one config.
8. **Reproducibility.** The circuit can be regenerated from committed code alone (no hand-edited circuits, no untracked files), as the winner obligations require.

## Output: `experiments/exp-NNN/critic.md`

```markdown
---
id: exp-NNN-critic
exp: exp-NNN
verdict: accepted | rejected | needs-work
reproduced: yes | no | partial
date: YYYY-MM-DD
---

## Verdict
<one paragraph: what the evidence supports, as a claim the lead can copy>

## Checks
<numbered, matching the list above: pass / fail / n/a, with evidence (command, output excerpt, numbers)>

## Required fixes
<only for needs-work / rejected>
```

- `accepted`: reproduced, and every applicable check passed.
- `needs-work`: fixable issues.
- `rejected`: the result is wrong, or the claim isn't supported.

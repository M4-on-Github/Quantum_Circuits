---
name: critique-checklist
description: Review tiers, audit checklist, re-run triggers, synthesis questions, writing guidelines and verdict format for reviewing an experiment before its result updates the claims ledger.
user-invocable: false
---

# Critique checklist

Review one experiment. Audit it from what was committed, then explain it against everything else the logbook knows.

## Review tier

The lead names the tier in the dispatch. If it didn't, pick one and say which in `critic.md`.

- **light**: infrastructure, packaging, byte-identical reproductions, and results whose numbers can't change any claim's status. Audit checks 1, 2, 3 and 6 only. No synthesis, no re-runs. Aim for well under 400 words.
- **full**: everything that moves a claim to supported/refuted/contested or goes into a submission. All audit checks, synthesis.

## Direction review

When dispatched on a D-NNN instead of an experiment: no audit, no files. Answer in your report, under 300 words: the weakest assumption and what evidence would test it; public evidence (kg-, lit-) that points the other way; what a top-20 team would most likely do instead; one option the proposal didn't consider.

## Re-review

When `critic.md` already exists for this experiment, this is a re-review of a `needs-work` or `rejected` verdict:
- Read the previous `critic.md` and check only its Required fixes, plus anything the fixes changed.
- Don't re-audit what already passed.
- Append a dated `## Re-review YYYY-MM-DD` section with the new verdict and update the frontmatter `verdict`. Keep the earlier text.

## Audit (no re-runs)

1. **Pre-registration.** The prediction was committed before the results commit (`git log --follow experiments/exp-NNN/README.md`). Read the code: the method matches what it does.
2. **Verifier integrity.** The official verifier from `data/verifiers/` was used unmodified (diff it). No reimplemented cost. Pass/fail and metrics in `results.json` match `verifier.log`.
3. **Cost arithmetic.** Recompute cost, improvement factor and score delta from the raw metrics in `verifier.log`, using the formulas in competition-brief.
4. **Task-specific checks.**
   - invsqrt: all x covered, not a sample. Phase tolerance unchanged.
   - dqi: at least 3 salts, ε+ stable across them, and the reported number isn't the luckiest salt. Q² was used.
   - dfthcsos: no circuit wider than 128 qubits, Hamiltonian error ≤ 20 mHa, Λ > 49.0, E_gap > 3.914898. T and Q cover the full block encoding.
5. **Baseline fairness.** The baseline is the right exp, verified the same way.
6. **Claim scope.** The conclusion claims no more than the evidence shows: one task, one salt range, one config.
7. **Reproducibility.** The circuit can be regenerated from committed code alone (no hand-edited circuits, no untracked files), as the winner obligations require.

## Re-run triggers

Re-run only when one applies, and name it in `critic.md`:
- **Re-verify the saved circuit** (check its hash against `circuit_sha256` first) if `verifier.log` is missing or disagrees with `results.json`, the gain is larger than the method explains, or the result will go into a submission.
- **Regenerate from code** only if the saved circuit is missing, its hash doesn't match, or the code doesn't obviously produce it.
- Anything else costly (extra dqi salts, ablations, new Kaggle kernels): don't run it. List it under Required fixes for the experimenter.

## Synthesis (full tier)

- Does the result agree with the claim's sources (lit-, kg- notes) and with earlier experiments? Where does it conflict?
- Why did it come out this way? Point at the mechanism: which gates, qubits or terms moved the cost.
- What else could explain it? Rank the explanations by plausibility.
- What is the cheapest experiment that tells the leading explanations apart?
- Which other claims does this strengthen, weaken or suggest?

## Writing

The lead reads every `critic.md`, so write for a reader who has the README open.
- Don't restate the README's method or results. Refer to them.
- Lead with the finding, then the one piece of evidence that settles it. Quote the decisive line of a command's output, not the whole output.
- A check that passed gets one line. Spend words on what failed, what surprised you, and what the lead should do next.
- Numbers over adjectives. Cite IDs (exp-, lit-, kg-, C-) instead of re-explaining them.
- Mark inference as yours. Don't pad with caveats that apply to every experiment.
- Analysis is a ranked list of explanations, not an essay.

## Output: `experiments/exp-NNN/critic.md`

```markdown
---
id: exp-NNN-critic
exp: exp-NNN
tier: light | full
verdict: accepted | rejected | needs-work
verified: inspected | reverified | regenerated
date: YYYY-MM-DD
---

## Verdict
<one paragraph: what the evidence supports, as a claim the lead can copy>

## Audit
<numbered, matching the list above: pass / fail / n/a, with evidence. Any re-run: trigger, command, result>

## Analysis            (full tier)
<ranked explanations, citing exp-, lit-, kg-, C- IDs. Mark speculation as such>

## Suggested next      (full tier)
<cheapest discriminating experiment; claims to add or revise>

## Required fixes
<only for needs-work / rejected>
```

- `accepted`: every applicable audit check passed.
- `needs-work`: fixable issues, including missing evidence the experimenter should produce.
- `rejected`: the result is wrong, or the claim isn't supported.

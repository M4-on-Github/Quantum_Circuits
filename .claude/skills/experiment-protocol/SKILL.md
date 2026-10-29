---
name: experiment-protocol
description: Pre-registered lab notebook protocol for running and logging experiments in experiments/exp-NNN/.
user-invocable: false
---

# Experiment protocol

## Order of work

1. Glob `experiments/exp-*` and create the next free `exp-NNN/`.
2. Write the README sections from Hypothesis through Method, including the prediction, before running anything. Then commit, so the prediction is timestamped before the result exists.
3. Implement in `exp-NNN/` (or `src/` if reusable). Put configs in files, not CLI flags you'll forget. Use the shared tools in `src/tools/` (results assembly, Kaggle kernel building, packaging) instead of writing per-experiment copies. If a tool you need isn't there, add it to `src/tools/` with a config interface, so the next experiment can call it.
4. Run the official verifier and save its full output to `exp-NNN/verifier.log`. Write `results.json` and fill in Results and Conclusion.
5. Commit code, README, configs, `verifier.log` and `results.json` with message `exp-NNN: <title>`. Circuit outputs stay gitignored, so their generator and config must reproduce them.
6. Report back: the result in one line, and whether the prediction held.

## Checkpoints

Runs get cut off (rate limits, permission blocks, context). Make a restart cheap:
- Commit after each milestone, not only at the end: pre-registration, code ready, kernel pushed, outputs downloaded, verified. Message `exp-NNN: <milestone>`.
- Keep a `## Status` section at the bottom of the README with one dated line: what is done, what is running (kernel slug, PID, log path), and the exact next step. Update it at each milestone. A restarted run reads this first and continues from there instead of re-deriving.

Never call the competition submit endpoint from experiment code or kernels. Only the submitter agent submits.
Never edit a prediction after seeing results. If the plan changes mid-run, add a dated `Deviations` note.

## README template

```markdown
---
id: exp-NNN
title: <short>
task: invsqrt | dqi | dfthcsos | all
tests: [C-NNN]
direction: D-NNN
status: planned | running | done
date: YYYY-MM-DD
commit: <hash of the commit that produced results>
result: <one line, filled at the end>
---

## Hypothesis
<the claim being tested, from claims.md>

## Prediction
<numbers before running: expected Q, T, cost, and score delta, with a range. Say what would refute it>

## Method
<what changed vs. which baseline (exp-ID), files, config, seeds/salts, verifier command>

## Results
<table: metric | baseline | this | change. All numbers from results.json>

## Conclusion
<prediction held / failed / inconclusive and why. Next step>

## Deviations
<only if any>

## Status
- YYYY-MM-DD HH:MM: <done / running (where) / next step>
```

## results.json

```json
{
  "exp": "exp-NNN",
  "commit": "<hash>",
  "task": "invsqrt",
  "verifier": "verify_submission_invsqrt.py",
  "verifier_cmd": "<exact command>",
  "passed": true,
  "circuit_path": "experiments/exp-NNN/out/<file>",
  "circuit_sha256": "<hash of the verified circuit>",
  "metrics": {"Q": 0, "toffoli": 0, "t_gates": 0, "cost": 0},
  "baseline": {"exp": "exp-001", "cost": 0},
  "improvement_factor": 0,
  "score_delta_factor": 0,
  "runtime_s": 0,
  "salts_or_seeds": []
}
```

- Task-specific metrics: dqi adds `failures`, `shots`, `eps_plus`, `R`. dfthcsos adds `lambda_eff`, `Lambda`, `E_gap`, `ham_error_mHa`, `max_width`, `n_circuits`.
- `improvement_factor` = baseline cost / new cost.
- `score_delta_factor` = improvement_factor^(1/3).
- For dqi, run at least 3 salts and report the mean and the range of ε+ and cost.

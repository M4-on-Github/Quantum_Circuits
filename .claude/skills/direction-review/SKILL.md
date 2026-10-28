---
name: direction-review
description: How the research lead ranks hypotheses, writes Heilmeier direction proposals, updates claims, and proposes submissions.
user-invocable: false
---

# Direction review

## Ranking hypotheses

Rank open claims by expected score gain per unit of effort.
- Expected score factor = (P(success) × improvement_factor on its task)^(1/3).
- Prefer the task whose cost has the most headroom against the public frontier.
- Prefer cheap, decisive experiments over large ones.
- Write the estimate down in the claim's `expected gain`.

## Updating claims

After a critic verdict:
- `accepted`: set the claim to supported or refuted per the result and add a dated `history` line.
- `needs-work` or `rejected`: leave the status, note it, and decide whether to re-run.

## Direction proposal: `knowledge/directions/D-NNN-<slug>.md`

Write one weekly, or whenever a direction should start, continue, pivot or be killed. The user approves it before work starts.

```markdown
---
id: D-NNN
title: <short>
decision: start | continue | pivot | kill
status: proposed | approved | rejected | active | done | killed
tasks: [...]
claims: [C-NNN]
date: YYYY-MM-DD
---

## What are we trying to do?          <plain words, no jargon>
## How is it done today?              <public frontier with kg-/lit- refs and numbers>
## What's new in our approach?
## Expected score impact              <cost and score factor, with assumptions>
## Risks and kill criteria            <the measurable result that ends this direction>
## Cost                               <experiments, compute time, days>
## Midterm check                      <what we should see after the first experiments>
## Final check                        <what "done" looks like>
```

## Submission proposal: `knowledge/submissions/S-NNN.md`

Proposals only. The user decides and runs the submission.

```markdown
---
id: S-NNN
date: YYYY-MM-DD
status: proposed | approved | submitted | declined
experiments: [exp-NNN for each task]
---

## Contents      <task → exp, local cost, factor vs. reference>
## Local score   <predicted score from verified local costs>
## Why now       <what we learn or gain; remaining daily budget>
## Risks         <dqi salt variance, anything not critic-accepted>
```

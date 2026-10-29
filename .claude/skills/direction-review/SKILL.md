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
- **Explore quota.** Of every four experiments, at least one tests an idea that is not the public frontier's design: a paper's method, an untried lever, a different decomposition. Expected-value ranking alone always picks the safe reproduction.
- **Nothing evaporates.** Every paper note with `relevance: high` and every digest's "Suggested claims" entry becomes a claim or a line under "Not pursued" in `plan.md` with the reason.

## Updating claims

After a critic verdict:
- `accepted`: set the claim to supported or refuted per the result and add a dated `history` line.
- `needs-work` or `rejected`: leave the status, note it, and decide whether to re-run.

## Direction proposal: `knowledge/directions/D-NNN-<slug>.md`

Write one weekly, or whenever a direction should start, continue, pivot or be killed. The user approves it before work starts.

Before it goes to the user, dispatch the critic on it (light tier, "review direction D-NNN"): weakest assumption, public evidence against it, what a top-20 team would do instead. Put the answer in the Options section, with your response.

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
## Options                            <at least two, with your recommendation, the strongest argument against it, and the critic's dissent>
## Expected score impact              <cost and score factor, with assumptions>
## Risks and kill criteria            <the measurable result that ends this direction>
## Cost                               <experiments, compute time, days>
## Midterm check                      <what we should see after the first experiments>
## Final check                        <what "done" looks like>
```

## Plan: `knowledge/plan.md`

The queue the user can read or veto at any time. Rewrite it every loop; keep it under a page.

```markdown
---
id: plan
updated: YYYY-MM-DD
direction: D-NNN
---

## Next experiments (in order)
| # | Claim | What it tests | Expected gain | Cost | Why now |

## Waiting on
<user decisions, running experiments, pending reviews, LB scores>

## Not pursued
- <claim or idea> — <one-line reason>
```

## Briefing: `knowledge/briefing.md`

Written for the user, not for agents. One page, plain words, rewritten every loop. Each number carries its ID so the user can go deeper.

```markdown
---
id: briefing
updated: YYYY-MM-DD
---

## Where we stand
| Task | Our best cost (exp) | Public frontier | LB top implies | Our factor / frontier factor |

## What we learned this week
- <finding, and the mechanism behind it in one or two plain sentences> (exp-, lit-, kg-)

## Open decisions
- <decision> — option A costs/gives ..., option B ... — recommended: ... — needed by: <date>

## Calibration
| exp | Predicted | Actual | Held? |
<every finished experiment; the user's own predictions from user-decisions.md too>

## Worth your time
- <up to three logbook files and why>
```

## Submission proposal: `knowledge/submissions/S-NNN.md`

Name the exact file to submit and its SHA-256. The user approves by writing `approvals/S-NNN.txt` with that hash. Only then dispatch the submitter with the S-NNN ID. The submit hook enforces all of this.

```markdown
---
id: S-NNN
date: YYYY-MM-DD
status: proposed | approved | submitted | declined
experiments: [exp-NNN for each task]
file: <path to the zip>
sha256: <hash of that file>
---

## Contents      <task → exp, local cost, factor vs. reference>
## Local score   <predicted score from verified local costs>
## Why now       <what we learn or gain; remaining daily budget>
## Risks         <dqi salt variance, anything not critic-accepted>
```

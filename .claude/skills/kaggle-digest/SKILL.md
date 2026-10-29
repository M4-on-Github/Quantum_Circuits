---
name: kaggle-digest
description: How to scan the competition's Kaggle discussions, notebooks and leaderboard with the Kaggle CLI and write a dated digest.
user-invocable: false
---

# Kaggle digest

## Commands

Kaggle CLI only. No pipes, chaining or redirects; they are blocked.

| Need | Command |
|---|---|
| Topic list (newest activity) | `kaggle competitions topics list google-verifiable-quantum-circuit-compilation` |
| One thread with comments | `kaggle competitions topics show <topic_id>` |
| Public notebooks | `kaggle kernels list --competition google-verifiable-quantum-circuit-compilation --sort-by dateRun --page-size 50` |
| Notebook source (read only) | `kaggle kernels pull <owner/slug> -p kaggle/.cache` |
| Leaderboard top | `kaggle competitions leaderboard google-verifiable-quantum-circuit-compilation --show` |

## Procedure

1. Read the newest file in `kaggle/digests/` to get the `since` date.
2. List topics and notebooks. Keep only items that are new or have new activity since then.
3. For each kept thread, `show` it. Write or update `kaggle/threads/kg-<topic_id>-<slug>.md` only if the thread has at least one of: a quoted number (Q, T, ε, cost, score), a rule or metric statement, a technique, or a null result. Everything else (orientation, chit-chat, unsourced predictions) gets one row in the digest table and no note.
4. Write `kaggle/digests/<today>.md`.

## Credibility

| Level | Source |
|---|---|
| high | Competition host or Kaggle staff. Statements about the rules or metric are binding |
| medium | Author in the LB top 50, or a claim with reproducible code or verifier output |
| low | Everything else, including unsourced score claims and speculation |

The level weights the item. Nothing from Kaggle becomes a fact in our logbook: it is a lead for a claim.

## What to extract

- Techniques and the task and cost term each one targets.
- Reported Q, T, ε, cost or score, with the exact quoted number.
- Metric or rule clarifications.
- Null results ("didn't work").
- The LB top score and the public-notebook frontier score.
- Use the author's numbers verbatim. Don't summarize code you didn't read.

## Thread note: `kaggle/threads/kg-<topic_id>-<slug>.md`

```markdown
---
id: kg-<topic_id>-<slug>
topic_id: <id>
title: <exact>
author: <name>
author_role: host | staff | top-lb | participant
credibility: high | medium | low
tasks: [...]
first_seen: YYYY-MM-DD
last_checked: YYYY-MM-DD
---

## Summary
## Claims made (quoted numbers)
## Possible claims for us
## Updates
- YYYY-MM-DD: <what changed>
```

## Digest: `kaggle/digests/YYYY-MM-DD.md`

```markdown
---
id: kg-digest-YYYY-MM-DD
date: YYYY-MM-DD
since: YYYY-MM-DD
items: N
headline: <single most important change>
---

## Leaderboard
<top score, our rank if known, public-notebook frontier>

## New or updated
| Item | Credibility | Task | What's new | Link |
|---|---|---|---|---|

## Suggested claims
- <falsifiable statement> — source kg-..., credibility
```

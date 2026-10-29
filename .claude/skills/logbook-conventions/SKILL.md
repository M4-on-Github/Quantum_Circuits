---
name: logbook-conventions
description: Layout, IDs, frontmatter fields and evidence rules for this project's research logbook.
user-invocable: false
---

# Logbook conventions

## Layout and ownership

| Path | What | Written by |
|---|---|---|
| `knowledge/claims.md` | Claims ledger, `C-NNN` | research-lead |
| `knowledge/directions/D-NNN-<slug>.md` | Heilmeier proposals | research-lead |
| `knowledge/submissions/S-NNN.md` | Submission proposals | research-lead |
| `knowledge/submissions/S-NNN-result.md` | Submission outcome | submitter |
| `approvals/S-NNN.txt` | Approval: SHA-256 of the file to submit | the user only |
| `literature/papers/lit-<arxiv-id>.md` | Paper notes (non-arXiv: `lit-<firstauthor><year>-<word>`) | lit-scout |
| `kaggle/digests/YYYY-MM-DD.md` | Dated digests | kaggle-scout |
| `kaggle/threads/kg-<topic-id>-<slug>.md` | Notes on one discussion thread or notebook | kaggle-scout |
| `experiments/exp-NNN/` | `README.md`, code, configs, `results.json` | experimenter |
| `experiments/exp-NNN/critic.md` | Review | critic |
| `src/` | Code shared across experiments | experimenter |

`INDEX.md` files are generated automatically after every write. Never edit them.
Hooks block writes outside your own paths.

## Files

- Every logbook file starts with YAML frontmatter.
- Keys are flat: `key: value` or `key: [a, b]`. No nesting.
- `id` must match the filename.
- Dates are absolute: `YYYY-MM-DD`.
- `tasks` takes values from `invsqrt`, `dqi`, `dfthcsos`, `all`.

## Linking

- Cite by ID inline: `lit-2610.23832 §III.B`, `kg-753185`, `exp-004`, `C-012`, `D-002`.
- Number IDs by taking the next free number. Glob the folder first and never reuse a number.

## Evidence rules

- Papers and Kaggle posts can only propose claims (status `hypothesis`).
- Only an experiment with critic verdict `accepted` can move a claim to `supported` or `refuted`.
- A conflicting accepted result makes a claim `contested`.
- Record a number with its source. If you didn't see it, write `unknown`. Never estimate silently.

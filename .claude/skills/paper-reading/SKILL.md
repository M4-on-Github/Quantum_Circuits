---
name: paper-reading
description: How to find, read and write a verifiable note on a paper for literature/papers/.
user-invocable: false
---

# Paper reading

## Finding

- Prefer arXiv. Fetch the abstract page, then the HTML (`arxiv.org/html/<id>`) or PDF for the full text.
- Before writing, Glob `literature/papers/` and skip papers that already have a note unless asked to update one.

## Hard rules

- Every claim, number and method step carries a locator: `§3.2`, `Eq. (14)`, `Table 2`, `Fig. 5`, `Alg. 1`, or `App. B`. If you can't point to where it is, leave it out.
- Copy numbers exactly as printed, with units. Never convert, round or estimate.
- Keep what the paper shows separate from what you infer. Inferences go only under "Relevance" and "Ideas to test", marked as yours.
- If you read only the abstract or part of the paper, say so in `read:` and don't fill sections you didn't read.

## Note template: `literature/papers/lit-<id>.md`

```markdown
---
id: lit-<id>
title: <exact title>
authors: [<first author>, <...>, <last author>]
year: YYYY
url: <arxiv abs url>
tasks: [invsqrt | dqi | dfthcsos]
relevance: high | medium | low
read: full | partial | abstract
date_added: YYYY-MM-DD
---

## Takeaway
<2-3 sentences: what this paper offers us>

## Method
- <step> (§x)

## Reported results
| Quantity | Value | Where |
|---|---|---|
| Toffoli count for ... | ... | Table 2 |

## Relevance
<which task, which cost term (Q, T, ε, λ), and why — your inference>

## Ideas to test
- <falsifiable idea: change X, expect cost term Y to drop by ~Z, because §w>

## Caveats
<assumptions that don't hold here, e.g. different precision, different cost model, asymptotic only>
```

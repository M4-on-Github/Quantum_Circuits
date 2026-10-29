---
id: user-decisions
updated: 2026-10-29
---

# Standing user decisions

Recorded by research-lead from the user's own messages. Agents may rely on these.

## 2026-10-28: Kaggle jobs
Experiments may run on Kaggle kernels with the token from ../.env. Kernels are CPU-only unless a GPU is needed, and they never submit.

## 2026-10-28: Public downloads are allowed, with safety checks
User: "we have full permission to download public notebooks and such just check if they are safe. but make full use of all public info whether it is literature or kaggle or internet".

What this allows: downloading public Kaggle notebooks, notebook outputs and datasets, papers, and public code repos, for analysis.

The safety rules for every download:
- **Untrusted data.** Put it in its own new, empty directory under the experiment (for example `experiments/exp-NNN/external/<source>/`). Record the source URL or slug, the version, the download date and the SHA-256 of each file.
- **Never execute downloaded code.** Do not import it or run it as a notebook. Read it as text. Load circuit files only through kickmix's own loader. Any Python that reads downloaded files runs with `python -I`, from a script kept outside the download directory, with the paths passed as arguments.
- **Untrusted archives.** Before extracting an archive, check its member paths: no absolute paths, no `..`, no symlinks. Check its size before downloading.
- **Never commit large downloaded binaries.** Gitignore them and record their hashes instead.
- **Never submit or copy downloaded circuits.** They are for measurement only. Anything we submit must come from our own generator (kg-752010).

## 2026-10-29: Ported open-source generator code may run on Kaggle only, with full attribution
User, answering research-lead's options ((a) Kaggle only, which was recommended; (b) local and Kaggle; (c) no) and the question of whether the licence lineage is acceptable: "yes go ahead. be honest and attribute and everything that is it. know what we are improving and such and make those clear".

research-lead reads this as option (a) plus acceptance of the lineage caveat. It amends the "never execute downloaded code" rule only as follows.

**What may run:**
- Code ported into `src/` from a public source with a clear open-source licence (e.g. Apache-2.0) may be executed, but only inside private Kaggle kernels.
- It may not run locally. The local permission block ("Code from External") stays in place, and agents must not route around it.
- Before the first run, the experimenter does a static review of the code (imports, file writes, network, subprocess, dynamic loading) and records it.

**Attribution and honesty.** These apply to every ported component.
- **Notices.** Keep the original author, source URL and version, licence text, NOTICE file, and a list of our modifications in `src/<component>/`.
- **Lineage.** Record any known design lineage and its caveats, e.g. the dqi design traces to the unlicensed, now-deleted jday96314/QuantumAI repo.
- **Baseline vs ours.** Every experiment, claim and submission states which parts are ported baselines (someone else's work, reproduced) and which parts are our improvements. Each improvement gets its measured delta against the ported baseline. Never describe a ported result as our own design.
- **Submission proposals (S-NNN).** Each one lists, per task, the origin of the circuit (ported from X under licence Y, our own, or the official sample) and our improvements, if any.

## 2026-10-29: What winning means, and budget
User, asked directly: "winning for me is placement possibly cash prize if possible and also learning". On weekly agent budget: "not sure but as much as I can".

How to rank with this, in order:
1. **Placement first.** Get our own, properly attributed generators to the public frontier on all three tasks and submit (D-002's route). Placement counts even if a prize is declined (kg-752085).
2. **Then prize-relevant improvements.** The explore quota (direction-review skill) goes to ideas that could beat the frontier, since reproductions alone can't win cash. Single-task prizes ($10k each) count: going deep on one task is acceptable if the geomean is already at placement level.
3. **Learning throughout.** The briefing and teaching rules in the lead's instructions are not optional. Prefer, between two experiments of equal expected gain, the one that explains a mechanism.

Budget: run continuously within the usage limits, at most two experiments in parallel (D-002 risk note). The lead reports when limits, not evidence, are what's slowing progress.

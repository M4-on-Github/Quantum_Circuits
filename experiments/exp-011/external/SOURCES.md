---
id: exp-011-sources
exp: exp-011
date: 2026-10-29
---

# Downloaded third-party files (exp-011)

These files are untrusted data. Nothing in this directory is imported or executed, and only this file is committed (`../.gitignore`).
- Notebooks are read as text with `../../exp-005/tools/nbtext.py` under `python -I -B`.
- The embedded `SOURCES` dicts are read with `../tools/nb_sources.py`. It parses each code cell with `ast.parse` and takes the literal with `ast.literal_eval`, so no notebook code runs. Before writing anything it checks every member path: not absolute, no `..` component.
- No archives were downloaded. Every file arrived as itself.
- No circuit was downloaded in this experiment.

All downloads were made on 2026-10-29 between 13:01 and 13:05 UTC, with `kaggle kernels pull <slug>[/<version>] -m` (Kaggle CLI 2.2.5).
- `kernels pull` accepts `owner/slug/N`. The ipynb filename is always the current slug's, whatever the version.
- The CLI gives no creation date per version, so version dates are `unknown`.

## Licence of every source

| Source | Licence stated | Where |
|---|---|---|
| SomeJoint notebook, all versions read (v14 = the 897 builder) | **Apache-2.0** | Embedded `LICENSE` file: the full Apache-2.0 text, SHA-256 `cfc7749b…3d30`, byte-identical to the competition's `data/kickmix/LICENSE.txt`. Credits cell: "The circuits keep their authors' licences; the notebook code is Apache-2.0". `notebooks/launch.py` and `take.py` also carry `SPDX-License-Identifier: Apache-2.0`. The 69 decoder files carry no per-file header. |
| saurabhkumar234 "DQI Width Anatomy 897 Qubits" | none stated for its own text. It calls SomeJoint's builder "Public Apache-2.0; notices retained" | cell 7 |
| avazaku "Slack Homotopy + 897-Qubit DQI" | not needed. It uses SomeJoint v20's `dqi.kmb` (`53d8b2ed…`) unchanged and holds no decoder source | cell 0 |
| jday96314/QuantumAI (GitHub), upstream of the design | **none**. "That repository states no license" appears in SomeJoint v13 to v21, in Özer's `DQI_NOTICE.md` (embedded in v13) and in the alexchilton notebook. The repository now returns HTTP 404 (`api.github.com/repos/jday96314/QuantumAI` and `github.com/jday96314/QuantumAI`, checked 2026-10-29 about 13:15 UTC), so its current state can't be checked. Not downloaded. | |

**Provenance chain of the 897 decoder, as its authors state it.**
- **Pro's three new files** (`final_decoder/`) and the 658-Toffoli jet (`exp/jet24/pro_jet.py`): GPT-6 Astra Pro, asked by SomeJoint.
- **The kit modules**: SomeJoint's "fused decoder". SomeJoint v10 to v12 describe its decoder as "rebuilt from scratch", from a design that "starts from" Alex Chilton's 883-qubit Schur decoder.
- **Chilton's decoder**: "The decoder is jday96314's … Rebuilt it from their code" (`kaggle/.cache/alexchilton-22-57-portfolio/22-57-lb-verified-three-task-portfolio.ipynb`, cell 9).
- **So**:
  - The code we port is licensed Apache-2.0 by SomeJoint, who states it is a from-scratch rebuild.
  - The design lineage runs through an unlicensed repository whose code Chilton reused.
  - We did not compare SomeJoint's text with jday96314's code, because the repository is gone.

## nb-somejoint-versions/vN/

Notebook `somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi`, `id_no` 140675727.
- It is the notebook exp-005 pulled under an earlier slug: its v18 file is byte-identical to exp-005's `b44fc04a…` download.
- Versions 22 to 29 do not exist (`pull` fails).
- Versions 2 to 4 and 6 to 9 were not pulled.

| Version | Bytes | SHA-256 | Title (cell 0) |
|---|---|---|---|
| v1 | 288234 | 116c0d55c00ce0892e6b555a9c4b932c26cd27f1c51b11da7e1988a4a804b0c2 | Quantum Circuits: 8.95, Every Cost Explained |
| v5 | 661096 | 8e9aecfd1da53dc5a7dca0e5a42b5c46cd197b263fd4c35bb872c0ffc292d8e5 | 11.81 LB: Cost Gains |
| v10 | 387937 | 8982773adde717e1f84d1b671f9fb8909c6ac6954632efa9e5e18ea3438eda56 | 20.96 Local GM: Confluent DQI |
| v11 | 374457 | 031466450afff77a96e20adae770ec8b747fb090bea73e8b0cf4e19a3ef5522c | 21.20 Local GM: Taylor DQI |
| v12 | 406991 | 18d6760953783bec316ddb46266a1b5ccc50c291fbf47ec35f87c73f4d0cf2ac | 21.34 Local GM: Fused DQI |
| v13 | 449980 | e687c12b974522737a04b1ea005ee243129c4cb7a65eff07600eec9ccfb637e4 | 21.98 Local GM: 883-Qubit DQI |
| **v14** | 369614 | **b7e42f52411165caa1ab07d419b46c10a0fbcd5edd97086aadafe71383ef43ff** | **22.34 Local GM: 897-Qubit DQI**. States Q 897, mean T 440,633.0, cost 4.22346e+11, build `b3354f60…` |
| v15 | 482491 | 5f8201122733c55ff5268eff99ff610f166989690fd2683f3512aed5151d8c73 | 22.44 Local GM: Our Chemistry |
| v16 | 105947 | 0c573d3b36497513230865182ea6479de9b01995c5d746f5c9c72320bf4a4aa6 | 22.63 Local GM: Full-XOR Chem |
| v17 | 106806 | bd2eab423689e10f8c0ae5c9bbb2502b33682141853f285841099076ce4e82ca | 22.67 Local GM: Full-XOR Chem |
| v18 | 107029 | b44fc04a99ab0c18afce4c7d8408ddc079dd8a87957e294d2102494d8d9b001a | 22.67 Local GM: Full-XOR Chem |
| v19 | 409034 | 6b35d50c4d4e1ce2cdecb44573eb8fcbe6caa8d6ec863fd5ec817309a75100f4 | 22.73 Local GM: 897-Qubit DQI (team-1028). States mean T 431,732.9, cost 4.13815e+11 |
| v20 | 419631 | 0069cff9b222d13f298e415615fa5ed0687c5a819d2e1d85161cb857b8523a87 | 22.75 Local GM: 897-Qubit DQI (team-1028-stream). Its build.py states `53d8b2ed…`, mean T 430,822.9, cost 4.12943e+11 |
| v21 | 470668 | f0ca002084da37a9419706f7e2065709e04ddc5f84796e37b401100b90c34135 | 22.77 Local GM: 889-Qubit DQI (team-1028-narrow240). States mean T 437,947.6, cost 4.14212e+11 |

So heliosli/qcc-circuits-live v15's `dqi.kmb` `53d8b2ed…` is SomeJoint's **v20** decoder. That is a different, cheaper design than the v14 `b3354f60…` decoder named in C-016.

## somejoint-v14-sources/

The 73 entries of v14's `SOURCES` dict, written out as text by `nb_sources.py dump`.
- All 73 SHA-256 values equal v14's own `SOURCE_HASHES` entries.
- v14's `NOTEBOOK` record gives `assembled_from_commit` `98286bd634320b11254f9b3c2d83948eb3d18f3c`.

What the entries are:
- `LICENSE`: Apache-2.0, `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
- `blocks/dqi/pro-q2-897/source/`: 69 files making up the 897 builder: `build_897.py` `82026453…`, `README.md` `02836173…`, `decode.py`, `exp/`, `final_decoder/`, `playbook/` and `source_sha256.json`. Their per-file hashes are in `src/dqi/MANIFEST.json`, which our port checks at build time.
- `notebooks/`: 4 notebook helper files, not ported.

## nb-saurabhkumar234_dqi-width-anatomy-897-qubits/

`saurabhkumar234/dqi-width-anatomy-897-qubits`, `id_no` 141290036, latest version, lastRunTime 2026-10-28 06:23:12 UTC.
- It states an independent byte-identical rebuild of `build_897.py`: SHA-256 `b3354f60…32fd6`, Q 897, T_static 454,477, num_ops 55,778,145.
- It used the competition `kickmix.so` on CPython 3.13.18, numpy 2.5.4 and scipy 1.18.1.

| File | Bytes | SHA-256 |
|---|---|---|
| dqi-width-anatomy-897-qubits.ipynb | 8131 | f2b9805bde57f13edd6853fe2c57dffeffa85cabb29c40afddd3c436512a91d7 |
| kernel-metadata.json | 668 | 689eec2a2af4593100a57165f9a8389b8f8700c40b862bd331e3c96607b365c6 |

## nb-somejoint_quantum-circuits-22-77-local-gm-889-qubit-dqi/ (latest, which is v21)

| File | Bytes | SHA-256 |
|---|---|---|
| quantum-circuits-22-77-local-gm-889-qubit-dqi.ipynb | 470668 | f0ca002084da37a9419706f7e2065709e04ddc5f84796e37b401100b90c34135 |
| kernel-metadata.json | 808 | 227e1205cb8750728289da55927c4e6f275f0c8f103fa70e84574e6c6f52af2b |

## nb-avazaku_slack-homotopy-897-qubit-dqi/

`avazaku/slack-homotopy-897-qubit-dqi`, `id_no` 141420867, latest version.

| File | Bytes | SHA-256 |
|---|---|---|
| slack-homotopy-897-qubit-dqi.ipynb | 102928 | 1e15c0f432a033e32632c34f2f422e5dc2c3a8e57ff02b8a22500d525fa9199b |
| kernel-metadata.json | 729 | 75479dc8fcd8bec4b5c0f24b6c3090662d5bda7b8f3795d8d575816de6a3f07e |

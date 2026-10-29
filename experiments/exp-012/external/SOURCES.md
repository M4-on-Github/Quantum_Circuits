---
id: exp-012-sources
exp: exp-012
date: 2026-10-29
---

# Downloaded third-party files (exp-012)

These files are untrusted data. Nothing in this directory is imported or executed, and only this file is committed (`../.gitignore`).
- Notebooks are read as text with `../../exp-005/tools/nbtext.py` under `python -I -B`.
- Embedded `SOURCES` dicts are written out with `../../exp-011/tools/nb_sources.py` (`ast.literal_eval` only, member paths checked).
- The one archive (`ds-somejoint-xor2/*.zip`) was extracted with `../tools/safe_unzip.py` after checking every member path (no absolute paths, no `..`, no symlinks). Two members, both data.
- No circuit file was downloaded in this experiment.

All downloads: 2026-10-29, between about 20:17 and 20:25 UTC (local clock 16:17 to 16:25), Kaggle CLI 2.2.5.
- Notebooks: `kaggle kernels pull <slug>[/<N>] -p <dir> [-m]`. Version dates are `unknown` (the CLI gives none).
- Datasets: `kaggle datasets download <slug> [-f <file>] -p <dir>`. Versions identified with `kaggle datasets files <slug>/<N> --format csv`.

## Licence of every source read

| Source | What it holds for chemistry | Licence stated | Where |
|---|---|---|---|
| SomeJoint notebook `somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi` (id 140675727) v18, "22.67 Local GM: Full-XOR Chem" | Embedded `SOURCES`: the B143 C60 xor2 build (`build.py`, 5 emitter/helper modules, README, `source_sha256.json`) | **Apache-2.0** | Embedded `LICENSE` (full Apache-2.0 text, SHA-256 `cfc7749b…3d30`, byte-identical to the competition's `kickmix/LICENSE.txt`); `build.py` header `SPDX-License-Identifier: Apache-2.0`; credits cell: "the notebook code is Apache-2.0" |
| Dataset `somejoint/qcc-our-chemistry-b143-c60-xor2` v1 (the only version; id 12922479) | `submission.npz` (factorization and angle words) and `BUILD.json` (each circuit's frozen plan and schedule) | **Apache-2.0** | Dataset metadata `licenses: [apache-2.0]`; description ends "Licence: Apache 2.0." |
| SomeJoint notebook v15 ("22.44 Our Chemistry", B143 C62) and v16 (B143 C60 xor) | Earlier builds of the same family | Apache-2.0 (same embedded LICENSE) | not ported |
| kirilltym `quantum-circuits-exact-gauge-5-word-qrom` (id 140275741), current version | No generator. Integrates Atakan's compiled chemistry by hash and reruns verifiers; MPS phase audit | "New integration/audit code is Apache-2.0" | not ported (no chemistry generator in it; the "exact gauge" code of earlier versions is not in the current one) |
| atakanaldemir `qcc-888q-repair-and-native-chemistry-co-design` (id 141478744) and dataset `atakanaldemir/qcc-native-chemistry-and-888q-source-bank` | Learned factor `factorization.npz`, 15 plans, `rebuild_native.py`, and 21 producer/training scripts (`11_optimize_gauge_lp_trust.py`, `13_train_chemistry_joint.py`, …) | **Unclear.** `chemistry/LICENSE.md`: "Each exported source or asset retains its applicable recorded author terms. No blanket Apache-2.0 licence is asserted"; the only Apache-2.0 sentence is a verbatim "historical seed-dataset notice" about another author's work | not ported (licence not clearly stated for Atakan's own files). Only the 7 licence/readme/manifest files were downloaded |
| dmitriigluzdov `quantum-circuit-compilation-from-source` (id 140416287), dataset `dmitriigluzdov/vqcc-femoco-public-factorization` | Describes the factorization pipeline in prose; the dataset holds frozen `submission.npz` files per version and loader emitters from frozen plans (`open_circuits_v41/source/`). No factorization or gauge code found in its 536-file listing | "this notebook and its dataset are released under Apache 2.0" | listed only (`kaggle datasets files`), nothing downloaded from the dataset |
| ahmedberatozer `quantum-ai-df-thc-group-compression` (id 140603701), v14 | PSD weight update applied as a stored delta (`apply_weight_delta.py`) to Atakan's factor | "Our scripts are Apache-2.0" | not ported |
| heliosli `the-dataset-is-public-now-enjoy` (id 141060698), leoprovorov `full-xor-chemistry-no-borrowed-bits` (id 141336180), lightningv08 `bezout-schur-5-word-qrom` (id 140278322), phucthaiv02 `qcc-verified-portfolio-df-thc-retraining-study` (id 140619581) | Portfolio assembly, a gauge probe (leoprovorov), other factorization families (R4/B255/C128; R24/60/30) | various | read only, not ported |

**No public source found regenerates the R8/B143/C60 factorization.** SomeJoint's notebook says its team pruned B154 to B143, lowered the rank to 60, requantized to 8-bit words with coded low bits, and fitted the weights (v18 credits cell), but the code for those stages is not in any public notebook or dataset found. Every public build of this family copies a frozen `submission.npz`.

## nb-somejoint/

| Version | Bytes | SHA-256 |
|---|---|---|
| v15 | 482491 | 5f8201122733c55ff5268eff99ff610f166989690fd2683f3512aed5151d8c73 |
| v16 | 105947 | 0c573d3b36497513230865182ea6479de9b01995c5d746f5c9c72320bf4a4aa6 |
| v17 | 106806 | bd2eab423689e10f8c0ae5c9bbb2502b33682141853f285841099076ce4e82ca |
| **v18** | 107029 | **b44fc04a99ab0c18afce4c7d8408ddc079dd8a87957e294d2102494d8d9b001a** |
| latest (v21) | 470668 | f0ca002084da37a9419706f7e2065709e04ddc5f84796e37b401100b90c34135 |

These equal the hashes recorded in `experiments/exp-011/external/SOURCES.md` for the same versions. v18's `NOTEBOOK` record: `assembled_from_commit` `d5317831e36961852010cfb5b35c938f9ea3af28`. All 13 v18 `SOURCES` entries match v18's own `SOURCE_HASHES`.

v18 states its chemistry result (`EXPECTED['dfthcsos']`): PASS, score 343,172,572.78225887, lambda_eff 48.76425214813735, toffoli_count 16,366.0, num_qubits 430, 15 circuits, verified_shots 78,080, submission_sha256 `c88f058efddd1b273a7161ebdb57740ff3da36452acf337995c19ff67951a414`.

## sj-v18-sources/ (v18 `SOURCES`, written out)

| File | SHA-256 |
|---|---|
| LICENSE | cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 |
| blocks/dfthcsos/team-b143-c60-xor2/source/build.py | 2438a6b9ec82c8cf1f760a5276e2bc55fb669fd87ab8b24835ab1eeb4a86c8a5 |
| …/source/README.md | 8444fd68f378c95b8b200dd0d0b3dc414552337a753843db93956efd65f9d6c1 |
| …/source/source_sha256.json | 3fb3568aed0dea4f33099db638fa41b803fbe8f5e6a7b3f440f46777bdff1d70 |
| …/source/exp/full_xor/emitter.py | 64810f36e4c6dc01f94d2315eb0e9e4f3d1580cab3d29c1e9a977d06431099ce |
| …/source/playbook/exp/staged_b154/paired_anf.py | ecc419266710033469abeaa2fc9c1ed542a3a5cdaf37e9a72c65c4297e67b633 |
| …/source/playbook/exp/staged_b154/planio.py | f4c4d3d7e9a24c152df57300d5666f7240fddb682da52420b46d061bd5e3b650 |
| …/source/playbook/exp/staged_b154/scheduler.py | 1d14b12709aeafb068667d3f48140b9b914b48d7add5e7a1f600aaec30007085 |
| …/source/playbook/exp/staged_b154/validation_helpers.py | ae776666c53e9181632c77e3d59973fa3809022bb008efb0df5e7b381fa36aac |
| notebooks/{launch.py, take.py, check-submission, extra-format.py} | 72179eb4…, 64b52764…, b1a0e519…, 6593250b… (notebook helpers, not ported) |

`sj-v15-sources/` (92 files) and `sj-v16-sources/` (13 files) were written out the same way, for reading only.

## ds-somejoint-xor2/

`kaggle datasets download somejoint/qcc-our-chemistry-b143-c60-xor2` (v1, files created 2026-10-28 13:11:57 UTC).

| File | Bytes | SHA-256 |
|---|---|---|
| qcc-our-chemistry-b143-c60-xor2.zip | 1471736 | 5c174e16eb000bb258ce9c8f690d5586d7fb9e07ca8b33251922b40df3b66fbe |
| v1/BUILD.json | 465650 | 5e28b8fe7ea1b7448d0e1782c7f58d9feae58fdc71318d27c39dd21ee9130c90 |
| v1/submission.npz | 1995236 | aef36d39b83bbbf696e909884218f6c02f067baef14a29de1c41306bc1f6395b |
| dataset-metadata.json | | 536d8d4b1a8d82b821b3bd3afab7993091687e474503c8fb0479090100f97aaa |

Both data hashes equal the ones pinned in v18's `source_sha256.json`. `submission.npz` is byte-identical to heliosli/qcc-circuits-live v11's `dfthcsos__submission.npz` (`aef36d39…`, exp-006 `external_manifest.json`), so the exp-006 v11 build and this build share their factorization file. BUILD.json's `circuit_sha256` for k = 5, 7, 9, 11, 13 equal heliosli v11's manifest hashes for those files (`tools/read_build_json.py`).

## Other notebooks (read as text, not ported)

| Path | SHA-256 |
|---|---|
| nb-kirilltym/quantum-circuits-exact-gauge-5-word-qrom.ipynb | 4deb3439d808381783e3c162da2f15fac6af181d18b7ecb1e601544fcb44b386 |
| nb-atakanaldemir_…/qcc-888q-repair-and-native-chemistry-co-design.ipynb | bc1cb9337fbb6fe9d0ead7ac213e6fb4988221d676018d3d988361c6ef74fcdd |
| nb-dmitriigluzdov_…/quantum-circuit-compilation-from-source.ipynb | add82334b288a8d7121286e07c92b7b139db8581620393a018396dba4c4f2945 |
| nb-ahmedberatozer_…/quantum-ai-df-thc-group-compression.ipynb | 7535cd0728ded0a7006bebe1e18251e553c3525a5b886b4cfaa219ac9573fbbd |
| nb-heliosli_…/the-dataset-is-public-now-enjoy.ipynb | ca400d91b39b94e4fb7c7a888204103fdaa5ed9242839d10bc8b85a002e87bda |
| nb-leoprovorov_…/full-xor-chemistry-no-borrowed-bits.ipynb | 9cf3ad4cef4b34d0ae21b76f83ab9edb4316a0ad2e4916841e1a2e903f9faaa2 |
| nb-lightningv08_…/bezout-schur-5-word-qrom.ipynb | 17a0cc7b03d283fb2f7b2816fb4aff85090b1c43c602812a7890e0459bab399f |
| nb-phucthaiv02_…/qcc-verified-portfolio-df-thc-retraining-study.ipynb | 2748246815e10c09885e5829357add32ea2aeaa45f56499630c32bbea0727935 |

## ds-atakan/ (licence and readme files only)

| File | SHA-256 |
|---|---|
| README.md | 6a3fd53aa093c4787a3c928155d3a94546a6f7dda7dea10645c19b390a3b4d0b |
| chemistry/LICENSE.md | 84ab9263bbeaebf17ad1a593f4e39b6bb59b92b295799a8f63734c35e0d1c86f |
| chemistry/README.md | 707db6c78f06712456b1982747086fc45fe2ca3c01ca85b4a10332cd3f294311 |
| chemistry/CREDITS.md | c5f4b4d44c3a50d5c8f7501787331afe1408859534c736952f9bfe9aa21ab87a |
| chemistry/DATASET_CARD.json | 6f1a13d8335e8f2f44d950efb38f61cc08f67d7a28b2ce29c6f6d37d96ad53cd |
| chemistry/MANIFEST.json | 1dca791a732d8e079f2d510701f6031c8255be99ac6651489d199a6775fe54b1 |
| chemistry/SOURCE_MANIFEST.json | 5f20d94b4093166b5f399032c800232834f2979385520fa3f6891a718836d179 |

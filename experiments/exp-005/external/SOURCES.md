---
id: exp-005-sources
exp: exp-005
date: 2026-10-28
---

# Downloaded third-party files (exp-005)

These are untrusted data, kept for measurement only. Nothing in this directory is executed, imported or committed except this file. Notebooks are read as text with `../tools/nbtext.py` under `python -I`. Circuits are loaded only with kickmix's `Circuit.from_file`, which runs on Kaggle.

Downloads were made on 2026-10-28, around 19:21 UTC, with the Kaggle CLI 2.2.5 (`kaggle datasets download -f`, `kaggle kernels pull -m`).
- No archives: every file arrived as itself, not zip-wrapped.
- `dqi.kmb.xz` is a single XZ stream (`file`: "XZ compressed data, checksum CRC64"), with no member paths.

## heliosli-qcc-circuits-live/

Dataset `heliosli/qcc-circuits-live`, Apache-2.0 per its metadata.
- The CLI shows no version number. `kaggle datasets list --user heliosli` reports lastUpdated `2026-10-28 15:57:44.233` and size 11,032,009 B. Every file's creationDate is 2026-10-28 15:57:47 to 15:57:48.
- Manifest `portfolio: "v17_sjx"`. The heliosli notebook, cached copy SHA-256 7f68a867...653e, asserts `v15b_sjmixL`, so the dataset has moved on since that notebook version.

| File | Bytes | SHA-256 |
|---|---|---|
| dqi.kmb.xz | 9,144,688 | 07db71ee28c1d3bfaf2496c92dd7153eb0d01ced3797a8d95502ccf0fa541c33 |
| dqi.kmb (xz content, streamed, not written locally) | 505,139,960 | 4ee7a17b4cbca4053a19bc951e7f2ef91fabdbb036006c9d658adcff4fe76da4 (equals the manifest entry) |
| QCC_RELEASE_MANIFEST.json | 3,663 | e32f07075055fe45a276b7dbd0e67077f1906c8f7cf346868a8d00049bc0ba1a |
| CREDITS.md | 1,899 | d45c0367542be9954f09d34f81d2b1bc01aba8cf4b73741755d7222b155384dd |
| LICENSE.md | 535 | ddd71764aaf7930662ae40ecd18070bf099d5537397cd6edf51db706261340fe |

Licence note from LICENSE.md: the DQI decoder design comes from jday96314's QuantumAI repository, "which states no licence". Measurement only. We do not reuse it.

## somejoint-22-67-notebook/

Notebook `somejoint/quantum-circuits-22-67-local-gm-full-xor-chem` (id_no 140675727), lastRunTime 2026-10-28 13:30:38 UTC per `kaggle kernels list --user somejoint`. `kernels pull` gives the latest version, and the CLI shows no version number.
- The slug named in CREDITS.md, `somejoint/quantum-circuits-22-34-local-gm-897-qubit-dqi`, no longer resolves (`kernels pull` fails). This is SomeJoint's only public notebook now.
- It embeds no DQI generator. Cell 3 says its DQI is heliosli's 889-qubit modification of SomeJoint's 897-qubit decoder, used unchanged.

| File | Bytes | SHA-256 |
|---|---|---|
| quantum-circuits-22-67-local-gm-full-xor-chem.ipynb | 107,029 | b44fc04a99ab0c18afce4c7d8408ddc079dd8a87957e294d2102494d8d9b001a |
| kernel-metadata.json | 862 | b97cf75f2c368310e51cc75f3e3bceda626c52f7b5ec02ecf063583174559ba6 |

## Read in place (already downloaded by kaggle-scout, not re-downloaded)

| File | SHA-256 | Used for |
|---|---|---|
| kaggle/.cache/alexchilton-22-57-portfolio/22-57-lb-verified-three-task-portfolio.ipynb | 9d0980a719eb5f1e2dfe761837da11b478b46562a5fd6decbc5697fb4573bd6a | Decoder lineage and design text: jday96314 Schur decoder, "42-AND GF(2^12) multiplier" |
| kaggle/.cache/heliosli-dataset-now-public/the-dataset-is-now-public-now-enjoy.ipynb | 7f68a8671b3a6e9eee356e7cc117880acd910cfa54bff6820c42fbc31ff7653e | Dataset slug, manifest format |

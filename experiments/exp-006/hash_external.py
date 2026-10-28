"""exp-006: record provenance + SHA-256 of every file under external/ into external_manifest.json.
Usage: python -I hash_external.py <external_dir> <out_json>. Reads files as bytes only."""
import hashlib, json, sys
from pathlib import Path

SOURCES = {
    "heliosli-qcc-circuits-live-v10": {"kind": "kaggle dataset", "slug": "heliosli/qcc-circuits-live", "version": 10,
        "how": "kaggle datasets download heliosli/qcc-circuits-live/10 -f <file>", "portfolio": "v15b_sjmixL"},
    "heliosli-qcc-circuits-live-v11": {"kind": "kaggle dataset", "slug": "heliosli/qcc-circuits-live", "version": 11,
        "how": "kaggle datasets download heliosli/qcc-circuits-live -f <file> (latest = v11 on 2026-10-28; version inferred from v11 manifest match)",
        "portfolio": "v17_sjx"},
    "heliosli-manifests": {"kind": "kaggle dataset (manifest only)", "slug": "heliosli/qcc-circuits-live", "version": "2..11 (subdir vN)",
        "how": "kaggle datasets download heliosli/qcc-circuits-live/N -f QCC_RELEASE_MANIFEST.json"},
    "nb-somejoint-quantum-circuits-22-44-local-gm-our-chemistry": {"kind": "kaggle notebook", "slug": "somejoint/quantum-circuits-22-44-local-gm-our-chemistry",
        "version": "n/a", "how": "kaggle kernels pull -m: not found (404); empty directory"},
    "nb-somejoint-quantum-circuits-22-67-local-gm-full-xor-chem": {"kind": "kaggle notebook", "slug": "somejoint/quantum-circuits-22-67-local-gm-full-xor-chem",
        "version": "latest on 2026-10-28 (lastRunTime 2026-10-28 13:30:38 UTC)", "how": "kaggle kernels pull -m; sources_as_text/ = ast.literal_eval of its SOURCES dict, written as .txt"},
}

ext, out = Path(sys.argv[1]), Path(sys.argv[2])
rec = {"downloaded": "2026-10-28", "rules": "knowledge/user-decisions.md 2026-10-28; never executed; gitignored", "sources": {}}
for d in sorted(p for p in ext.iterdir() if p.is_dir()):
    files = {}
    for f in sorted(d.rglob("*")):
        if f.is_file():
            files[str(f.relative_to(d)).replace("\\", "/")] = {"bytes": f.stat().st_size,
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
    rec["sources"][d.name] = {**SOURCES.get(d.name, {}), "files": files}
out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
print({k: len(v["files"]) for k, v in rec["sources"].items()})

"""exp-006: hash, safety-check and statically inspect a downloaded dfthcsos build.

Run as:  python -I inspect_build.py <label> <raw_dir> <verifiers_dir> <out_json> [<stage_dir>]

- raw_dir holds files named like the heliosli release (dfthcsos__angle_k_<k>.kmb,
  dfthcsos__submission.npz, QCC_RELEASE_MANIFEST.json). They are untrusted data:
  nothing in raw_dir is imported or executed; circuits are read only by
  kickmix.Circuit.from_file, the npz only by numpy.load(allow_pickle=False) after
  its zip members are checked.
- verifiers_dir is the official competition verifiers/ directory; it is put on
  sys.path only to use scoreinfra.register_layout (official, unmodified code).
- stage_dir (optional): writes angle_k_<k>.kmb + submission.npz copies there, the
  layout verify.py reads, after the hashes check out.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import stat
import sys
import time
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def check_npz_members(path: Path) -> list[dict]:
    members = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = info.filename
            mode = (info.external_attr >> 16) & 0o170000
            bad = (
                name.startswith(("/", "\\"))
                or ":" in name
                or ".." in Path(name).parts
                or "/" in name
                or "\\" in name
                or mode == stat.S_IFLNK
                or not name.endswith(".npy")
            )
            members.append({"name": name, "file_size": info.file_size,
                            "compress_size": info.compress_size, "ok": not bad})
            if bad:
                raise SystemExit(f"unsafe npz member {name!r} in {path}")
    return members


def main() -> None:
    label, raw_dir, verifiers_dir, out_json = sys.argv[1:5]
    stage_dir = Path(sys.argv[5]) if len(sys.argv) > 5 else None
    raw = Path(raw_dir)
    sys.path.insert(0, str(Path(verifiers_dir).resolve()))
    import numpy as np
    import kickmix as km
    from importlib.metadata import version
    from dfthcsos.scoreinfra.circuits import register_layout

    manifest = json.loads((raw / "QCC_RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    expected = {item["stored_as"]: item for item in manifest["files"]}
    files = {}
    for p in sorted(raw.iterdir()):
        if p.is_symlink() or not p.is_file():
            raise SystemExit(f"unexpected non-regular entry {p}")
        digest = sha256(p)
        exp = expected.get(p.name)
        files[p.name] = {
            "bytes": p.stat().st_size,
            "sha256": digest,
            "matches_release_manifest": None if exp is None else (exp["sha256"] == digest and exp["bytes"] == p.stat().st_size),
        }
    dft_items = [n for n in expected if n.startswith("dfthcsos__")]
    for n in dft_items:
        if n not in files or not files[n]["matches_release_manifest"]:
            raise SystemExit(f"{n}: missing or SHA-256 mismatch against the release manifest")

    npz_path = raw / "dfthcsos__submission.npz"
    members = check_npz_members(npz_path)
    arrays = {}
    with np.load(npz_path, allow_pickle=False) as z:
        for key in z.files:
            a = z[key]
            arrays[key] = {"shape": list(a.shape), "dtype": str(a.dtype)}
            if a.dtype.kind in "iu" and a.size:
                arrays[key].update(min=int(a.min()), max=int(a.max()))
        w_shape = z["W"].shape
        angle_words = z["angle_words"] if "angle_words" in z.files else None
    R, B, C = (int(x) for x in w_shape)

    n_circ = len([n for n in dft_items if n.startswith("dfthcsos__angle_k_")])
    circuits, per = [], []
    t0 = time.time()
    for k in range(n_circ):
        c = km.Circuit.from_file(str(raw / f"dfthcsos__angle_k_{k}.kmb"), format="kmb")
        circuits.append(c)
        st = c.operation_statistics()
        regs = {name: len(qs) for name, qs in c.register_data.items()}
        per.append({
            "k": k,
            "num_qubits": int(c.num_qubits),
            "num_bits": int(c.num_bits),
            "static_toffoli_like": int(st.num_toffoli_like),
            "num_instructions": int(st.num_instructions),
            "reaction_depth": int(c.reaction_depth()),
            "spare_under_128": 128 - int(c.num_qubits),
            "op_counts": {str(key): int(v) for key, v in st.items()},
            "registers": regs,
        })
    layout = register_layout(circuits)
    sel, J, brot = len(layout.selection), int(layout.batch_size), int(layout.brot)
    for row in per:
        row["workspace_qubits"] = row["num_qubits"] - sel - J * brot
    load_s = time.time() - t0

    summary = {
        "label": label,
        "portfolio": manifest.get("portfolio"),
        "manifest_local_metric": manifest.get("local_metric"),
        "kickmix_version": version("kickmix"),
        "numpy_version": np.__version__,
        "R": R, "B": B, "C": C,
        "num_addresses": 76 + R * B,
        "selection_qubits": sel, "J": J, "brot": brot, "n_circuits": n_circ,
        "max_width": max(r["num_qubits"] for r in per),
        "min_spare_under_128": min(r["spare_under_128"] for r in per),
        "static_toffoli_sum_one_pass": sum(r["static_toffoli_like"] for r in per),
        "static_toffoli_both_passes": 2 * sum(r["static_toffoli_like"] for r in per),
        "angle_words_in_npz": None if angle_words is None else list(angle_words.shape),
        "npz_members": members,
        "npz_arrays": arrays,
        "files": files,
        "per_circuit": per,
        "load_inspect_s": round(load_s, 2),
    }
    if stage_dir is not None:
        stage_dir.mkdir(parents=True, exist_ok=True)
        for k in range(n_circ):
            shutil.copyfile(raw / f"dfthcsos__angle_k_{k}.kmb", stage_dir / f"angle_k_{k}.kmb")
        shutil.copyfile(npz_path, stage_dir / "submission.npz")
        for p in stage_dir.iterdir():
            src = raw / ("dfthcsos__" + p.name)
            assert sha256(p) == files[src.name]["sha256"], p
        summary["staged_to"] = str(stage_dir)
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("files", "per_circuit", "npz_members", "npz_arrays")}, indent=1))
    for r in per:
        print(r["k"], r["num_qubits"], r["static_toffoli_like"], r["workspace_qubits"], r["num_instructions"], r["op_counts"])


if __name__ == "__main__":
    main()

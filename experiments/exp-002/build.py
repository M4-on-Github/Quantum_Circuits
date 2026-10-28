"""exp-002: build our ANGLE_k family and assemble the swapped dfthcsos submission.

Usage (repo root): .venv/Scripts/python.exe experiments/exp-002/build.py
Reads config.json next to this file. Writes out/submission/ (sample submission.npz
copied byte for byte + our angle_k_*.kmb) and out/build_report.json.
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from angleload import build_family, circuit_stats, write_family  # noqa: E402

import kickmix as km  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    cfg = json.loads((Path(__file__).parent / "config.json").read_text())
    sample = ROOT / cfg["sample_dir"]
    out = ROOT / cfg["out_dir"]
    npz_path, key = cfg["angle_words_source"].split(":")
    pinned = cfg.get("angle_words_source_sha256")
    if pinned is not None and sha(ROOT / npz_path) != pinned:
        raise SystemExit(f"input {npz_path} SHA-256 {sha(ROOT / npz_path)} != pinned {pinned}")
    with np.load(ROOT / npz_path, allow_pickle=False) as z:
        words = np.array(z[key], dtype=np.int64)

    t0 = time.perf_counter()
    circuits = build_family(words, cfg["brot"], cfg["J"])
    t_build = time.perf_counter() - t0

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    paths = write_family(circuits, out, cfg["format"])
    shutil.copyfile(sample / "submission.npz", out / "submission.npz")

    stats = circuit_stats(circuits)
    sample_paths = sorted(sample.glob("angle_k_*.kmb"), key=lambda p: int(p.stem.split("_")[-1]))
    sample_stats = circuit_stats([km.Circuit.from_file(p) for p in sample_paths])
    rows = []
    for s, ss, p, sp in zip(stats, sample_stats, paths, sample_paths):
        ours, theirs = p.read_bytes(), sp.read_bytes()
        rows.append({
            **s,
            "file": p.name,
            "sha256": hashlib.sha256(ours).hexdigest(),
            "bytes": len(ours),
            "sample_sha256": hashlib.sha256(theirs).hexdigest(),
            "sample_bytes": len(theirs),
            "sample_num_qubits": ss["num_qubits"],
            "sample_toffoli_static": ss["toffoli_static"],
            "sample_num_instructions": ss["num_instructions"],
            "bit_identical": ours == theirs,
        })
    report = {
        "config": cfg,
        "n_circuits": len(circuits),
        "n_sample_circuits": len(sample_paths),
        "angle_words_shape": list(words.shape),
        "build_seconds": round(t_build, 3),
        "submission_npz_identical": sha(out / "submission.npz") == sha(sample / "submission.npz"),
        "all_bit_identical": len(paths) == len(sample_paths) and all(r["bit_identical"] for r in rows),
        "circuits": rows,
    }
    (out.parent / "build_report.json").write_text(json.dumps(report, indent=2))
    for r in rows:
        print(r["file"], r["num_qubits"], r["toffoli_static"], r["num_instructions"],
              "identical" if r["bit_identical"] else "DIFFERENT")
    print("npz identical:", report["submission_npz_identical"], "all identical:", report["all_bit_identical"],
          "build s:", report["build_seconds"])


if __name__ == "__main__":
    main()

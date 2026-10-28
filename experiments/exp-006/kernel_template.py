"""exp-006: official dfthcsos verify.py on the public heliosli 430Q builds (measurement only).

Self-contained Kaggle script (built from experiments/exp-006/kernel_template.py by make_kernel.py).
- pip-installs kickmix==1.0.0, finds the competition data under /kaggle/input.
- Finds the attached heliosli/qcc-circuits-live files (dfthcsos__*.kmb / .npz) under /kaggle/input.
  They are untrusted DATA: only hashed, copied, and read by kickmix / numpy(allow_pickle=False)
  inside the official verifier. Nothing from the dataset is imported or executed; no .py,
  .xz or dqi/invsqrt member is touched.
- Identifies each file set by SHA-256 against EXPECTED (our local downloads, exp-006), stages it as
  <stage>/angle_k_<k>.kmb + submission.npz, and runs the UNMODIFIED official verifier as
  `python -I dfthcsos/verify.py <stage>` (cwd = competition verifiers/, default seed, no salt).
- Also records per-circuit width / static Toffoli via kickmix.
It calls no Kaggle API and never submits.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

KICKMIX_PIN = "kickmix==1.0.0"
subprocess.run([sys.executable, "-m", "pip", "install", "-q", KICKMIX_PIN], check=True)

import psutil  # noqa: E402

EXPECTED = json.loads(r"""__EXPECTED_JSON__""")
OUT = Path("/kaggle/working/exp006")
POLL_S = 0.5


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def find_data_root() -> Path:
    marker = Path("verifiers") / "dfthcsos" / "verify.py"
    for dirpath, dirnames, _ in os.walk("/kaggle/input"):
        if (Path(dirpath) / marker).is_file():
            return Path(dirpath)
        if dirpath.count(os.sep) > 6:
            dirnames[:] = []
    raise FileNotFoundError("competition data not found under /kaggle/input")


def find_release_dirs() -> list[Path]:
    hits = []
    for dirpath, dirnames, filenames in os.walk("/kaggle/input"):
        if "dfthcsos__submission.npz" in filenames:
            hits.append(Path(dirpath))
        if dirpath.count(os.sep) > 8:
            dirnames[:] = []
    return hits


def machine_info() -> dict:
    from importlib.metadata import version
    info = {
        "platform": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "total_mem_bytes": psutil.virtual_memory().total,
        "kickmix_dist_version": version("kickmix"),
        "numpy": version("numpy"),
        "scipy": version("scipy"),
    }
    for cg in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/cpu.max"):
        if Path(cg).is_file():
            info[cg] = Path(cg).read_text().strip()
    return info


def run_verify(label: str, verifiers: Path, stage: Path) -> dict:
    cmd = [sys.executable, "-I", "dfthcsos/verify.py", str(stage)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    stdout_p, stderr_p = OUT / f"verify_{label}.stdout.json", OUT / f"verify_{label}.stderr.txt"
    peak = {"rss": 0}
    t0 = time.time()
    with open(stdout_p, "wb") as fo, open(stderr_p, "wb") as fe:
        proc = subprocess.Popen(cmd, cwd=str(verifiers), env=env, stdout=fo, stderr=fe)
        ps = psutil.Process(proc.pid)

        def poll():
            while proc.poll() is None:
                try:
                    peak["rss"] = max(peak["rss"], ps.memory_info().rss)
                except psutil.Error:
                    pass
                time.sleep(POLL_S)

        th = threading.Thread(target=poll, daemon=True)
        th.start()
        rc = proc.wait()
        th.join()
    wall = time.time() - t0
    return {"label": label, "cmd": cmd, "cwd": str(verifiers), "returncode": rc,
            "wall_s": round(wall, 2), "peak_rss_bytes": peak["rss"]}


def static_inspect(stage: Path) -> list[dict]:
    import kickmix as km
    rows = []
    k = 0
    while (stage / f"angle_k_{k}.kmb").is_file():
        c = km.Circuit.from_file(str(stage / f"angle_k_{k}.kmb"), format="kmb")
        st = c.operation_statistics()
        rows.append({"k": k, "num_qubits": int(c.num_qubits),
                     "static_toffoli_like": int(st.num_toffoli_like),
                     "num_instructions": int(st.num_instructions)})
        k += 1
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = find_data_root()
    verifiers = data / "verifiers"
    report = {"machine": machine_info(), "data_root": str(data),
              "verify_py_sha256": sha256_file(verifiers / "dfthcsos" / "verify.py"), "runs": []}
    dirs = find_release_dirs()
    report["release_dirs"] = [str(d) for d in dirs]
    for d in dirs:
        names = {p.name[len("dfthcsos__"):]: p for p in d.iterdir()
                 if p.name.startswith("dfthcsos__") and p.is_file() and not p.is_symlink()}
        got = {n: sha256_file(p) for n, p in names.items()}
        label = next((v for v, exp in EXPECTED.items() if exp == got), None)
        entry = {"dir": str(d), "identified_as": label,
                 "manifest_portfolio": None}
        mf = d / "QCC_RELEASE_MANIFEST.json"
        if mf.is_file():
            entry["manifest_portfolio"] = json.loads(mf.read_text(encoding="utf-8")).get("portfolio")
        if label is None:
            entry["hashes"] = got
            report["runs"].append(entry)
            print("unidentified file set in", d, flush=True)
            continue
        stage = Path("/kaggle/working") / f"stage_{label}" / "dfthcsos"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True)
        for n, p in names.items():
            shutil.copyfile(p, stage / n)
            assert sha256_file(stage / n) == EXPECTED[label][n], n
        entry["static"] = static_inspect(stage)
        print("verifying", label, "from", d, flush=True)
        entry["verify"] = run_verify(label, verifiers, stage)
        print(label, entry["verify"], flush=True)
        shutil.rmtree(stage.parent)
        report["runs"].append(entry)
        (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1)[:4000], flush=True)


if __name__ == "__main__":
    main()

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

EXPECTED = json.loads(r"""{"v10": {"angle_k_0.kmb": "03f6d6be463b19aa0851fa97d2eec424d578413640c2882e47e22d3f06f4a07a", "angle_k_1.kmb": "3356b81d9172196bffbf769fa446d228e6ab92a24625ca5f6ecf4510bc4f48da", "angle_k_10.kmb": "bd98550e656553014cb1a13cae825666c5e68a0e7a384d5965107599f128e0f0", "angle_k_11.kmb": "dd0551f1da64eec6dc73ec7688ea7f8c6418a216b8a9125eea486a2cf939ffd2", "angle_k_12.kmb": "c34e9459efe42c4b3679d4e2a66ffd3b6556965fd462f5f2675772cd529a26f3", "angle_k_13.kmb": "3e9a4e1b764043e22f3587675d2b578aca04df75425b3a66615e1a1088be600f", "angle_k_14.kmb": "8bf80f72edf85122666c68a6e8af3d0a882003836478bc66418cbc87bac1a135", "angle_k_2.kmb": "d2cf59731f562b29e1063b65ee93aad9e4fd7fe9f8517d2157b9280a72833ab5", "angle_k_3.kmb": "c8cff0c10aafdf1a4571debdd2535a9231a90528a61a4900d6a7e5204ed941fc", "angle_k_4.kmb": "1f949ad54757dfaafb6bfdac99894bffd0410d924b0e454d1aec3d894dd5afbd", "angle_k_5.kmb": "84655d0b97912178da383df083a3424c3822f23e590abc95dcaaea0e998c2e79", "angle_k_6.kmb": "27875555d228d50e3681676b63d84d638750afb4245f23a71b67d2f6a2cff1c5", "angle_k_7.kmb": "49e43cd23195ec70278ca2d0e618c585b8a49189d4584ee59bd0a793a720f4fb", "angle_k_8.kmb": "0e49460864fbb5270b8755d98e3d5af14b1b94d35d183dc842d1953253cfe845", "angle_k_9.kmb": "20b1d32646f1965669ddd5c310779d7a0b23cfdf6276fdb5a415a75359c7fc09", "submission.npz": "3249dbf46ee61ddd4a6f180a5058b0420a5bbf1b744eb7b5738358c638a950b7"}, "v11": {"angle_k_0.kmb": "114a2acb164b6538af6fac7784d97ce4bca52cd59878b9ae597889f230888f71", "angle_k_1.kmb": "a01248289fe2a488a39491455089b16bd41b8bff1e86b6dce6be5e85c5019385", "angle_k_10.kmb": "708409dc540b0726438b94854f959a2b6641de6b1aa9b0840beaffe3862f6ba2", "angle_k_11.kmb": "78c041703bbc43f795ae4ab9224a15e2a6dc97d60c76cf9927226de6c959a466", "angle_k_12.kmb": "8375a66c80b83e4a4ac697112769fbba126d6f58fc58e7591aba01fb864bd269", "angle_k_13.kmb": "fbdac0002c7cd3e66487f966ccac1edf2ac40f628fb7d22af048c1ce66f60219", "angle_k_14.kmb": "be4bd2e0e6f63e5c37a232aec0b2a30fd693b4e928605f1d4ade6f4263ffa39c", "angle_k_2.kmb": "b88a234ab24b00c657c4b3b5e8f3f680ac1e41208a64abad08ef4bf87f0d475e", "angle_k_3.kmb": "abf0069e563e4797ed7e3b74d65f932aec131974009f80cb323ae5f5d754fb56", "angle_k_4.kmb": "017d5072da349301a8c0ca5243ffd058528c38531e88728f6735b29f48a65eab", "angle_k_5.kmb": "b4d36019132b43661850f984cf8eb723482cfb0af7eeb4cadb0964b6cc103e2a", "angle_k_6.kmb": "d30c71fb6a288e946f688829f56b6c7026418337441e87a0a2bb5c7bb4fab794", "angle_k_7.kmb": "dead802918d2183ecb2d3c96d6ea1df5ba7e5240d3a20cf63dbfc8fa146bb05f", "angle_k_8.kmb": "ea2d9ab05bd9c61d8e4f2a21ba20c188e08b0db614c222aafa1af0d948f93f18", "angle_k_9.kmb": "663497ad211daa8803a60e1cfff5d4e760499f971054c2908fe3a59489aa597c", "submission.npz": "aef36d39b83bbbf696e909884218f6c02f067baef14a29de1c41306bc1f6395b"}}""")
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

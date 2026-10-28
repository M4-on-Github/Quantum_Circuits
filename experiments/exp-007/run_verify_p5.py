"""exp-007: run the unmodified dfthcsos verify.py locally on a staged build, default seed.

Usage (repo root): .venv/Scripts/python.exe -I experiments/exp-007/run_verify_p5.py <label> <abs stage dir>
The verifier itself runs as `python -B -I dfthcsos/verify.py <stage>` with cwd data/verifiers.
Writes logs/verify_<label>_local.stdout.json, .stderr.txt and run_meta_<label>_local.json.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[1]
VERIFIERS = ROOT / "data" / "verifiers"
label, stage = sys.argv[1], Path(sys.argv[2]).resolve()
LOGS = EXP / "logs"
LOGS.mkdir(exist_ok=True)
cmd = [sys.executable, "-B", "-I", "dfthcsos/verify.py", str(stage)]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
t0 = time.time()
with open(LOGS / f"verify_{label}_local.stdout.json", "wb") as out, open(LOGS / f"verify_{label}_local.stderr.txt", "wb") as err:
    proc = subprocess.Popen(cmd, cwd=VERIFIERS, stdout=out, stderr=err, env=env)
    ps = psutil.Process(proc.pid)
    peak = 0
    while proc.poll() is None:
        try:
            tree = [ps] + ps.children(recursive=True)
            peak = max(peak, max(p.memory_info().rss for p in tree))
        except psutil.Error:
            pass
        time.sleep(0.5)
meta = {"label": label, "cmd": cmd, "cwd": str(VERIFIERS), "returncode": proc.returncode,
        "wall_s": round(time.time() - t0, 1), "peak_rss_bytes_max_process": peak, "python": sys.version}
(LOGS / f"run_meta_{label}_local.json").write_text(json.dumps(meta, indent=2))
print(json.dumps(meta, indent=2))

"""exp-002: run the unmodified dfthcsos verify.py on out/submission at default seed.

Usage (repo root): .venv/Scripts/python.exe experiments/exp-002/run_verify.py
Writes logs/verify_stdout.json, logs/verify_stderr.log, logs/run_meta.json.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
VERIFIERS = ROOT / "data" / "verifiers"
SUB = EXP / "out" / "submission"
LOGS = EXP / "logs"
LOGS.mkdir(exist_ok=True)

cmd = [sys.executable, str(VERIFIERS / "dfthcsos" / "verify.py"), str(SUB)]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
t0 = time.time()
with open(LOGS / "verify_stdout.json", "wb") as out, open(LOGS / "verify_stderr.log", "wb") as err:
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
wall = time.time() - t0
meta = {
    "cmd": " ".join(cmd),
    "cwd": str(VERIFIERS),
    "returncode": proc.returncode,
    "wall_s": round(wall, 1),
    "peak_rss_bytes_max_process": peak,
    "python": sys.version,
}
(LOGS / "run_meta.json").write_text(json.dumps(meta, indent=2))
print(json.dumps(meta, indent=2))

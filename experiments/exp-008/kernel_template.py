"""exp-008: regenerate our invsqrt circuit from source on Kaggle, then run the official verifier.

Self-contained private CPU kernel. Steps:
  1. pip install kickmix==1.0.0
  2. write the embedded src/invsqrt package (our generator) to /kaggle/working/src
  3. build the circuit from the embedded config (fit, LP calibration, build, exact pass)
  4. check its canonical .kmb SHA-256 against the local build (__EXPECTED_SHA__)
  5. run the unmodified verifier: python -I -B invsqrt/verify_submission_invsqrt.py <kmb>
     (default 64 shots per x, default salt, no seed; 4 forked workers on Kaggle)
It never calls any Kaggle API and never submits.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

OUT = Path('/kaggle/working/exp008')
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'kickmix==1.0.0'], check=True)
import psutil  # noqa: E402

SOURCES = __SOURCES_JSON__
CONFIG = __CONFIG_JSON__
EXPECTED_SHA = '__EXPECTED_SHA__'
TAG = '__TAG__'


def log(msg):
    line = f'[{time.strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    with open(OUT / 'kernel.log', 'a') as f:
        f.write(line + '\n')


def find_data_root() -> Path:
    marker = Path('verifiers') / 'invsqrt' / 'verify_submission_invsqrt.py'
    for dirpath, dirnames, _ in os.walk('/kaggle/input'):
        if (Path(dirpath) / marker).is_file():
            return Path(dirpath)
        if dirpath.count(os.sep) > 6:
            dirnames[:] = []
    raise FileNotFoundError('competition data not found under /kaggle/input')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def run_monitored(cmd, cwd, stdout_path):
    """Run cmd, sample summed tree RSS and system used memory every 0.5 s."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    t0 = time.time()
    with open(stdout_path, 'w') as fo, open(str(stdout_path) + '.stderr', 'w') as fe:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=fo, stderr=fe, env=env)
        ps = psutil.Process(p.pid)
        peak = {'tree_rss': 0, 'sys_used': 0}
        stop = threading.Event()

        def poll():
            while not stop.is_set():
                try:
                    procs = [ps] + ps.children(recursive=True)
                    rss = sum(q.memory_info().rss for q in procs)
                    peak['tree_rss'] = max(peak['tree_rss'], rss)
                except psutil.Error:
                    pass
                peak['sys_used'] = max(peak['sys_used'], psutil.virtual_memory().used)
                stop.wait(0.5)

        th = threading.Thread(target=poll, daemon=True)
        th.start()
        rc = p.wait()
        stop.set()
        th.join()
    return rc, time.time() - t0, peak


def main():
    info = {'platform': platform.platform(), 'python': sys.version, 'cpu_count': os.cpu_count(),
            'total_mem_bytes': psutil.virtual_memory().total, 'tag': TAG}
    import importlib.metadata as md
    for pkg in ('kickmix', 'numpy', 'scipy'):
        info[pkg] = md.version(pkg)
    log(json.dumps(info))
    src = Path('/kaggle/working/src')
    for rel, text in SOURCES.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    (OUT / 'config.json').write_text(json.dumps(CONFIG, indent=1))
    runner = OUT / 'build_runner.py'
    runner.write_text(
        'import sys\n'
        "sys.path.insert(0, '/kaggle/working/src')\n"
        "if __name__ == '__main__':\n"
        '    from invsqrt import generate\n'
        '    generate.main(sys.argv[1:])\n')
    kmb = OUT / 'invsqrt.kmb'
    t0 = time.time()
    r = subprocess.run([sys.executable, '-I', '-B', str(runner), str(OUT / 'config.json'), str(OUT / 'work'), str(kmb)],
                       capture_output=True, text=True)
    (OUT / 'build.stdout').write_text(r.stdout)
    (OUT / 'build.stderr').write_text(r.stderr)
    log(f'build rc {r.returncode} in {time.time() - t0:.1f}s')
    if r.returncode != 0:
        raise SystemExit('build failed')
    sha_file = sha256_file(kmb)
    import kickmix as km
    import io
    buf = io.BytesIO()
    km.Circuit.from_file(str(kmb), format='kmb').to_file(buf, format='kmb')
    sha_canon = hashlib.sha256(buf.getvalue()).hexdigest()
    log(f'kmb sha256 file {sha_file} canonical {sha_canon} expected {EXPECTED_SHA}')
    if sha_canon != EXPECTED_SHA:
        (OUT / 'SHA_MISMATCH').write_text(sha_canon)
        raise SystemExit('regenerated circuit differs from the local build; not verifying')
    root = find_data_root()
    ver = root / 'verifiers'
    vfile = ver / 'invsqrt' / 'verify_submission_invsqrt.py'
    log(f'verifier {vfile} sha256 {sha256_file(vfile)}')
    cmd = [sys.executable, '-I', '-B', 'invsqrt/verify_submission_invsqrt.py', str(kmb)]
    log('running: ' + ' '.join(cmd) + f' (cwd {ver})')
    rc, wall, peak = run_monitored(cmd, ver, OUT / 'verify_full.json')
    summary = {'rc': rc, 'wall_s': wall, 'peak': peak, 'cmd': cmd, 'cwd': str(ver), 'sha256': sha_canon,
               'verifier_sha256': sha256_file(vfile), 'machine': info}
    (OUT / 'verify_meta.json').write_text(json.dumps(summary, indent=1))
    log(json.dumps(summary))
    log((OUT / 'verify_full.json').read_text())


if __name__ == '__main__':
    main()

"""exp-009: full official invsqrt verify, with a fresh salt, of the exact invsqrt.kmb that goes into S-002.

Self-contained private CPU kernel. Steps:
  1. pip install kickmix==1.0.0
  2. write the embedded invsqrt.kmb (base64 of the local exp-009 build, the zip member) and check its SHA-256
  3. rebuild the circuit from the embedded src/invsqrt (commit 46af961) and config_port.json in an empty work dir,
     and check the rebuild is byte-identical to the embedded file
  4. run the unmodified verifier on the embedded file:
     python -I -B invsqrt/verify_submission_invsqrt.py <kmb> --salt __SALT__
     (default 64 shots per x, no seed; 4 forked workers on Kaggle)
It never calls any Kaggle API and never submits.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

OUT = Path('/kaggle/working/exp009')
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'kickmix==1.0.0'], check=True)
import psutil  # noqa: E402

SOURCES = __SOURCES_JSON__
CONFIG = __CONFIG_JSON__
KMB_B64 = '__KMB_B64__'
EXPECTED_SHA = '__EXPECTED_SHA__'
SALT = '__SALT__'


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


def canonical_sha(path: Path) -> str:
    import kickmix as km
    buf = io.BytesIO()
    km.Circuit.from_file(str(path), format='kmb').to_file(buf, format='kmb')
    return hashlib.sha256(buf.getvalue()).hexdigest()


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
            'total_mem_bytes': psutil.virtual_memory().total}
    import importlib.metadata as md
    for pkg in ('kickmix', 'numpy', 'scipy'):
        info[pkg] = md.version(pkg)
    log(json.dumps(info))

    # 2. the exact file that goes into the zip
    kmb = OUT / 'invsqrt.kmb'
    kmb.write_bytes(base64.b64decode(KMB_B64))
    emb_file_sha, emb_canon_sha = sha256_file(kmb), canonical_sha(kmb)
    log(f'embedded kmb sha256 file {emb_file_sha} canonical {emb_canon_sha} expected {EXPECTED_SHA}')
    if emb_file_sha != EXPECTED_SHA or emb_canon_sha != EXPECTED_SHA:
        (OUT / 'SHA_MISMATCH_EMBEDDED').write_text(emb_file_sha + ' ' + emb_canon_sha)
        raise SystemExit('embedded circuit hash differs; not verifying')

    # 3. independent rebuild from the committed generator
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
    rebuilt = OUT / 'rebuilt.kmb'
    t0 = time.time()
    r = subprocess.run([sys.executable, '-I', '-B', str(runner), str(OUT / 'config.json'), str(OUT / 'work'),
                        str(rebuilt)], capture_output=True, text=True)
    (OUT / 'build.stdout').write_text(r.stdout)
    (OUT / 'build.stderr').write_text(r.stderr)
    build_s = time.time() - t0
    log(f'build rc {r.returncode} in {build_s:.1f}s')
    if r.returncode != 0:
        raise SystemExit('build failed')
    rb_file_sha = sha256_file(rebuilt)
    rebuild_identical = rebuilt.read_bytes() == kmb.read_bytes()
    log(f'rebuilt kmb sha256 {rb_file_sha} byte_identical_to_embedded {rebuild_identical}')
    if not rebuild_identical:
        (OUT / 'REBUILD_MISMATCH').write_text(rb_file_sha)
        raise SystemExit('rebuild differs from the embedded file; not verifying')

    # 4. the official verifier, fresh salt, on the embedded file
    root = find_data_root()
    ver = root / 'verifiers'
    vfile = ver / 'invsqrt' / 'verify_submission_invsqrt.py'
    log(f'verifier {vfile} sha256 {sha256_file(vfile)}')
    cmd = [sys.executable, '-I', '-B', 'invsqrt/verify_submission_invsqrt.py', str(kmb), '--salt', SALT]
    log('running: ' + ' '.join(cmd) + f' (cwd {ver})')
    rc, wall, peak = run_monitored(cmd, ver, OUT / 'verify_full.json')
    summary = {'rc': rc, 'wall_s': wall, 'peak': peak, 'cmd': cmd, 'cwd': str(ver), 'salt': SALT,
               'verified_file_sha256': sha256_file(kmb), 'verified_canonical_sha256': emb_canon_sha,
               'rebuilt_sha256': rb_file_sha, 'rebuild_byte_identical': rebuild_identical, 'build_s': build_s,
               'verifier_sha256': sha256_file(vfile), 'machine': info}
    (OUT / 'verify_meta.json').write_text(json.dumps(summary, indent=1))
    log(json.dumps(summary))
    log((OUT / 'verify_full.json').read_text())


if __name__ == '__main__':
    main()

"""exp-001: run the unmodified official verifiers on the official sample submission.

Self-contained. On Kaggle it pip-installs kickmix==1.0.0 first, finds the competition data under
/kaggle/input, and writes everything to /kaggle/working/exp001/. Locally pass --data-root and --out.

Each verifier runs as a child process exactly as its CLI documents (default arguments only). This
script measures wall time and memory around it and never touches the verifier code or the inputs.
It does not call any Kaggle API and never submits.

Memory measures (sampled every POLL_S seconds, so short spikes can be missed):
  tree_rss_peak_bytes   max over samples of the summed RSS of the child and all its descendants
                        (forked workers share copy-on-write pages, so this can over-count)
  proc_hwm_peak_bytes   max per-process high-water mark seen (Linux VmHWM, Windows peak_wset)
  sys_used_peak_bytes   max of system-wide used memory (psutil.virtual_memory().used)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

ON_KAGGLE = Path('/kaggle/working').is_dir()
POLL_S = 0.5
KICKMIX_PIN = 'kickmix==1.0.0'

if ON_KAGGLE:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', KICKMIX_PIN], check=True)

import psutil  # noqa: E402


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


def proc_hwm(p: psutil.Process) -> int:
    try:
        if sys.platform.startswith('linux'):
            with open(f'/proc/{p.pid}/status') as f:
                for line in f:
                    if line.startswith('VmHWM:'):
                        return int(line.split()[1]) * 1024
            return 0
        mi = p.memory_info()
        return int(getattr(mi, 'peak_wset', 0) or 0)
    except (psutil.Error, OSError):
        return 0


def machine_info() -> dict:
    info = {
        'platform': platform.platform(),
        'python': sys.version,
        'cpu_count': os.cpu_count(),
        'process_cpu_count': getattr(os, 'process_cpu_count', os.cpu_count)(),
        'total_mem_bytes': psutil.virtual_memory().total,
        'on_kaggle': ON_KAGGLE,
    }
    if hasattr(os, 'sched_getaffinity'):
        info['affinity_cpus'] = len(os.sched_getaffinity(0))
    for cg in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes',
               '/sys/fs/cgroup/cpu.max'):
        if Path(cg).is_file():
            info[cg] = Path(cg).read_text().strip()
    try:
        import multiprocessing as mp
        info['mp_start_methods'] = mp.get_all_start_methods()
    except Exception as ex:  # pragma: no cover
        info['mp_start_methods'] = repr(ex)
    try:
        import kickmix
        info['kickmix_dunder_version'] = getattr(kickmix, '__version__', None)
        info['kickmix_file'] = kickmix.__file__
    except Exception as ex:
        info['kickmix_import_error'] = repr(ex)
    try:
        from importlib.metadata import version
        info['kickmix_dist_version'] = version('kickmix')
        info['numpy'] = version('numpy')
        info['scipy'] = version('scipy')
        info['psutil'] = version('psutil')
    except Exception as ex:
        info['version_error'] = repr(ex)
    return info


def task_commands(data: Path) -> dict[str, list[str]]:
    v, s = data / 'verifiers', data / 'sample_submission'
    py = sys.executable
    return {
        'invsqrt': [py, str(v / 'invsqrt' / 'verify_submission_invsqrt.py'), str(s / 'invsqrt.kmb')],
        'invsqrt_rerun': [py, str(v / 'invsqrt' / 'verify_submission_invsqrt.py'), str(s / 'invsqrt.kmb')],
        'dfthcsos': [py, str(v / 'dfthcsos' / 'verify.py'), str(s / 'dfthcsos')],
        'dqi': [py, str(v / 'dqi' / 'verify_submission_dqi.py'), str(s / 'dqi.kmb')],
    }


def run_one(label: str, cmd: list[str], out: Path) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    stdout_path, stderr_path = out / f'{label}.stdout.json', out / f'{label}.stderr.log'
    peaks = {'tree_rss_peak_bytes': 0, 'proc_hwm_peak_bytes': 0, 'sys_used_peak_bytes': 0,
             'max_live_processes': 0, 'samples': 0}
    t0 = time.time()
    with open(stdout_path, 'wb') as fo, open(stderr_path, 'wb') as fe:
        child = subprocess.Popen(cmd, stdout=fo, stderr=fe, env=env, cwd=str(out))
        root = psutil.Process(child.pid)
        stop = threading.Event()

        def poll() -> None:
            while not stop.is_set():
                try:
                    procs = [root] + root.children(recursive=True)
                except psutil.Error:
                    procs = []
                rss = 0
                for p in procs:
                    try:
                        rss += p.memory_info().rss
                    except psutil.Error:
                        pass
                    peaks['proc_hwm_peak_bytes'] = max(peaks['proc_hwm_peak_bytes'], proc_hwm(p))
                peaks['tree_rss_peak_bytes'] = max(peaks['tree_rss_peak_bytes'], rss)
                peaks['sys_used_peak_bytes'] = max(peaks['sys_used_peak_bytes'], psutil.virtual_memory().used)
                peaks['max_live_processes'] = max(peaks['max_live_processes'], len(procs))
                peaks['samples'] += 1
                stop.wait(POLL_S)

        th = threading.Thread(target=poll, daemon=True)
        th.start()
        rc = child.wait()
        stop.set()
        th.join()
    wall = time.time() - t0
    text = stdout_path.read_text(errors='replace')
    try:
        parsed = json.loads(text[text.index('{'):])
    except ValueError:
        parsed = None
    rec = {'label': label, 'cmd': cmd, 'returncode': rc, 'wall_s': round(wall, 1),
           'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)), **peaks,
           'verifier_output': parsed}
    print(json.dumps({k: rec[k] for k in ('label', 'returncode', 'wall_s', 'tree_rss_peak_bytes',
                                           'proc_hwm_peak_bytes')}), flush=True)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-root', type=Path, default=None)
    ap.add_argument('--out', type=Path, default=None)
    ap.add_argument('--tasks', default='dfthcsos,invsqrt,dqi,invsqrt_rerun')
    ap.add_argument('--tag', default='kaggle' if ON_KAGGLE else 'local')
    args = ap.parse_args()

    data = (args.data_root or find_data_root()).resolve()
    out = (args.out or Path('/kaggle/working/exp001')).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tasks = [t for t in args.tasks.split(',') if t]
    cmds = task_commands(data)

    summary = {'tag': args.tag, 'data_root': str(data), 'machine': machine_info(), 'input_sha256': {},
               'runs': []}
    for rel in ['verifiers/invsqrt/verify_submission_invsqrt.py', 'verifiers/dqi/verify_submission_dqi.py',
                'verifiers/dfthcsos/verify.py', 'verifiers/dfthcsos/scoreinfra/circuits.py',
                'verifiers/dfthcsos/scoreinfra/costs_prepare.py', 'verifiers/dfthcsos/scoreinfra/dfthc_math.py',
                'verifiers/dfthcsos/scoreinfra/reference.py', 'sample_submission/invsqrt.kmb',
                'sample_submission/dfthcsos/submission.npz'] + \
               [f'sample_submission/dfthcsos/angle_k_{k}.kmb' for k in range(10)] + \
               (['sample_submission/dqi.kmb'] if 'dqi' in tasks else []):
        p = data / rel
        summary['input_sha256'][rel] = sha256_file(p) if p.is_file() else None
    summary_path = out / f'summary_{args.tag}.json'
    summary_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary['machine'], indent=2), flush=True)

    for label in tasks:
        summary['runs'].append(run_one(label, cmds[label], out))
        summary_path.write_text(json.dumps(summary, indent=2))  # incremental, survives a later crash


if __name__ == '__main__':
    main()

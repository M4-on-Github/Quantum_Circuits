"""exp-009: write kernel/exp009_verify.py and kernel-metadata.json.

Embeds the local invsqrt.kmb (base64), the committed src/invsqrt sources (read from git at COMMIT, not the worktree)
and the config. Usage (repo root):
    python -I -B experiments/exp-009/make_kernel.py
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

# ---- config ---------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
COMMIT = '46af961'
CONFIG = 'experiments/exp-008/config_port.json'
KMB = HERE / 'out' / 'invsqrt.kmb'
EXPECTED_SHA = 'ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917'
SALT = 'exp-009-S-002'
KID = 'rainm4/exp-009-s002-invsqrt-salt-verify'
KDIR = HERE / 'kernel'
# ---------------------------------------------------------------------------


def git_show(path):
    return subprocess.run(['git', '-C', str(REPO), 'show', f'{COMMIT}:{path}'], check=True,
                          capture_output=True).stdout.decode('utf-8')


def main():
    names = subprocess.run(['git', '-C', str(REPO), 'ls-tree', '--name-only', COMMIT, 'src/invsqrt/'], check=True,
                           capture_output=True, text=True).stdout.split()
    sources = {f'invsqrt/{Path(n).name}': git_show(n) for n in sorted(names) if n.endswith('.py')}
    cfg = json.loads(git_show(CONFIG))
    raw = KMB.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA, 'local kmb hash'
    text = (HERE / 'kernel_template.py').read_text(encoding='utf-8')
    text = (text.replace('__SOURCES_JSON__', repr(sources)).replace('__CONFIG_JSON__', repr(cfg))
            .replace('__KMB_B64__', base64.b64encode(raw).decode('ascii'))
            .replace('__EXPECTED_SHA__', EXPECTED_SHA).replace('__SALT__', SALT))
    KDIR.mkdir(parents=True, exist_ok=True)
    (KDIR / 'exp009_verify.py').write_text(text, encoding='utf-8', newline='\n')
    meta = {
        'id': KID,
        'title': KID.split('/', 1)[1],
        'code_file': 'exp009_verify.py',
        'language': 'python',
        'kernel_type': 'script',
        'is_private': True,
        'enable_gpu': False,
        'enable_tpu': False,
        'enable_internet': True,
        'dataset_sources': [],
        'competition_sources': ['google-verifiable-quantum-circuit-compilation'],
        'kernel_sources': [],
        'model_sources': [],
    }
    (KDIR / 'kernel-metadata.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(json.dumps({'kernel': str(KDIR), 'sources': {k: hashlib.sha256(v.encode()).hexdigest()[:12]
                                                       for k, v in sources.items()},
                      'kmb_sha256': EXPECTED_SHA, 'salt': SALT, 'script_bytes': len(text)}, indent=1))


if __name__ == '__main__':
    main()

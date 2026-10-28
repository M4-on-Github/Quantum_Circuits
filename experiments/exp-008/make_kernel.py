"""exp-008: write kernel/<name>/exp008_verify.py (our src/invsqrt embedded) and kernel-metadata.json.

python -I -B make_kernel.py <kernel_dir> <kernel_id> <config.json> <expected_sha256> <tag>
"""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
repo = here.parents[1]
kdir, kid, cfg_path, sha, tag = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5]
sources = {}
for p in sorted((repo / 'src' / 'invsqrt').glob('*.py')):
    sources[f'invsqrt/{p.name}'] = p.read_text(encoding='utf-8')
cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
text = (here / 'kernel_template.py').read_text(encoding='utf-8')
text = text.replace('__SOURCES_JSON__', repr(sources)).replace('__CONFIG_JSON__', repr(cfg))
text = text.replace('__EXPECTED_SHA__', sha).replace('__TAG__', tag)
kdir.mkdir(parents=True, exist_ok=True)
(kdir / 'exp008_verify.py').write_text(text, encoding='utf-8', newline='\n')
meta = {
    'id': kid,
    'title': kid.split('/', 1)[1],
    'code_file': 'exp008_verify.py',
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
(kdir / 'kernel-metadata.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
print('wrote', kdir, 'sources', list(sources))

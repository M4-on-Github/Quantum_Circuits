"""Writes src/dqi/MANIFEST.json: SHA-256 of every ported kit file, checked against the v14 notebook's SOURCE_HASHES.

Usage: python -I -B make_manifest.py <v14.ipynb> <src/dqi>
The notebook is parsed with ast.literal_eval only (nothing in it runs).
"""
import ast, hashlib, json, sys
from pathlib import Path

nb = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
dst = Path(sys.argv[2])
hashes = None
for c in nb['cells']:
    if c.get('cell_type') != 'code':
        continue
    src = c['source'] if isinstance(c['source'], str) else ''.join(c['source'])
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) == 'SOURCE_HASHES':
            hashes = ast.literal_eval(node.value)
prefix = 'blocks/dqi/pro-q2-897/source/'
up = {k[len(prefix):]: v for k, v in hashes.items() if k.startswith(prefix)}
kit = dst / 'pro_q2_897'
files = {}
for p in sorted(kit.rglob('*')):
    if p.is_file():
        rel = p.relative_to(kit).as_posix()
        if '__pycache__' in rel:
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert up.get(rel) == h, (rel, h, up.get(rel))
        files[rel] = h
assert set(files) == set(up), sorted(set(up) ^ set(files))
lic = hashlib.sha256((dst / 'LICENSE').read_bytes()).hexdigest()
assert lic == hashes['LICENSE'], lic
manifest = {
    'upstream': 'Kaggle notebook somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi version 14 '
                '("Quantum Circuits | 22.34 Local GM: 897-Qubit DQI", id 140675727), embedded SOURCES dict, '
                'prefix blocks/dqi/pro-q2-897/source/',
    'upstream_ipynb_sha256': hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
    'upstream_assembled_from_commit': '98286bd634320b11254f9b3c2d83948eb3d18f3c',
    'licence': 'Apache-2.0 (LICENSE, sha256 ' + lic + ')',
    'retrieved': '2026-10-29',
    'stated_output_sha256': 'b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6',
    'kit_dir': 'pro_q2_897',
    'files': files,
}
(dst / 'MANIFEST.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8', newline='\n')
print(len(files), 'files ok; licence ok')

"""Writes exp011_verify.py = exp011_template.py with src/dqi embedded as a base64 zip (deterministic).

Usage: python -I -B make_kernel.py
Members are dqi/<path> for every file under src/dqi except __pycache__, sorted, with fixed metadata.
"""
import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
src = here.parents[2] / 'src' / 'dqi'
buf = io.BytesIO()
members = {}
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(src.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:
            continue
        name = 'dqi/' + p.relative_to(src).as_posix()
        data = p.read_bytes()
        zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        zi.create_system = 3
        zi.external_attr = 0o100644 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, data)
        members[name] = hashlib.sha256(data).hexdigest()
raw = buf.getvalue()
tpl = (here / 'exp011_template.py').read_text(encoding='utf-8')
for key, val in (('__SRC_ZIP_B64__', repr(base64.b64encode(raw).decode('ascii'))),
                 ('__SRC_MEMBERS__', json.dumps(members, indent=1))):
    assert tpl.count(key) == 1, key
    tpl = tpl.replace(key, val)
(here / 'exp011_verify.py').write_text(tpl, encoding='utf-8', newline='\n')
print(json.dumps({'members': len(members), 'zip_bytes': len(raw), 'zip_sha256': hashlib.sha256(raw).hexdigest(),
                  'script_bytes': len(tpl.encode('utf-8'))}))

"""exp-004: package the official sample submission as submission.zip and check it.

Never submits anything. Usage (repo root):
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I experiments/exp-004/package.py
"""
import hashlib
import io
import json
import re
import sys
import time
import zipfile
import zlib
from pathlib import Path

import numpy as np

# ---- config ---------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
SRC = REPO / 'data' / 'sample_submission'
EXP = REPO / 'experiments' / 'exp-004'
ZIP_PATH = EXP / 'submission.zip'
EXTRACT = EXP / 'out' / 'extract'
MANIFEST = EXP / 'manifest.json'
EXP001_HASHES = REPO / 'experiments' / 'exp-001' / 'kaggle_output' / 'exp001' / 'summary_kaggle.json'
COMPRESSION = zipfile.ZIP_DEFLATED
COMPRESSLEVEL = 6
DATE_TIME = (1980, 1, 1, 0, 0, 0)
UNIX_MODE = 0o100644
CHUNK = 1 << 22
# ---------------------------------------------------------------------------


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


def find_hashes(obj):
    """Collect every 'sample_submission/...': sha256 pair anywhere in the exp-001 Kaggle summary."""
    found = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.startswith('sample_submission/') and isinstance(v, str):
                found[k] = v
            else:
                found.update(find_hashes(v))
    elif isinstance(obj, list):
        for v in obj:
            found.update(find_hashes(v))
    return found


def member_list():
    """Archive names in the competition layout: invsqrt, dqi, dfthcsos/angle_k_0..n-1, dfthcsos/submission.npz."""
    inv = sorted(p.name for p in SRC.glob('invsqrt.*'))
    dqi = sorted(p.name for p in SRC.glob('dqi.*'))
    assert inv == ['invsqrt.kmb'] and dqi == ['dqi.kmb'], (inv, dqi)
    chem = [p for p in (SRC / 'dfthcsos').iterdir() if p.is_file()]
    angles = sorted((p for p in chem if re.fullmatch(r'angle_k_\d+\.km[bx]', p.name)),
                    key=lambda p: int(p.stem.split('_')[-1]))
    others = sorted(p.name for p in chem if p not in angles)
    assert others == ['submission.npz'], others
    return inv + dqi + [f'dfthcsos/{p.name}' for p in angles] + ['dfthcsos/submission.npz']


def build(names):
    tmp = ZIP_PATH.with_name(ZIP_PATH.name + '.partial')
    with zipfile.ZipFile(tmp, 'w', compression=COMPRESSION, compresslevel=COMPRESSLEVEL) as z:
        for n in names:
            zi = zipfile.ZipInfo(n, date_time=DATE_TIME)
            zi.compress_type = COMPRESSION
            zi.create_system = 3
            zi.external_attr = UNIX_MODE << 16
            with open(SRC / n, 'rb') as f, z.open(zi, 'w', force_zip64=False) as w:
                for b in iter(lambda: f.read(CHUNK), b''):
                    w.write(b)
    # Windows: a just-written zip can be briefly locked by another process (seen on the exp-004 rerun,
    # WinError 32), so retry the rename.
    for attempt in range(30):
        try:
            tmp.replace(ZIP_PATH)
            return
        except PermissionError:
            if attempt == 29:
                raise
            time.sleep(2)


def check(names, src_hash, exp001):
    out = {'checks': {}, 'members': []}
    c = out['checks']
    with zipfile.ZipFile(ZIP_PATH) as z:
        infos = z.infolist()
        got = [i.filename for i in infos]
        c['member_names_exact'] = got == names
        c['no_directory_entries'] = not any(i.is_dir() for i in infos)
        c['no_duplicates'] = len(got) == len(set(got))
        c['testzip_ok'] = z.testzip() is None
        c['one_invsqrt'] = sum(1 for n in got if re.fullmatch(r'invsqrt\.km[bx]', n)) == 1
        c['one_dqi'] = sum(1 for n in got if re.fullmatch(r'dqi\.km[bx]', n)) == 1
        idx = sorted(int(m.group(1)) for n in got
                     if (m := re.fullmatch(r'dfthcsos/angle_k_(\d+)\.km[bx]', n)))
        c['angle_k_contiguous_from_0'] = idx == list(range(len(idx)))
        c['n_angle_k'] = len(idx)
        c['has_submission_npz'] = 'dfthcsos/submission.npz' in got
        c['no_zip64'] = all(i.file_size < 0xFFFFFFFF and i.compress_size < 0xFFFFFFFF for i in infos)
        all_same_src = all_same_001 = True
        for i in infos:
            h = hashlib.sha256()
            with z.open(i) as r:
                for b in iter(lambda: r.read(CHUNK), b''):
                    h.update(b)
            d = h.hexdigest()
            e001 = exp001.get(f'sample_submission/{i.filename}')
            same_src = d == src_hash[i.filename] and i.file_size == (SRC / i.filename).stat().st_size
            same_001 = d == e001
            all_same_src &= same_src
            all_same_001 &= same_001
            out['members'].append({
                'name': i.filename, 'size': i.file_size, 'compressed_size': i.compress_size,
                'crc32': f'{i.CRC:08x}', 'sha256': d, 'source_sha256': src_hash[i.filename],
                'exp001_kaggle_sha256': e001, 'byte_identical_to_source': same_src,
                'matches_exp001_kaggle': same_001})
        c['all_members_byte_identical_to_source'] = all_same_src
        c['all_members_match_exp001_kaggle_hashes'] = all_same_001
        with z.open('dfthcsos/submission.npz') as r:
            npz_bytes = r.read()
    # kg-751951 checklist item we can check: npz arrays load without pickles, little-endian dtypes
    arrs = {}
    with np.load(io.BytesIO(npz_bytes), allow_pickle=False) as f:
        for k in f.files:
            a = f[k]
            arrs[k] = {'dtype': a.dtype.str, 'shape': list(a.shape),
                       'little_endian_or_na': a.dtype.byteorder in ('<', '=', '|')}
    c['npz_required_keys_present'] = all(k in arrs for k in ('U', 'W', 'H2_I', 'H1_I', 'Hsym_lower', 'tree_edges'))
    c['npz_all_little_endian'] = all(v['little_endian_or_na'] for v in arrs.values())
    out['npz_arrays'] = arrs
    return out


def main():
    t0 = time.time()
    names = member_list()
    src_hash = {n: sha256_file(SRC / n) for n in names}
    exp001 = find_hashes(json.loads(EXP001_HASHES.read_text()))
    build(names)
    res = check(names, src_hash, exp001)
    EXTRACT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(EXTRACT)
    res['checks']['extracted_files_byte_identical_to_source'] = all(
        sha256_file(EXTRACT / n) == src_hash[n] for n in names)
    manifest = {
        'exp': 'exp-004',
        'zip_path': 'experiments/exp-004/submission.zip',
        'zip_sha256': sha256_file(ZIP_PATH),
        'zip_size': ZIP_PATH.stat().st_size,
        'n_members': len(names),
        'source_dir': 'data/sample_submission',
        'zip_params': {'compression': 'ZIP_DEFLATED', 'compresslevel': COMPRESSLEVEL,
                       'date_time': list(DATE_TIME), 'create_system': 3, 'unix_mode': oct(UNIX_MODE),
                       'python': sys.version.split()[0], 'zlib': zlib.ZLIB_RUNTIME_VERSION},
        **res,
        'all_checks_pass': all(v for v in res['checks'].values() if isinstance(v, bool)),
        'runtime_s': round(time.time() - t0, 1),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + '\n')
    print(json.dumps({k: manifest[k] for k in ('zip_sha256', 'zip_size', 'n_members', 'all_checks_pass', 'runtime_s')}))
    print(json.dumps(res['checks'], indent=1))
    return 0 if manifest['all_checks_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())

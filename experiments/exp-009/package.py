"""exp-009: package S-002 = exp-004's sample zip with invsqrt.kmb replaced by our src/invsqrt circuit.

exp-004's package.py logic, layout, member order, compression and ZipInfo metadata, unchanged except:
  - the source of invsqrt.kmb is experiments/exp-009/out/invsqrt.kmb (built from commit 46af961);
  - extra checks: dqi/dfthcsos members equal exp-004's manifest hashes, invsqrt.kmb equals the file the Kaggle
    verifier checked (kaggle_output/exp009/verify_meta.json and verify_full.json circuit_sha256).
Never submits anything. Usage (repo root):
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I -B experiments/exp-009/package.py
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
SAMPLE = REPO / 'data' / 'sample_submission'
EXP = REPO / 'experiments' / 'exp-009'
INVSQRT_SRC = EXP / 'out' / 'invsqrt.kmb'
INVSQRT_EXPECTED = 'ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917'
ZIP_PATH = EXP / 'submission.zip'
EXTRACT = EXP / 'out' / 'extract'
MANIFEST = EXP / 'manifest.json'
EXP004_MANIFEST = REPO / 'experiments' / 'exp-004' / 'manifest.json'
KAGGLE_OUT = EXP / 'kaggle_output' / 'exp009'
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


def source_of(name):
    return INVSQRT_SRC if name == 'invsqrt.kmb' else SAMPLE / name


def member_list():
    """exp-004's archive names: invsqrt, dqi, dfthcsos/angle_k_0..n-1, dfthcsos/submission.npz."""
    inv = sorted(p.name for p in SAMPLE.glob('invsqrt.*'))
    dqi = sorted(p.name for p in SAMPLE.glob('dqi.*'))
    assert inv == ['invsqrt.kmb'] and dqi == ['dqi.kmb'], (inv, dqi)
    chem = [p for p in (SAMPLE / 'dfthcsos').iterdir() if p.is_file()]
    angles = sorted((p for p in chem if re.fullmatch(r'angle_k_\d+\.km[bx]', p.name)),
                    key=lambda p: int(p.stem.split('_')[-1]))
    others = sorted(p.name for p in chem if p not in angles)
    assert others == ['submission.npz'], others
    return inv + dqi + [f'dfthcsos/{p.name}' for p in angles] + ['dfthcsos/submission.npz']


def verified_hashes():
    """SHA-256s of the file the Kaggle verifier checked; None if the kernel output is not downloaded yet."""
    meta, full = KAGGLE_OUT / 'verify_meta.json', KAGGLE_OUT / 'verify_full.json'
    if not (meta.is_file() and full.is_file()):
        return None
    m, v = json.loads(meta.read_text()), json.loads(full.read_text())
    return {'verified_file_sha256': m.get('verified_file_sha256'), 'verifier_circuit_sha256': v.get('circuit_sha256'),
            'verifier_status': v.get('status'), 'salt': m.get('salt')}


def build(names):
    tmp = ZIP_PATH.with_name(ZIP_PATH.name + '.partial')
    with zipfile.ZipFile(tmp, 'w', compression=COMPRESSION, compresslevel=COMPRESSLEVEL) as z:
        for n in names:
            zi = zipfile.ZipInfo(n, date_time=DATE_TIME)
            zi.compress_type = COMPRESSION
            zi.create_system = 3
            zi.external_attr = UNIX_MODE << 16
            with open(source_of(n), 'rb') as f, z.open(zi, 'w', force_zip64=False) as w:
                for b in iter(lambda: f.read(CHUNK), b''):
                    w.write(b)
    for attempt in range(30):  # Windows: a just-written zip can be briefly locked (WinError 32)
        try:
            tmp.replace(ZIP_PATH)
            return
        except PermissionError:
            if attempt == 29:
                raise
            time.sleep(2)


def check(names, src_hash, e004, ver):
    out = {'checks': {}, 'members': []}
    c = out['checks']
    with zipfile.ZipFile(ZIP_PATH) as z:
        infos = z.infolist()
        got = [i.filename for i in infos]
        c['member_names_exact'] = got == names
        c['member_order_equals_exp004'] = got == [m['name'] for m in e004['members']]
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
        e004_hash = {m['name']: m['sha256'] for m in e004['members']}
        all_src = all_sample = True
        inv_ok = False
        for i in infos:
            h = hashlib.sha256()
            with z.open(i) as r:
                for b in iter(lambda: r.read(CHUNK), b''):
                    h.update(b)
            d = h.hexdigest()
            same_src = d == src_hash[i.filename] and i.file_size == source_of(i.filename).stat().st_size
            all_src &= same_src
            rec = {'name': i.filename, 'size': i.file_size, 'compressed_size': i.compress_size,
                   'crc32': f'{i.CRC:08x}', 'sha256': d, 'source': str(source_of(i.filename).relative_to(REPO)
                                                                      ).replace('\\', '/'),
                   'source_sha256': src_hash[i.filename], 'byte_identical_to_source': same_src,
                   'exp004_sha256': e004_hash[i.filename]}
            if i.filename == 'invsqrt.kmb':
                rec['expected_sha256'] = INVSQRT_EXPECTED
                rec['differs_from_exp004_sample_member'] = d != e004_hash[i.filename]
                if ver:
                    rec.update(ver)
                inv_ok = (d == INVSQRT_EXPECTED and ver is not None and ver['verified_file_sha256'] == d
                          and ver['verifier_circuit_sha256'] == d and ver['verifier_status'] == 'PASS')
            else:
                same_sample = d == sha256_file(SAMPLE / i.filename) == e004_hash[i.filename]
                rec['byte_identical_to_sample_and_exp004'] = same_sample
                all_sample &= same_sample
            out['members'].append(rec)
        c['all_members_byte_identical_to_source'] = all_src
        c['dqi_and_dfthcsos_byte_identical_to_sample_and_exp004'] = all_sample
        c['invsqrt_member_is_the_verified_file'] = inv_ok
        with z.open('dfthcsos/submission.npz') as r:
            npz_bytes = r.read()
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
    src_hash = {n: sha256_file(source_of(n)) for n in names}
    e004 = json.loads(EXP004_MANIFEST.read_text())
    ver = verified_hashes()
    build(names)
    res = check(names, src_hash, e004, ver)
    EXTRACT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(EXTRACT)
    res['checks']['extracted_files_byte_identical_to_source'] = all(
        sha256_file(EXTRACT / n) == src_hash[n] for n in names)
    manifest = {
        'exp': 'exp-009',
        'submission': 'S-002',
        'zip_path': 'experiments/exp-009/submission.zip',
        'zip_sha256': sha256_file(ZIP_PATH),
        'zip_size': ZIP_PATH.stat().st_size,
        'n_members': len(names),
        'sources': {'invsqrt.kmb': 'experiments/exp-009/out/invsqrt.kmb (src/invsqrt @ 46af961, '
                                   'experiments/exp-008/config_port.json)',
                    'other members': 'data/sample_submission'},
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

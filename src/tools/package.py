"""Package a competition submission zip from a member map (JSON config), check it, and write a manifest.

Usage (repo root):
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I -B src/tools/package.py <config.json>
        [--zip PATH] [--manifest PATH] [--extract-dir DIR] [--expect-sha256 HEX]

  --zip / --manifest / --extract-dir   override the config's paths (e.g. to rebuild into a scratch directory)
  --expect-sha256                      exit 1 unless the zip's SHA-256 equals HEX

It never submits anything; submission is the submitter agent's job, from approvals/S-NNN.txt.

Config keys (paths relative to the repo root unless absolute):
  exp, submission        recorded in the manifest (submission optional, e.g. "S-002")
  zip_path               output zip (default experiments/<exp>/submission.zip)
  manifest_path          output manifest (default: manifest.json next to the zip)
  extract_dir            optional: extract the zip here and check every file against its source
  members                {archive name: source} where source is a path or {"source": path, "expected_sha256": hex,
                          "verified_by": {"verifier_json": path, "meta_json": path}, "note": str}.
                          A name ending in "/" maps a directory: every file directly inside it becomes
                          <name><file>. Archive order is always the competition layout: invsqrt.km[bx], dqi.km[bx],
                          dfthcsos/angle_k_0..n-1 (numeric), dfthcsos/submission.npz. Any other name is an error.
  compare                optional list of {"manifest": path, "expect_same": [globs], "expect_different": [globs]}:
                          per-member SHA-256 comparison with an earlier package manifest (e.g. exp-004's)
  sources_note           optional free text/object recorded as manifest "sources"
  zip                    optional {"compresslevel": 6}

Fixed zip parameters (exp-004, unchanged in exp-009): ZIP_DEFLATED level 6, ZipInfo date_time 1980-01-01,
create_system 3, mode 0o100644, no directory entries, streamed 4 MiB chunks with force_zip64=False, written to
<zip>.partial and renamed (retried for 60 s: Windows can hold a just-written file, WinError 32). With the same
member order, bytes and Python/zlib build, the zip SHA-256 is reproducible.

Checks (all booleans must hold for all_checks_pass): member names in layout order, no directory entries, no
duplicates, testzip, one invsqrt, one dqi, angle_k contiguous from 0, submission.npz present, no zip64, every
member byte-identical to its source, expected_sha256 where given, verified_by (the member is the file the verifier
checked: verifier circuit_sha256 and meta verified_file_sha256 equal the member hash, status PASS), compare
expectations, npz has U, W, H2_I, H1_I, Hsym_lower, tree_edges loadable without pickles and little-endian, and
(with extract_dir) the extracted files equal their sources.

Where exp-004/package.py and exp-009/package.py diverged, exp-009 wins: per-member source map, member order
compared with exp-004's manifest, a verified-file check on the replaced member. Generalised here: any member can be
overridden, compared or verified, and the comparison manifest is configurable. exp-004's check against hashes
scraped from the exp-001 Kaggle summary is expressed as a "compare" against a manifest instead. Manifests are
written with LF line ends (the copies used write_text, giving CRLF on Windows working trees).
"""
from __future__ import annotations

import argparse
import fnmatch
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

REPO = Path(__file__).resolve().parents[2]
COMPRESSION = zipfile.ZIP_DEFLATED
DATE_TIME = (1980, 1, 1, 0, 0, 0)
UNIX_MODE = 0o100644
CHUNK = 1 << 22
NPZ_KEYS = ('U', 'W', 'H2_I', 'H1_I', 'Hsym_lower', 'tree_edges')
CONFIG_KEYS = {'exp', 'submission', 'zip_path', 'manifest_path', 'extract_dir', 'members', 'compare',
               'sources_note', 'zip'}


def rpath(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else REPO / p


def rel(p) -> str:
    p = rpath(p).resolve()
    try:
        return p.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


def layout_key(name):
    if re.fullmatch(r'invsqrt\.km[bx]', name):
        return (0, 0)
    if re.fullmatch(r'dqi\.km[bx]', name):
        return (1, 0)
    m = re.fullmatch(r'dfthcsos/angle_k_(\d+)\.km[bx]', name)
    if m:
        return (2, int(m.group(1)))
    if name == 'dfthcsos/submission.npz':
        return (3, 0)
    raise ValueError(f'{name}: not a competition submission member')


def expand(members: dict) -> dict:
    """{archive name: spec dict with 'source' Path}, in layout order."""
    out = {}
    for name, spec in members.items():
        spec = {'source': spec} if isinstance(spec, str) else dict(spec)
        src = rpath(spec['source'])
        if name.endswith('/'):
            if not src.is_dir():
                raise ValueError(f'{name}: {src} is not a directory')
            for p in sorted(x for x in src.iterdir() if x.is_file()):
                out[name + p.name] = {'source': p}
        else:
            if not src.is_file():
                raise ValueError(f'{name}: {src} is not a file')
            out[name] = spec | {'source': src}
    names = sorted(out, key=layout_key)
    if len({layout_key(n) for n in names}) != len(names):
        raise ValueError(f'two members occupy one layout slot (e.g. invsqrt.kmb and invsqrt.kmx): {names}')
    return {n: out[n] for n in names}


def build(zip_path: Path, members: dict, level: int):
    tmp = zip_path.with_name(zip_path.name + '.partial')
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(tmp, 'w', compression=COMPRESSION, compresslevel=level) as z:
        for n, spec in members.items():
            zi = zipfile.ZipInfo(n, date_time=DATE_TIME)
            zi.compress_type = COMPRESSION
            zi.create_system = 3
            zi.external_attr = UNIX_MODE << 16
            with open(spec['source'], 'rb') as f, z.open(zi, 'w', force_zip64=False) as w:
                for b in iter(lambda: f.read(CHUNK), b''):
                    w.write(b)
    for attempt in range(30):  # Windows: a just-written zip can be briefly locked (WinError 32)
        try:
            tmp.replace(zip_path)
            return
        except PermissionError:
            if attempt == 29:
                raise
            time.sleep(2)


def verified(spec):
    vb = spec.get('verified_by')
    if not vb:
        return None
    rec = {}
    if 'verifier_json' in vb:
        p = rpath(vb['verifier_json'])
        if p.is_file():
            t = p.read_text(encoding='utf-8')
            v = json.loads(t[t.index('{'):])
            rec |= {'verifier_circuit_sha256': v.get('circuit_sha256'), 'verifier_status': v.get('status')}
    if 'meta_json' in vb:
        p = rpath(vb['meta_json'])
        if p.is_file():
            m = json.loads(p.read_text(encoding='utf-8'))
            rec |= {'verified_file_sha256': m.get('verified_file_sha256'), 'salt': m.get('salt')}
    return rec


def check(zip_path, members, src_hash, compares):
    out = {'checks': {}, 'members': []}
    c = out['checks']
    names = list(members)
    cmp_docs = [(spec, json.loads(rpath(spec['manifest']).read_text(encoding='utf-8'))) for spec in compares]
    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()
        got = [i.filename for i in infos]
        c['member_names_exact'] = got == names
        for spec, doc in cmp_docs:
            c[f"member_order_equals_{doc['exp'].replace('-', '')}"] = got == [m['name'] for m in doc['members']]
        c['no_directory_entries'] = not any(i.is_dir() for i in infos)
        c['no_duplicates'] = len(got) == len(set(got))
        c['testzip_ok'] = z.testzip() is None
        c['one_invsqrt'] = sum(1 for n in got if re.fullmatch(r'invsqrt\.km[bx]', n)) == 1
        c['one_dqi'] = sum(1 for n in got if re.fullmatch(r'dqi\.km[bx]', n)) == 1
        idx = sorted(int(m.group(1)) for n in got if (m := re.fullmatch(r'dfthcsos/angle_k_(\d+)\.km[bx]', n)))
        c['angle_k_contiguous_from_0'] = idx == list(range(len(idx)))
        c['n_angle_k'] = len(idx)
        c['has_submission_npz'] = 'dfthcsos/submission.npz' in got
        c['no_zip64'] = all(i.file_size < 0xFFFFFFFF and i.compress_size < 0xFFFFFFFF for i in infos)
        all_src, exp_ok, ver_ok = True, True, True
        cmp_ok = {doc['exp']: True for _, doc in cmp_docs}
        for i in infos:
            h = hashlib.sha256()
            with z.open(i) as r:
                for b in iter(lambda: r.read(CHUNK), b''):
                    h.update(b)
            d = h.hexdigest()
            spec = members[i.filename]
            same_src = d == src_hash[i.filename] and i.file_size == spec['source'].stat().st_size
            all_src &= same_src
            rec = {'name': i.filename, 'size': i.file_size, 'compressed_size': i.compress_size,
                   'crc32': f'{i.CRC:08x}', 'sha256': d, 'source': rel(spec['source']),
                   'source_sha256': src_hash[i.filename], 'byte_identical_to_source': same_src}
            if 'note' in spec:
                rec['note'] = spec['note']
            if 'expected_sha256' in spec:
                rec['expected_sha256'] = spec['expected_sha256']
                exp_ok &= d == spec['expected_sha256']
            for cs, doc in cmp_docs:
                tag = doc['exp'].replace('-', '')
                other = {m['name']: m['sha256'] for m in doc['members']}.get(i.filename)
                rec[f'{tag}_sha256'] = other
                if any(fnmatch.fnmatchcase(i.filename, g) for g in cs.get('expect_same', [])):
                    rec[f'same_as_{tag}'] = d == other
                    cmp_ok[doc['exp']] &= d == other
                if any(fnmatch.fnmatchcase(i.filename, g) for g in cs.get('expect_different', [])):
                    rec[f'differs_from_{tag}'] = d != other
                    cmp_ok[doc['exp']] &= d != other
            if 'verified_by' in spec:
                v = verified(spec) or {}
                rec |= v
                ver_ok &= (v.get('verifier_status') == 'PASS' and v.get('verifier_circuit_sha256') == d
                           and v.get('verified_file_sha256', d) == d)
            out['members'].append(rec)
        c['all_members_byte_identical_to_source'] = all_src
        if any('expected_sha256' in s for s in members.values()):
            c['members_match_expected_sha256'] = exp_ok
        if any('verified_by' in s for s in members.values()):
            c['verified_members_are_the_verified_files'] = ver_ok
        for e, ok in cmp_ok.items():
            c[f"compare_{e.replace('-', '')}_expectations_hold"] = ok
        npz_bytes = z.read('dfthcsos/submission.npz') if c['has_submission_npz'] else None
    arrs = {}
    if npz_bytes is not None:
        with np.load(io.BytesIO(npz_bytes), allow_pickle=False) as f:
            for k in f.files:
                a = f[k]
                arrs[k] = {'dtype': a.dtype.str, 'shape': list(a.shape),
                           'little_endian_or_na': a.dtype.byteorder in ('<', '=', '|')}
    c['npz_required_keys_present'] = all(k in arrs for k in NPZ_KEYS)
    c['npz_all_little_endian'] = bool(arrs) and all(v['little_endian_or_na'] for v in arrs.values())
    out['npz_arrays'] = arrs
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                 epilog='See the module docstring for the config keys and checks.')
    ap.add_argument('config', help='package config JSON (usually experiments/exp-NNN/package_config.json)')
    ap.add_argument('--zip', help='output zip path (overrides config zip_path)')
    ap.add_argument('--manifest', help='manifest path (overrides config manifest_path)')
    ap.add_argument('--extract-dir', help='extract and check here (overrides config extract_dir)')
    ap.add_argument('--expect-sha256', help='exit 1 unless the zip has this SHA-256')
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    t0 = time.time()
    cfg = json.loads(rpath(a.config).read_text(encoding='utf-8'))
    bad = [k for k in cfg if k not in CONFIG_KEYS and not k.startswith('_')]
    if bad:
        raise ValueError(f'unknown config keys (prefix "_" for comments): {bad}')
    zip_path = rpath(a.zip or cfg.get('zip_path', f"experiments/{cfg['exp']}/submission.zip"))
    manifest_path = rpath(a.manifest or cfg.get('manifest_path', zip_path.with_name('manifest.json')))
    extract = a.extract_dir or cfg.get('extract_dir')
    level = cfg.get('zip', {}).get('compresslevel', 6)
    members = expand(cfg['members'])
    src_hash = {n: sha256_file(s['source']) for n, s in members.items()}
    build(zip_path, members, level)
    res = check(zip_path, members, src_hash, cfg.get('compare', []))
    if extract:
        ex = rpath(extract)
        ex.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(ex)
        res['checks']['extracted_files_byte_identical_to_source'] = all(
            sha256_file(ex / n) == src_hash[n] for n in members)
    manifest = {
        'exp': cfg['exp'],
        **({'submission': cfg['submission']} if 'submission' in cfg else {}),
        'zip_path': rel(zip_path),
        'zip_sha256': sha256_file(zip_path),
        'zip_size': zip_path.stat().st_size,
        'n_members': len(members),
        'sources': cfg.get('sources_note', {n: rel(s['source']) for n, s in members.items()}),
        'zip_params': {'compression': 'ZIP_DEFLATED', 'compresslevel': level, 'date_time': list(DATE_TIME),
                       'create_system': 3, 'unix_mode': oct(UNIX_MODE), 'python': sys.version.split()[0],
                       'zlib': zlib.ZLIB_RUNTIME_VERSION},
        **res,
        'all_checks_pass': all(v for v in res['checks'].values() if isinstance(v, bool)),
        'runtime_s': round(time.time() - t0, 1),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(manifest, indent=1) + '\n')
    summary = {k: manifest[k] for k in ('zip_path', 'zip_sha256', 'zip_size', 'n_members', 'all_checks_pass',
                                        'runtime_s')}
    if a.expect_sha256:
        summary['zip_sha256_as_expected'] = manifest['zip_sha256'] == a.expect_sha256
    print(json.dumps(summary, indent=1))
    print(json.dumps(res['checks'], indent=1))
    ok = manifest['all_checks_pass'] and summary.get('zip_sha256_as_expected', True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

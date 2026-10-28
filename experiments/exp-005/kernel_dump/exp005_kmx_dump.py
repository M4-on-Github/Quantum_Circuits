"""exp-005 follow-up kernel: dump the downloaded dqi circuit as xz-compressed .kmx for local text analysis.

Measurement only. Never calls any Kaggle API and never submits. The downloaded circuit is loaded only
through kickmix (Circuit.from_file); no downloaded code runs. The .kmx is parsed locally as text.
"""
import glob
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_XZ_SHA = '07db71ee28c1d3bfaf2496c92dd7153eb0d01ced3797a8d95502ccf0fa541c33'
EXPECTED_KMB_SHA = '4ee7a17b4cbca4053a19bc951e7f2ef91fabdbb036006c9d658adcff4fe76da4'
OUT = Path('/kaggle/working/exp005dump')
TMP = Path('/tmp/exp005dump')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def peak_rss():
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmHWM:'):
                return int(line.split()[1]) * 1024
    return 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'kickmix==1.0.0'], check=True)
    import kickmix as km
    from importlib.metadata import version
    info = {'kickmix': version('kickmix'), 'python': sys.version}
    hits = [h for h in glob.glob('/kaggle/input/**/QCC_RELEASE_MANIFEST.json', recursive=True)
            if Path(h).with_name('dqi.kmb.xz').is_file()]
    assert len(hits) == 1, hits
    xz = Path(hits[0]).with_name('dqi.kmb.xz')
    info['dataset_dir'] = str(xz.parent)
    info['xz_sha256'] = sha256_file(xz)
    if info['xz_sha256'] != EXPECTED_XZ_SHA:
        (OUT / 'dump.json').write_text(json.dumps(info, indent=1))
        raise SystemExit('dataset dqi.kmb.xz differs from the exp-005 download')
    kmb = TMP / 'dqi.kmb'
    with lzma.open(xz) as fi, open(kmb, 'wb') as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)
    info['kmb_sha256'] = sha256_file(kmb)
    assert info['kmb_sha256'] == EXPECTED_KMB_SHA, info
    t0 = time.time()
    c = km.Circuit.from_file(str(kmb))
    info['num_qubits'] = c.num_qubits
    info['num_toffoli_like'] = c.operation_statistics().num_toffoli_like
    kmx = TMP / 'dqi.kmx'
    c.to_file(str(kmx), format='kmx')
    del c
    info['load_and_kmx_s'] = round(time.time() - t0, 1)
    info['kmx_bytes'] = kmx.stat().st_size
    info['kmx_sha256'] = sha256_file(kmx)
    t1 = time.time()
    with open(kmx, 'rb') as fi, lzma.open(OUT / 'dqi.kmx.xz', 'wb', preset=6) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)
    info['xz_s'] = round(time.time() - t1, 1)
    info['kmx_xz_bytes'] = (OUT / 'dqi.kmx.xz').stat().st_size
    info['kmx_xz_sha256'] = sha256_file(OUT / 'dqi.kmx.xz')
    info['peak_rss_bytes'] = peak_rss()
    (OUT / 'dump.json').write_text(json.dumps(info, indent=1))
    print(json.dumps(info), flush=True)


if __name__ == '__main__':
    main()

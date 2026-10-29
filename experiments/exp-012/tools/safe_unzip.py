"""Extract a downloaded zip after checking every member (no absolute paths, no '..', no symlinks).
Usage: python -I -B safe_unzip.py <zip> <outdir>"""
import hashlib, stat, sys, zipfile
from pathlib import Path, PurePosixPath

zp, out = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(zp) as z:
    for i in z.infolist():
        p = PurePosixPath(i.filename)
        assert not p.is_absolute() and ".." not in p.parts and "\\" not in i.filename, i.filename
        assert not stat.S_ISLNK(i.external_attr >> 16), ("symlink", i.filename)
        print(f"{i.file_size:>10} {i.filename}")
    for i in z.infolist():
        if i.is_dir():
            continue
        data = z.read(i)
        t = out.joinpath(*PurePosixPath(i.filename).parts)
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(data)
        print(hashlib.sha256(data).hexdigest(), i.filename)

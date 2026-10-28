"""Stream-decompress a single .xz file and print SHA-256 and size of the content. Usage: python -I xz_sha.py <file.xz>"""
import hashlib, lzma, sys
h, n = hashlib.sha256(), 0
with lzma.open(sys.argv[1]) as f:
    for chunk in iter(lambda: f.read(1 << 22), b''):
        h.update(chunk); n += len(chunk)
print(h.hexdigest(), n)

# Submission packaging

- `experiments/exp-004/package.py` builds a submission zip with Python `zipfile`, `ZIP_DEFLATED` level 6.
  - Layout: `invsqrt.kmb` and `dqi.kmb` at the root, then `dfthcsos/angle_k_0..n-1.kmb` and `dfthcsos/submission.npz`. No directory entries and no wrapping folder.
  - It then re-reads every member and checks its SHA-256 against the source.
  - This is the competition page layout, and the one public assembly notebooks use.
  - (unverified) That the LB accepts it. This is settled once a submission of it is scored.
- Deflate shrinks the sample a lot (exp-004): `dqi.kmb` goes from 886,118,180 B to 69,819,447 B, and the whole zip is 73,803,082 B. Building and checking takes about 45 s locally.
- Fixed member metadata makes the zip SHA-256 reproducible between runs on the same Python/zlib build (verified for 3.13.12 / zlib 1.3.1, exp-004): `ZipInfo` date_time (1980,1,1,0,0,0), `create_system=3`, mode 0o100644, sorted members.
- Verifier seeds hash member contents (canonical kmb bytes and npz arrays), not the zip bytes, so the packaging doesn't change which tests run.
- `experiments/exp-009/package.py` is the same logic with a per-member source map (invsqrt from an experiment build, the rest from the sample). With the same member order and metadata, the unchanged members get exp-004's compressed sizes and CRCs. Windows `C:/Windows/System32/tar.exe` (bsdtar) lists and inflates these zips (`tar -xOf z.zip member`), a reader independent of Python `zipfile` (exp-009).
- A circuit can be shipped to a kernel inside the script as base64 (exp-009: a 288,783 B `.kmb` gave a 446 KB script; `kaggle kernels push` accepted it and the kernel decoded it to the same SHA-256).
- Windows: `np.load` on an `.npz` keeps the file open until the `NpzFile` is closed, so a `tempfile.TemporaryDirectory` holding it fails to clean up with WinError 32. Use `with np.load(p) as z: d = {k: z[k] for k in z.files}` (exp-005).
- Windows: renaming a just-written zip can fail with `PermissionError` WinError 32 because something else briefly holds the file. Retry the rename (exp-004).
- dfthcsos `verify.py` accepts a folder extracted from the zip (`verify.py <extract>/dfthcsos`). Its output was bit-identical to exp-001 local: 512 s wall against 356 s in exp-001. Machine load is unknown: exp-002 and exp-003 were running at the same time.

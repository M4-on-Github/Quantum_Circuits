# Kaggle CLI and kernels: verified behaviour

Details behind the defaults in `SKILL.md` (Kaggle notebooks).

- Verified working (exp-001, kernel `rainm4/exp-001-verify-sample-submission` v1, 2026-10-28): the defaults above with Kaggle CLI 2.2.5 and `kaggle kernels push -p <dir>`. `kaggle kernels status <slug>` reports `KernelWorkerStatus.RUNNING` / `COMPLETE`. `kaggle kernels output <slug> -p <dir>` downloads `/kaggle/working` contents plus `<slug>.log`. The server renames `code_file` to `<slug>.py` and adds `docker_image` and `machine_shape: "None"` (see `kaggle kernels pull <slug> -m`).
- The Kaggle CLI is the miniconda one on PATH (`kaggle`, at `/c/Users/moemy/miniconda3/Scripts/kaggle`). It is not in `.venv` (exp-003).
- Auth: the CLI authenticates with `KAGGLE_API_TOKEN`. It is set at Windows user scope, but the Bash tool's shell may not inherit it. Load it without printing: `export KAGGLE_API_TOKEN="$(powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('KAGGLE_API_TOKEN','User')" | tr -d '\r\n')"`.
- Kaggle CPU kernel machine (exp-001): Python 3.13.15, 4 CPUs (`cpu.max` 400000/100000), cgroup `memory.max` 32212254720 B (30 GiB), `fork` available, numpy 2.1.3, scipy 1.16.3, psutil 5.9.5 preinstalled. `pip install kickmix==1.0.0` works with internet on.
- Competition data mounts at `/kaggle/input/competitions/google-verifiable-quantum-circuit-compilation/` (same layout as the zip: `verifiers/`, `sample_submission/`, ...), not `/kaggle/input/<slug>/`. Search for a marker file instead of hard-coding the path. The files there are byte-identical (SHA-256) to the local `data/` copy.
- Pass absolute paths when a runner starts a verifier with a different `cwd`. Relative paths then resolve against the child's cwd and fail.
- Kaggle datasets (CLI 2.2.5, exp-006): a specific version is addressed as `owner/slug/N` for `kaggle datasets files owner/slug/N` and `kaggle datasets download owner/slug/N -f <file>`. `owner/slug/versions/N` is rejected as invalid. `kaggle datasets status` returns not-found for other users' datasets. `datasets files` takes `--format`, not `-o`.
- Finding which version an unversioned download was (exp-005 fix, 2026-10-28): `kaggle datasets files owner/slug/N --format csv --page-size 200` works on other users' datasets and lists each file's size and creationDate for that version. The default page size is 20, and `--page-size` goes up to 200. Match the creationDates and sizes recorded at download time against each N.
- Kernel `dataset_sources` version pins do not work: `"owner/slug/N"` is accepted by `kaggle kernels push`, but the server strips the version (see `kaggle kernels pull -m`) and mounts the latest version. Identify attached files by SHA-256 inside the kernel (exp-006).
- Attached datasets mount at `/kaggle/input/datasets/<owner>/<slug>/` (exp-006).
- More Kaggle CLI 2.2.5 behaviour (exp-008):
  - `kaggle datasets files owner/slug/N --format csv --page-size 200` prints `Next Page Token = ...` when more files exist. Pass `--page-token <tok>` for the next page (mrmeows/qcc-1375-open-circuits v8 lists 2,704 files, including members of its zips).
  - `kaggle datasets download owner/slug/N -f dir/file -p D` writes to `D/dir/file`, keeping the file's directory path.
  - `kaggle kernels files <owner/slug>` lists a kernel's output files, but its `size` column is not the file size (every entry shows 870 to 970).
  - `kaggle kernels pull <slug> -p D -m` writes the code file and `kernel-metadata.json`, with no version number.
- More Kaggle CLI 2.2.5 behaviour (exp-011):
  - `kaggle kernels pull owner/slug/N -p D` fetches version N of another user's notebook. The file is named after the notebook's *current* slug, whatever the version. A version that doesn't exist fails with "To search for one, try 'kaggle search <query>'". This found the SomeJoint v14 generator after its old slug stopped resolving.
  - `kaggle kernels list --competition google-verifiable-quantum-circuit-compilation --sort-by dateRun --page-size 100 --page N` lists the competition's public notebooks. A bare `-s <term>` search returns mostly unrelated Kaggle notebooks.
- GitHub: `gh` is not authenticated on this machine. Anonymous `curl https://api.github.com/repos/<owner>/<repo>` works for public metadata, including the `license` field (exp-011).


"""exp-006: build kernel/<name>/exp006_verify.py and kernel-metadata.json from the template.

python -I make_kernel.py <kernel_dir> <kernel_id> <dataset_source>
The expected SHA-256 table comes from kernel_expected_hashes.json (our local downloads).
"""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
kdir, kid, source = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
expected = json.loads((here / "kernel_expected_hashes.json").read_text(encoding="utf-8"))
text = (here / "kernel_template.py").read_text(encoding="utf-8")
text = text.replace("__EXPECTED_JSON__", json.dumps(expected, sort_keys=True))
kdir.mkdir(parents=True, exist_ok=True)
(kdir / "exp006_verify.py").write_text(text, encoding="utf-8", newline="\n")
meta = {
    "id": kid,
    "title": kid.split("/", 1)[1],
    "code_file": "exp006_verify.py",
    "language": "python",
    "kernel_type": "script",
    "is_private": True,
    "enable_gpu": False,
    "enable_tpu": False,
    "enable_internet": True,
    "dataset_sources": [source],
    "competition_sources": ["google-verifiable-quantum-circuit-compilation"],
    "kernel_sources": [],
    "model_sources": [],
}
(kdir / "kernel-metadata.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("wrote", kdir)

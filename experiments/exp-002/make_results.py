"""exp-002: assemble results.json from the verifier output and the build report."""
import json
import subprocess
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[1]
v = json.loads((EXP / "logs" / "verify_stdout.json").read_text())
meta = json.loads((EXP / "logs" / "run_meta.json").read_text())
build = json.loads((EXP / "logs" / "build_report.json").read_text())
base_local = json.loads((ROOT / "experiments/exp-001/logs/local/dfthcsos.stdout.json").read_text())
base_kaggle = json.loads((ROOT / "experiments/exp-001/kaggle_output/exp001/dfthcsos.stdout.json").read_text())
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()

BASE_COST = 3355599588.3155375  # exp-001 Kaggle
cost = v["score"]
m = v["metrics"]
r = v["resources"]
identical_fields = sorted(k for k in base_local if base_local[k] == v.get(k))
differing_fields = sorted(k for k in set(base_local) | set(v) if base_local.get(k) != v.get(k))
res = {
    "exp": "exp-002",
    "commit": commit,
    "task": "dfthcsos",
    "verifier": "dfthcsos/verify.py",
    "verifier_cmd": f"(cwd {meta['cwd']}) PYTHONDONTWRITEBYTECODE=1 {meta['cmd']}",
    "platform": "local Windows 11 .venv, Python 3.13, kickmix 1.0.0, numpy 2.5.4, scipy 1.18.1",
    "passed": v["status"] == "PASS",
    "metrics": {
        "Q": v["num_qubits"],
        "toffoli": v["toffoli_count"],
        "t_gates": None,
        "cost": cost,
        "lambda_eff": v["lambda_eff"],
        "Lambda": m["Lambda"],
        "E_gap": m["E_gap"],
        "ham_error_mHa": {"error_1": m["error_1"] * 1e3, "error_2": m["error_2"] * 1e3},
        "max_width": r["angles_qubits"],
        "n_circuits": v["num_circuits"],
        "brot": v["brot"],
        "J": v["batch_size"],
        "angles_toffoli": r["angles_toffoli"],
        "heuristic_toffoli": r["heuristic_toffoli"],
        "submission_sha256": v["submission_sha256"],
        "verified_shots": v["verified_shots"],
    },
    "per_circuit": [
        {k: c[k] for k in ("k", "file", "num_qubits", "toffoli_static", "num_instructions", "sha256",
                           "sample_sha256", "bit_identical")}
        for c in build["circuits"]
    ],
    "all_bit_identical_to_sample": build["all_bit_identical"],
    "submission_npz_identical_to_sample": build["submission_npz_identical"],
    "generator_build_seconds": build["build_seconds"],
    "baseline": {"exp": "exp-001", "cost": BASE_COST, "cost_local": base_local["score"],
                 "submission_sha256": base_local["submission_sha256"]},
    "verifier_output_equal_to_exp001_local": {"identical_top_level_fields": identical_fields,
                                               "differing_top_level_fields": differing_fields},
    "rel_diff_vs_baseline_kaggle": (cost - BASE_COST) / BASE_COST,
    "rel_diff_vs_baseline_local": (cost - base_local["score"]) / base_local["score"],
    "improvement_factor": BASE_COST / cost,
    "score_delta_factor": (BASE_COST / cost) ** (1 / 3),
    "runtime_s": meta["wall_s"],
    "peak_rss_bytes": meta["peak_rss_bytes_max_process"],
    "salts_or_seeds": ["default (no --salt, no --seed): seed from submission_sha256"],
}
(EXP / "results.json").write_text(json.dumps(res, indent=2))
print(json.dumps({k: res[k] for k in ("passed", "rel_diff_vs_baseline_kaggle", "rel_diff_vs_baseline_local",
                                       "verifier_output_equal_to_exp001_local", "runtime_s", "peak_rss_bytes")}, indent=2))

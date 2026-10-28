"""exp-007: assemble results.json from the verifier output and probe/build/analysis JSONs."""

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
v = json.loads((HERE / "logs" / "verify_p5_local.stdout.json").read_text())
meta = json.loads((HERE / "logs" / "run_meta_p5_local.json").read_text())
probes = json.loads((HERE / "probes_result.json").read_text())
build = json.loads((HERE / "p5_build.json").read_text())
analysis = json.loads((HERE / "analysis.json").read_text())
BASE_COST = 3355599588.3155365  # exp-002 / SCORING_README reference score
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                        cwd=HERE).stdout.strip()
r, m = v["resources"], v["metrics"]
imp = BASE_COST / v["score"]
out = {
    "exp": "exp-007",
    "commit": commit,
    "task": "dfthcsos",
    "verifier": "data/verifiers/dfthcsos/verify.py",
    "verifier_cmd": "cd data/verifiers && python -B -I dfthcsos/verify.py <abs>/experiments/exp-007/out/p5",
    "passed": v["status"] == "PASS",
    "metrics": {
        "Q": v["num_qubits"], "toffoli": v["toffoli_count"], "cost": v["score"],
        "angles_toffoli": r["angles_toffoli"], "angles_toffoli_per_pass": r["angles_toffoli_per_pass"],
        "angles_static_both_passes": build["static_both_passes"],
        "lambda_eff": v["lambda_eff"], "Lambda": m["Lambda"], "E_gap": m["E_gap"],
        "ham_error_mHa": {"error_1": 1e3 * m["error_1"], "error_2": 1e3 * m["error_2"]},
        "max_width": r["angles_qubits"], "n_circuits": v["num_circuits"],
        "submission_sha256": v["submission_sha256"], "verified_shots": v["verified_shots"],
    },
    "baseline": {"exp": "exp-002", "cost": BASE_COST, "toffoli": 93237, "Q": 730, "angles_toffoli": 79480},
    "improvement_factor": imp,
    "score_delta_factor": imp ** (1 / 3),
    "note": "P5 is a legality probe (MBU section added to the reference); it is not meant to improve cost.",
    "runtime_s": meta["wall_s"],
    "peak_rss_bytes": meta["peak_rss_bytes_max_process"],
    "salts_or_seeds": ["default (empty salt) for P5", "seeds 0 and 12345 for P1-P3, 0 for P4"],
    "probes": probes,
    "p5_build": {k: build[k] for k in build if k != "files"},
    "analysis_best_feasible": analysis["best_feasible"],
    "analysis_J4_lambda2": next(x for x in analysis["layouts"] if x["J"] == 4 and x["lambda"] == 2),
    "analysis_hypothetical": analysis["hypothetical_direction_specific_reverse"],
}
(HERE / "results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("passed", "metrics", "improvement_factor", "score_delta_factor")}, indent=2))

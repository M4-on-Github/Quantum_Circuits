"""exp-006: assemble results.json from verifier outputs and inspection logs only.

python -I make_results.py <commit>
"""
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
L = EXP / "logs"
BASELINE_COST = 3355599588.3155365  # exp-002 (local), equal to exp-001 local
BASELINE_ANGLE, BASELINE_T = 79480.0, 93237.0


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def build(label, verify, meta, inspect, xor, platform):
    r, m = verify["resources"], verify["metrics"]
    T = verify["toffoli_count"]
    per = []
    xk = {row["k"]: row for row in xor["per_circuit"]}
    for c in inspect["per_circuit"]:
        x = xk[c["k"]]
        per.append({
            "k": c["k"], "width": c["num_qubits"], "spare_under_128": c["spare_under_128"],
            "workspace_qubits": c["workspace_qubits"], "static_toffoli": c["static_toffoli_like"],
            "ccx": c["op_counts"].get("CCX", 0), "hmr": c["op_counts"].get("HMR", 0),
            "mean_toffoli_per_shot_sim": x["zero"]["mean_toffoli_per_shot"],
            "fail_frac_sign_canonical_words": x["sign"]["fail_frac"],
            "fail_frac_random_words": x["random"]["fail_frac"],
        })
    return {
        "label": label, "portfolio": inspect["portfolio"], "platform": platform,
        "verifier_cmd": meta.get("cmd"), "passed": verify["status"] == "PASS",
        "runtime_s": meta.get("wall_s"), "peak_rss_bytes": meta.get("peak_rss_bytes", meta.get("peak_rss_bytes_max_process")),
        "submission_sha256": verify["submission_sha256"], "verified_shots": verify["verified_shots"],
        "metrics": {
            "cost": verify["score"], "Q": verify["num_qubits"], "toffoli": T,
            "lambda_eff": verify["lambda_eff"], "Lambda": m["Lambda"], "E_gap": m["E_gap"],
            "ham_error_mHa": {"error_1": 1e3 * m["error_1"], "error_2": 1e3 * m["error_2"]},
            "max_width": r["angles_qubits"], "n_circuits": verify["num_circuits"],
            "brot": verify["brot"], "J": verify["batch_size"],
            "R_B_C": [inspect["R"], inspect["B"], inspect["C"]],
        },
        "T_split": {
            "angles": r["angles_toffoli"], "angles_per_pass": r["angles_toffoli_per_pass"],
            "inner_state_prep": r["inner_state_prep_toffoli"], "outer_state_prep": r["outer_state_prep_toffoli"],
            "givens": r["givens_rotations_toffoli"], "heuristic": r["heuristic_toffoli"],
            "angle_share": r["angles_toffoli"] / T,
            "static_angle_sum_both_passes": inspect["static_toffoli_both_passes"],
        },
        "Q_split": {
            "outer_persistent": r["outer_state_prep_persistent_qubits"],
            "inner_persistent": r["inner_state_prep_persistent_qubits"],
            "angle_words_J_brot": r["angles_persistent_qubits"],
            "persistent": r["persistent_qubits"],
            "temp_outer": r["outer_state_prep_temporary_qubits"], "temp_inner": r["inner_state_prep_temporary_qubits"],
            "temp_angles": r["angles_temporary_qubits"], "temporary_max": r["temporary_qubits"],
            "selection": r["angles_selection_qubits"],
        },
        "improvement_factor_vs_reference": BASELINE_COST / verify["score"],
        "per_circuit": per,
    }


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    v10 = build("v10", load(L / "verify_v10_local.stdout.json"), load(L / "run_meta_v10_local.json"),
                load(L / "inspect_local_v10.json"), load(L / "xor_check_v10.json"), "local Windows .venv")
    krep = load(EXP / "kaggle_output/v11/exp006/report.json")
    kmeta = krep["runs"][0]["verify"]
    v11 = build("v11", load(EXP / "kaggle_output/v11/exp006/verify_v11.stdout.json"), kmeta,
                load(L / "inspect_local_v11.json"), load(L / "xor_check_v11.json"), "Kaggle CPU kernel")
    share = v10["T_split"]["angle_share"]
    out = {
        "exp": "exp-006", "commit": commit, "task": "dfthcsos", "verifier": "dfthcsos/verify.py",
        "verifier_cmd": "(cwd data/verifiers) PYTHONDONTWRITEBYTECODE=1 python -I dfthcsos/verify.py <abs stage dir>",
        "target": "heliosli/qcc-circuits-live v10 (portfolio v15b_sjmixL), the 430Q R8/B143/C62 build",
        "passed": v10["passed"],
        "metrics": v10["metrics"],
        "baseline": {"exp": "exp-002", "cost": BASELINE_COST, "angle_toffoli": BASELINE_ANGLE,
                     "toffoli": BASELINE_T, "angle_share": BASELINE_ANGLE / BASELINE_T},
        "C011_angle_share": share, "C011_threshold": 0.5, "C011_holds": share >= 0.5,
        "improvement_factor": v10["improvement_factor_vs_reference"],
        "score_delta_factor": v10["improvement_factor_vs_reference"] ** (1 / 3),
        "score_delta_note": "measurement of a public artifact; not our circuit, not submittable",
        "runtime_s": v10["runtime_s"], "salts_or_seeds": ["default (empty salt, no seed)"],
        "builds": {"v10": v10, "v11_secondary": v11},
    }
    (EXP / "results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for b in (v10, v11):
        print(b["label"], b["metrics"]["cost"], b["metrics"]["toffoli"], b["metrics"]["Q"],
              round(b["T_split"]["angle_share"], 4), b["metrics"]["lambda_eff"])


if __name__ == "__main__":
    main()

"""exp-004: assemble results.json from manifest.json and the dfthcsos verifier output on the zip-extracted folder.

Usage (repo root): .venv/Scripts/python.exe -I experiments/exp-004/make_results.py <commit>
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = REPO / 'experiments' / 'exp-004'
LOGS = EXP / 'logs'
E001 = REPO / 'experiments' / 'exp-001'


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    man = json.loads((EXP / 'manifest.json').read_text())
    ver = json.loads((LOGS / 'dfthcsos_from_zip.stdout.json').read_text())
    base = json.loads((E001 / 'logs' / 'local' / 'dfthcsos.stdout.json').read_text())
    e001 = json.loads((E001 / 'results.json').read_text())['tasks']
    exit_line = (LOGS / 'dfthcsos_from_zip.exit').read_text().split()
    m = ver['metrics']
    same_keys = ('status', 'score', 'lambda_eff', 'toffoli_count', 'num_qubits', 'num_circuits',
                 'verified_shots', 'submission_sha256', 'resources', 'metrics')
    identical = {k: ver.get(k) == base.get(k) for k in same_keys}
    res = {
        'exp': 'exp-004',
        'commit': commit,
        'task': 'all',
        'verifier': 'verify.py (dfthcsos only; invsqrt and dqi members byte-identical to exp-001 inputs, not re-run)',
        'verifier_cmd': '.venv/Scripts/python.exe <repo>/data/verifiers/dfthcsos/verify.py '
                        '<repo>/experiments/exp-004/out/extract/dfthcsos',
        'passed': ver['status'] == 'PASS' and man['all_checks_pass'],
        'packaging': {
            'zip_path': man['zip_path'],
            'zip_sha256': man['zip_sha256'],
            'zip_size': man['zip_size'],
            'n_members': man['n_members'],
            'zip_params': man['zip_params'],
            'checks': man['checks'],
            'reproducible_rebuild_same_sha256': True,
            'members': [{k: x[k] for k in ('name', 'size', 'compressed_size', 'sha256')} for x in man['members']],
        },
        'metrics': {
            'dfthcsos': {
                'status': ver['status'],
                'Q': ver['num_qubits'],
                'toffoli': ver['toffoli_count'],
                'cost': ver['score'],
                'lambda_eff': ver['lambda_eff'],
                'Lambda': m['Lambda'],
                'E_gap': m['E_gap'],
                'error_1': m['error_1'],
                'error_2': m['error_2'],
                'max_width': ver['resources']['angles_qubits'],
                'n_circuits': ver['num_circuits'],
                'verified_shots': ver['verified_shots'],
                'submission_sha256': ver['submission_sha256'],
                'wall_s': float(exit_line[3]) if len(exit_line) > 3 else None,
                'returncode': int(exit_line[1]),
            },
            'invsqrt_cost_from_exp001': e001['invsqrt']['metrics']['cost'],
            'dqi_cost_from_exp001': e001['dqi']['metrics']['cost'],
        },
        'dfthcsos_identical_to_exp001_local': identical,
        'baseline': {'exp': 'exp-001', 'dfthcsos_cost_local': base['score'],
                     'local_three_task_score_vs_C001_refs': 1.000042972609377},
        'improvement_factor': base['score'] / ver['score'],
        'score_delta_factor': (base['score'] / ver['score']) ** (1 / 3),
        'lb_prediction': {
            'if_C001_holds': 1.00004,
            'refuted_if_outside': [0.999, 1.001],
            'alt_half_shot_dqi_eps': 0.97498,
            'alt_brief_unsourced': 1.015,
            'measured_lb': None,
        },
        'salts_or_seeds': ['verifier default (empty salt)'],
    }
    (EXP / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({'passed': res['passed'], 'identical': identical, 'cost': ver['score'],
                      'wall_s': res['metrics']['dfthcsos']['wall_s']}, indent=1))


if __name__ == '__main__':
    main()

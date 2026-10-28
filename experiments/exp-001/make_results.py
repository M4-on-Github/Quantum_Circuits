"""Assemble exp-001 results.json from the runner summaries (Kaggle + local). Copies verifier numbers only."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
KAGGLE = json.loads((HERE / 'kaggle_output' / 'exp001' / 'summary_kaggle.json').read_text())
LOCAL = {}
for tag in ('local_invsqrt', 'local_invsqrt_rerun', 'local_dfthcsos'):
    p = HERE / 'logs' / 'local' / f'summary_{tag}.json'
    if p.is_file():
        LOCAL[tag] = json.loads(p.read_text())
KERNEL = json.loads((HERE / 'kernel' / 'server-metadata-v1.json').read_text())


def runs(summary):
    return {r['label']: r for r in summary['runs']}


K = runs(KAGGLE)
L = {lab: r for s in LOCAL.values() for lab, r in runs(s).items()}


def mem(r):
    return {k: r[k] for k in ('wall_s', 'tree_rss_peak_bytes', 'proc_hwm_peak_bytes', 'sys_used_peak_bytes',
                              'max_live_processes', 'returncode', 'start_utc')}


def inv_metrics(o):
    return {'Q': o['num_qubits'], 'toffoli': o['toffoli_equivalent'], 'toffoli_count': o['toffoli_count'],
            't_gates': o['t_count'], 'rotation_count': o['rotation_count'], 'rotation_eps': o['rotation_eps'],
            'cost': o['score'], 'verified_shots': o['verified_shots'],
            'worst_error_over_tolerance': o['worst_error_over_tolerance'], 'worst_x': o['worst_x'],
            'circuit_sha256': o['circuit_sha256']}


def dqi_metrics(o):
    return {'Q': o['num_qubits'], 'toffoli': o['toffoli_count'], 'max_toffoli_count': o['max_toffoli_count'],
            'cost': o['score'], 'failures': o['value_errors'] + o['phase_errors'],
            'value_errors': o['value_errors'], 'phase_errors': o['phase_errors'], 'shots': o['verified_shots'],
            'eps_plus': o['effective_error_rate'], 'R': o['repetition_factor'], 'num_bits': o['num_bits'],
            'circuit_sha256': o['circuit_sha256']}


def dft_metrics(o):
    m, r = o['metrics'], o['resources']
    return {'Q': o['num_qubits'], 'toffoli': o['toffoli_count'], 'cost': o['score'], 'lambda_eff': o['lambda_eff'],
            'Lambda': m['Lambda'], 'E_gap': m['E_gap'], 'ham_error_mHa': 1e3 * max(m['error_1'], m['error_2']),
            'error_1_mHa': 1e3 * m['error_1'], 'error_2_mHa': 1e3 * m['error_2'], 'max_width': r['angles_qubits'],
            'n_circuits': o['num_circuits'], 'brot': o['brot'], 'angles_toffoli': r['angles_toffoli'],
            'heuristic_toffoli': r['heuristic_toffoli'], 'verified_shots': o['verified_shots'],
            'submission_sha256': o['submission_sha256']}


def cmd_str(r):
    return ' '.join(Path(c).name if i == 0 else c for i, c in enumerate(r['cmd']))


out_k = {lab: r['verifier_output'] for lab, r in K.items()}
out_l = {lab: r['verifier_output'] for lab, r in L.items()}

tasks = {
    'invsqrt': {
        'verifier': 'verify_submission_invsqrt.py',
        'verifier_cmd': cmd_str(K['invsqrt']),
        'passed': out_k['invsqrt']['status'] == 'PASS',
        'metrics': inv_metrics(out_k['invsqrt']),
        'kaggle': mem(K['invsqrt']),
        'kaggle_rerun': {**mem(K['invsqrt_rerun']), 'identical_output': out_k['invsqrt'] == out_k['invsqrt_rerun']},
    },
    'dqi': {
        'verifier': 'verify_submission_dqi.py',
        'verifier_cmd': cmd_str(K['dqi']),
        'passed': out_k['dqi']['status'] == 'PASS',
        'metrics': dqi_metrics(out_k['dqi']),
        'kaggle': mem(K['dqi']),
        'local': 'not run (pre-registered: Kaggle only)',
    },
    'dfthcsos': {
        'verifier': 'verify.py',
        'verifier_cmd': cmd_str(K['dfthcsos']),
        'passed': out_k['dfthcsos']['status'] == 'PASS',
        'metrics': dft_metrics(out_k['dfthcsos']),
        'kaggle': mem(K['dfthcsos']),
    },
}
for lab in ('invsqrt', 'invsqrt_rerun', 'dfthcsos'):
    if lab in L:
        task = 'dfthcsos' if lab == 'dfthcsos' else 'invsqrt'
        o = out_l[lab]
        met = dft_metrics(o) if task == 'dfthcsos' else inv_metrics(o)
        key = 'local' if lab != 'invsqrt_rerun' else 'local_rerun'
        tasks[task][key] = {**mem(L[lab]), 'passed': o['status'] == 'PASS', 'metrics': met,
                            'identical_to_kaggle': o == out_k[lab]}
        if task == 'dfthcsos':
            tasks[task][key]['cost_rel_diff_vs_kaggle'] = abs(o['score'] - out_k[lab]['score']) / out_k[lab]['score']

if 'invsqrt' in out_l and 'invsqrt_rerun' in out_l:
    tasks['invsqrt']['local_rerun']['identical_to_local_first'] = out_l['invsqrt'] == out_l['invsqrt_rerun']

commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=HERE).stdout.strip()
results = {
    'exp': 'exp-001',
    'commit': commit,
    'task': 'all',
    'passed': all(t['passed'] for t in tasks.values()),
    'tasks': tasks,
    'baseline': None,
    'improvement_factor': 1.0,
    'score_delta_factor': 1.0,
    'runtime_s': {'kaggle_kernel_total': round(sum(r['wall_s'] for r in K.values()), 1),
                  **{f'kaggle_{lab}': r['wall_s'] for lab, r in K.items()},
                  **{f'local_{lab}': r['wall_s'] for lab, r in L.items()}},
    'salts_or_seeds': ['verifier defaults: no --salt, no --seed; seed = int(SHA-256 of canonical .kmb) for invsqrt/dqi, '
                       'int(submission_sha256) for dfthcsos'],
    'kaggle_kernel': {'slug': KERNEL['id'], 'id_no': KERNEL['id_no'], 'version': 1,
                      'docker_image': KERNEL['docker_image'], 'machine': KAGGLE['machine']},
    'local_machine': next(iter(LOCAL.values()))['machine'] if LOCAL else None,
    'input_sha256_kaggle': KAGGLE['input_sha256'],
    'input_sha256_match_local': all(KAGGLE['input_sha256'][k] == v for s in LOCAL.values()
                                    for k, v in s['input_sha256'].items() if k in KAGGLE['input_sha256']),
}
(HERE / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({t: {k: v for k, v in d['metrics'].items() if k in ('Q', 'toffoli', 'cost', 'R')}
                  for t, d in tasks.items()}, indent=1))

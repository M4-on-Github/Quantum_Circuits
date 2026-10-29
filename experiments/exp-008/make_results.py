"""exp-008: write results.json from the downloaded Kaggle output (verifier stdout + meta).

python -I -B make_results.py <kaggle_output_dir> <commit>
"""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
out_dir = Path(sys.argv[1])
commit = sys.argv[2]
v = json.loads((out_dir / 'exp008' / 'verify_full.json').read_text())
meta = json.loads((out_dir / 'exp008' / 'verify_meta.json').read_text())
FRONTIER = 102664.23957721348
build_s = next(l.split(' in ')[1].rstrip('s') for l in (out_dir / 'exp008' / 'kernel.log').read_text().splitlines() if 'build rc' in l)
BASE = 2076774.233715282
res = {
    'exp': 'exp-008',
    'commit': commit,
    'task': 'invsqrt',
    'verifier': 'verify_submission_invsqrt.py',
    'verifier_cmd': ' '.join(meta['cmd']) + f"  (cwd {meta['cwd']})",
    'verifier_sha256': meta['verifier_sha256'],
    'kernel': 'rainm4/exp-008-invsqrt-port-verify',
    'passed': v.get('status') == 'PASS',
    'circuit_sha256': v.get('circuit_sha256'),
    'generator': 'src/invsqrt (config experiments/exp-008/config_port.json)',
    'metrics': {
        'Q': v.get('num_qubits'),
        'toffoli': v.get('toffoli_count'),
        'max_toffoli': v.get('max_toffoli_count'),
        't_gates': v.get('t_count'),
        'rotation_count': v.get('rotation_count'),
        'rotation_eps': v.get('rotation_eps'),
        'toffoli_equivalent': v.get('toffoli_equivalent'),
        'cost': v.get('score'),
        'worst_error_over_tolerance': v.get('worst_error_over_tolerance'),
        'worst_x': v.get('worst_x'),
        'verified_shots': v.get('verified_shots'),
    },
    'baseline': {'exp': 'exp-001', 'cost': BASE},
    'improvement_factor': BASE / v['score'] if v.get('score') else None,
    'score_delta_factor': (BASE / v['score']) ** (1 / 3) if v.get('score') else None,
    'frontier': {'cost': FRONTIER, 'Q': 63, 'sha256': '07314803a0925970cf45007ebbdb8a146378c242e3991c70d6f7509af3d583da',
                 'source': 'busyaprime/33-qcc-v8-members v4 (dataset README: official x86-64 unsalted 102,664.24)'},
    'cost_over_frontier': v['score'] / FRONTIER if v.get('score') else None,
    'c014_threshold': 1.01 * FRONTIER,
    'c014_holds': bool(v.get('status') == 'PASS' and v['score'] <= 1.01 * FRONTIER),
    'byte_identical_to_frontier': v.get('circuit_sha256') == '07314803a0925970cf45007ebbdb8a146378c242e3991c70d6f7509af3d583da',
    'byte_identical_to_marsyas_stated': v.get('circuit_sha256') == 'ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917',
    'kernel_version': 1,
    'runtime_s': meta['wall_s'],
    'runtime_note': 'runtime_s is the verifier subprocess wall time on Kaggle (4 forked workers); the in-kernel build took ' + build_s + ' s',
    'memory': meta['peak'],
    'machine': meta['machine'],
    'salts_or_seeds': ['default (no salt, no seed)'],
}
(here / 'results.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
print(json.dumps(res, indent=1))

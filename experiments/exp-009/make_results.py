"""exp-009: write results.json from the downloaded kernel output, manifest.json and accepted baseline costs.

Usage (repo root): python -I -B experiments/exp-009/make_results.py <commit>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
KO = HERE / 'kaggle_output' / 'exp009'

# C-001 references (knowledge/claims.md)
REF = {'invsqrt': 260 * 7988, 'dqi': 1.19128 * 1893 ** 2 * 5725461, 'dfthcsos': 3355599588.3}
# exp-001 (accepted) sample costs; exp-004 (accepted) re-verified dfthcsos from its zip identically
SAMPLE_COST = {'invsqrt': 2076774.233715282, 'dqi': 24439463583672.93, 'dfthcsos': 3355599588.3155365}
EXP008_COST = 148977.90224394592
PRED = {'toffoli': (1304.000 - 0.0016, 1304.000 + 0.0016), 'cost': (148977.95 - 0.15, 148977.95 + 0.15),
        'rotation_eps': 2.8298390184213153e-13, 'worst': 0.9999059628540141, 'Q': 92}
WINDOW = (2.4043, 2.4091)


def main():
    commit = sys.argv[1]
    v = json.loads((KO / 'verify_full.json').read_text())
    m = json.loads((KO / 'verify_meta.json').read_text())
    man = json.loads((HERE / 'manifest.json').read_text())
    e004 = json.loads((REPO / 'experiments' / 'exp-004' / 'manifest.json').read_text())
    cost = v['score']
    costs = dict(SAMPLE_COST, invsqrt=cost)
    f_ref = {k: REF[k] / costs[k] for k in REF}
    f_exact = {k: SAMPLE_COST[k] / costs[k] for k in REF}
    score_ref = (f_ref['invsqrt'] * f_ref['dqi'] * f_ref['dfthcsos']) ** (1 / 3)
    score_exact = (f_exact['invsqrt'] * f_exact['dqi'] * f_exact['dfthcsos']) ** (1 / 3)
    held = {
        'pass': v['status'] == 'PASS',
        'Q': v['num_qubits'] == PRED['Q'],
        'rotation_eps_exact': v['rotation_eps'] == PRED['rotation_eps'],
        'worst_ratio_exact': v['worst_error_over_tolerance'] == PRED['worst'],
        'toffoli_in_band': PRED['toffoli'][0] <= v['toffoli_count'] <= PRED['toffoli'][1],
        'cost_in_band': PRED['cost'][0] <= cost <= PRED['cost'][1],
        'circuit_sha256': v['circuit_sha256'] == 'ff629b0925ebfce1e7da166f895b1105332e7edebe26f359deb32f7c942b5917',
        'shots_full': v['verified_shots'] == 64 * 3133452,
        'local_score_in_c001_window': WINDOW[0] <= score_ref <= WINDOW[1] and WINDOW[0] <= score_exact <= WINDOW[1],
    }
    e004m = {x['name']: x for x in e004['members']}
    raw_entries_same = {x['name']: (x['compressed_size'] == e004m[x['name']]['compressed_size']
                                    and x['crc32'] == e004m[x['name']]['crc32'])
                        for x in man['members'] if x['name'] != 'invsqrt.kmb'}
    res = {
        'exp': 'exp-009',
        'submission': 'S-002',
        'commit': commit,
        'task': 'all',
        'verifier': 'verify_submission_invsqrt.py',
        'verifier_cmd': ' '.join(m['cmd']) + f"  (cwd {m['cwd']})",
        'verifier_sha256': m['verifier_sha256'],
        'kernel': 'rainm4/exp-009-s002-invsqrt-salt-verify',
        'kernel_version': 1,
        'passed': v['status'] == 'PASS',
        'circuit_path': 'experiments/exp-009/out/invsqrt.kmb',
        'circuit_sha256': v['circuit_sha256'],
        'verified_file_sha256': m['verified_file_sha256'],
        'kaggle_rebuild_byte_identical': m['rebuild_byte_identical'],
        'generator': 'src/invsqrt @ 46af961, config experiments/exp-008/config_port.json',
        'metrics': {'Q': v['num_qubits'], 'toffoli': v['toffoli_count'], 'max_toffoli': v['max_toffoli_count'],
                    't_gates': v['t_count'], 'rotation_count': v['rotation_count'],
                    'rotation_eps': v['rotation_eps'], 'toffoli_equivalent': v['toffoli_equivalent'],
                    'cost': cost, 'worst_error_over_tolerance': v['worst_error_over_tolerance'],
                    'worst_x': v['worst_x'], 'verified_shots': v['verified_shots']},
        'baseline': {'exp': 'exp-008', 'cost': EXP008_COST, 'salt': 'default'},
        'cost_change_vs_exp008_default_salt': cost - EXP008_COST,
        'improvement_factor': SAMPLE_COST['invsqrt'] / cost,
        'score_delta_factor': (SAMPLE_COST['invsqrt'] / cost) ** (1 / 3),
        'local_score': {
            'task_costs': costs,
            'task_cost_sources': {'invsqrt': 'this verify (exp-009, salt exp-009-S-002)',
                                  'dqi': 'exp-001 (sample member, byte-identical)',
                                  'dfthcsos': 'exp-001 / exp-004 (sample members, byte-identical)'},
            'factors_vs_c001_refs': f_ref, 'score_vs_c001_refs': score_ref,
            'factors_vs_exact_sample_costs': f_exact, 'score_vs_exact_sample_costs': score_exact,
            'c001_lb_window': list(WINDOW),
            'alternatives': {'x1.015_refs_higher': [score_exact * 1.015, score_ref * 1.015],
                             'x0.974938_dqi_half_shot_eps': [score_exact * 0.974938, score_ref * 0.974938]},
        },
        'zip': {'path': man['zip_path'], 'sha256': man['zip_sha256'], 'size': man['zip_size'],
                'n_members': man['n_members'], 'all_checks_pass': man['all_checks_pass'],
                'member_sha256': {x['name']: x['sha256'] for x in man['members']},
                'non_invsqrt_raw_entries_same_size_and_crc_as_exp004': all(raw_entries_same.values())},
        'predictions_held': held,
        'runtime_s': m['wall_s'],
        'runtime_note': f"verifier subprocess wall on Kaggle (4 forked workers); in-kernel rebuild {m['build_s']:.1f} s",
        'memory': m['peak'],
        'machine': m['machine'],
        'salts_or_seeds': [m['salt']],
    }
    (HERE / 'results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({'held': held, 'score_ref': score_ref, 'score_exact': score_exact, 'cost': cost,
                      'zip_sha256': man['zip_sha256']}, indent=1))


if __name__ == '__main__':
    main()

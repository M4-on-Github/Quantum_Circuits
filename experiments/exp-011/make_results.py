"""Assembles experiments/exp-011/results.json from the downloaded kernel outputs and the local anatomy.

Usage: python -I -B experiments/exp-011/make_results.py
Every number comes from a file: the official verifier's JSON (kaggle_output/exp011/verify_*.stdout.txt), the kernel's
build/stats/dump records and runs.json, and out/anatomy/compare.json (our analysis of the .kmx text).
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KO = HERE / 'kaggle_output' / 'exp011'
UPSTREAM = 'b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6'
PRED_COST = 4.22346e11
BASE_COST = 24439471538812.85  # exp-003 / exp-001 sample dqi
EXP005_COST_DEFAULT = 414781342770.7355


def load(p):
    return json.loads(Path(p).read_text())


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else 'pending'
    runs = load(KO / 'runs.json')
    rr = {r['label']: r for r in runs['runs']}
    build, stats, dump = load(KO / 'build.json'), load(KO / 'stats.json'), load(KO / 'dump.json')
    ver = {}
    for label, salt in (('verify_default', None), ('verify_salt', 'exp011-a')):
        txt = (KO / f'{label}.stdout.txt').read_text()
        v = json.loads(txt[txt.index('{'):])
        ver[label] = dict(salt=salt, status=v['status'], Q=v['num_qubits'], toffoli_mean=v['toffoli_count'],
                          toffoli_static=v['max_toffoli_count'], failures=v['value_errors'] + v['phase_errors'],
                          value_errors=v['value_errors'], phase_errors=v['phase_errors'],
                          shots=v['verified_shots'], eps_plus=v['effective_error_rate'], R=v['repetition_factor'],
                          cost=v['score'], num_ops=v['num_ops'], reaction_depth=v['reaction_depth'],
                          circuit_sha256=v['circuit_sha256'], wall_s=rr[label]['wall_s'],
                          proc_hwm_peak_bytes=rr[label]['proc_hwm_peak_bytes'],
                          tree_rss_peak_bytes=rr[label]['tree_rss_peak_bytes'],
                          cost_within_1pct_of_prediction=abs(v['score'] / PRED_COST - 1) <= 0.01)
    costs = [ver[k]['cost'] for k in ver]
    mean_cost = sum(costs) / len(costs)
    passed = all(ver[k]['status'] == 'PASS' for k in ver)
    anatomy = load(HERE / 'anatomy' / 'compare.json') if (HERE / 'anatomy' / 'compare.json').exists() \
        else None
    res = {
        'exp': 'exp-011', 'commit': commit, 'task': 'dqi', 'tests': ['C-016'],
        'origin': ('ported baseline: SomeJoint (Agniv Banerjee) 897-qubit dqi decoder, notebook '
                   'somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi v14, Apache-2.0; design lineage via '
                   'Alex Chilton and the unlicensed jday96314/QuantumAI (see src/dqi/NOTICE). Not our design; '
                   'our part is only the launcher src/dqi/generate.py, the manifest and the build/verify harness.'),
        'verifier': 'verify_submission_dqi.py',
        'verifier_cmd': [' '.join(Path(c).name if i == 1 else c for i, c in enumerate(rr[k]['cmd'][1:], 1))
                         for k in ('verify_default', 'verify_salt')],
        'verifier_sha256': runs['machine']['verifier_sha256'],
        'kernel': 'rainm4/exp-011-dqi-897-port-verify', 'machine': runs['machine'],
        'passed': passed,
        'circuit_path': '/tmp/exp011/dqi.kmb (Kaggle kernel; not downloaded; rebuild with src/dqi/generate.py)',
        'circuit_sha256': stats['file_sha256'], 'circuit_canonical_sha256': stats['canonical_sha256'],
        'byte_identical_to_upstream_b3354f60': stats['equals_b3354f60'],
        'canonical_identical_to_upstream_b3354f60': stats['canonical_equals_b3354f60'],
        'identical_to_v15_53d8b2ed': stats['equals_v15_53d8b2ed'],
        'metrics': {'Q': ver['verify_default']['Q'], 'toffoli': sum(ver[k]['toffoli_mean'] for k in ver) / 2,
                    'toffoli_static': stats['num_toffoli_like'], 't_gates': stats['num_t_like'],
                    'num_ops': stats['num_ops'], 'cost': mean_cost, 'cost_per_salt': costs,
                    'cost_range': [min(costs), max(costs)],
                    'failures': [ver[k]['failures'] for k in ver], 'shots': ver['verify_default']['shots'],
                    'eps_plus_per_salt': [ver[k]['eps_plus'] for k in ver],
                    'R_per_salt': [ver[k]['R'] for k in ver]},
        'verify_runs': ver,
        'build': build, 'stats': stats, 'dump': dump,
        'baseline': {'exp': 'exp-003', 'cost': BASE_COST, 'note': 'sample dqi (reference decoder)'},
        'improvement_factor': BASE_COST / mean_cost,
        'improvement_factor_note': 'ported SomeJoint circuit vs the reference decoder; not an improvement of ours',
        'score_delta_factor': (BASE_COST / mean_cost) ** (1 / 3),
        'vs_exp005_889q_default_cost': ver['verify_default']['cost'] / EXP005_COST_DEFAULT,
        'prediction': {'cost': PRED_COST, 'window_1pct': [PRED_COST * 0.99, PRED_COST * 1.01],
                       'byte_identical_expected': True, 'Q': 897, 'toffoli_static': 454477, 'num_ops': 55778145,
                       'toffoli_mean_default': 440633.0},
        'claim_C016_refuted': (not passed) or not all(ver[k]['cost_within_1pct_of_prediction'] for k in ver),
        'runtime_s': {k: rr[k]['wall_s'] for k in rr},
        'peak_proc_hwm_bytes': {k: rr[k]['proc_hwm_peak_bytes'] for k in rr},
        'salts_or_seeds': ['(default, no salt)', 'exp011-a'],
        'anatomy': anatomy and {k: anatomy[k] for k in ('unit_ratio', 'tag_count_total', 'tag_count_conditioned')}
                   | {'units_restart_exp011': anatomy['exp011']['units_restart'],
                      'units_restart_exp005': anatomy['exp005']['units_restart'],
                      'fingerprint_hits_exp011': {k: v['hits'] for k, v in
                                                  anatomy['exp011']['fingerprint']['searches'].items()},
                      'kernel_hist_restart_exp011_top': dict(list(anatomy['exp011']['kernel_hist_restart'].items())[:8]),
                      'skeleton_exp011': anatomy['exp011']['skeleton']},
    }
    assert all(math.isfinite(c) for c in costs)
    (HERE / 'results.json').write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('passed', 'byte_identical_to_upstream_b3354f60', 'claim_C016_refuted',
                                          'improvement_factor')}, indent=1))
    for k, v in ver.items():
        print(k, {x: v[x] for x in ('status', 'Q', 'toffoli_mean', 'toffoli_static', 'failures', 'eps_plus', 'R',
                                    'cost', 'wall_s')})


if __name__ == '__main__':
    main()

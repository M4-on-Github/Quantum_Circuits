"""Builds experiments/exp-003/results.json from the downloaded Kaggle outputs.

Inputs (kaggle_output/exp003/): sample_count.json, generator_count.json, gen_compare.json, runs.json.
Every number comes from those files (counter tallies over the official circuit, and the official
verifier's JSON). The only derived quantities are sums over tag paths and expected per-shot counts
(static count x probability that the enclosing classical condition holds, using the verifier's
uniform E_j distribution over 0..4095).
"""
from __future__ import annotations

import collections
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
KO = HERE / 'kaggle_output' / 'exp003'
P_RUN = 4095 / 4096   # P(E_j != 0) for E_j ~ Uniform{0..4095} (verify_submission_dqi.py sample_shots)
BASELINE = {'exp': 'exp-001', 'cost': 24439463583672.93, 'toffoli': 5725108.382109375,
            'max_toffoli_count': 5725461, 'Q': 1893}


def classify(segs: list[str]) -> str:
    top = segs[0] if segs else '(none)'
    if 'gf_inverse_chain' in segs:
        return 'inversion_forney' if top == 'chien_forney_mbuc' else 'inversion_eea_division'
    if 'gf_div' in segs and 'gf_mul' in segs:
        return 'mul_eea_division'
    if 'c_gf_mul' in segs and 'gf_mul' in segs:
        return 'mul_eea_sweep_core'
    if 'c_gf_mul' in segs:
        return 'mul_eea_sweep_control_overhead'
    if 'gf_mul' in segs:
        return 'mul_other'
    if 'quotient_div' in segs:
        return 'eea_quotient_accumulate'
    if top == 'chien_forney_mbuc':
        return 'forney_step_other' if 'forney_step' in segs else 'chien_align_unalign'
    return 'other'


def other_key(segs: list[str]) -> str:
    # Group "everything else" by the EEA sub-step (or top mark) and the innermost kickmix tag.
    if segs and segs[0] in ('forward_eea', 'reverse_eea'):
        sub = segs[2] if len(segs) > 2 else 'eea_step(direct)'
        if sub == 'multiply_and_add_or_sub' and len(segs) > 3:
            sub = f'{sub}/{segs[3]}'
        return f'eea/{sub}'
    return segs[0] if segs else '(untagged)'


def breakdown(count: dict) -> dict:
    static = collections.Counter()
    cond = collections.Counter()
    other = collections.Counter()
    mul_tof = 0
    for path, n in count['by_path'].items():
        segs = path.split('/') if path else []
        c = classify(segs)
        static[c] += n
        if c == 'other':
            other[other_key(segs)] += n
        if 'gf_mul' in segs:
            mul_tof += n
    for key, n in count['conditioned_by_path'].items():
        path = key.split(' | ', 1)[0]
        cond[classify(path.split('/') if path else [])] += n
    assert sum(cond.values()) == count['conditioned_toffoli_like'], 'conditioned_by_path truncated'
    total = count['total_toffoli_like']
    rows = {}
    for c in sorted(static, key=lambda k: -static[k]):
        per_shot = static[c] - cond[c] + cond[c] * P_RUN
        rows[c] = {'static': static[c], 'conditioned_static': cond[c],
                   'per_shot_expected': round(per_shot, 3),
                   'share_static': round(static[c] / total, 5)}
    hist = count['instance_histograms']
    return {'total_static': total,
            'total_per_shot_expected': round(sum(r['per_shot_expected'] for r in rows.values()), 3),
            'categories': rows,
            'other_breakdown': dict(sorted(other.items(), key=lambda kv: -kv[1])),
            'toffolis_inside_any_gf_mul': mul_tof,
            'instance_histograms': {k: hist.get(k) for k in
                                    ('gf_mul', 'c_gf_mul', 'gf_inverse_chain', 'gf_div',
                                     'quotient_div', 'forney_step', 'eea_step')},
            'conditioned_by_top_mark': count['conditioned_by_top_mark'],
            'push_condition_definitions': count['push_condition_definitions']}


def multiplies(count: dict) -> dict:
    # Number of gf_mul instances by location; Forney instances are classically conditioned.
    per_inst = {int(k): v for k, v in count['instance_histograms']['gf_mul'].items()}
    out = collections.Counter()
    for path, n in count['by_path'].items():
        segs = path.split('/') if path else []
        if segs and segs[-1] == 'gf_mul':
            out[classify(segs)] += n
    assert len(per_inst) == 1, per_inst
    tof_each = next(iter(per_inst))
    inst = {k: v // tof_each for k, v in out.items()}
    forney = inst.get('inversion_forney', 0)
    total = sum(inst.values())
    assert total == sum(per_inst.values())
    return {'toffolis_per_gf_mul': tof_each, 'instances_by_location': inst,
            'instances_total_static': total,
            'instances_per_shot_expected': round(total - forney + forney * P_RUN, 4),
            'saving_if_all_51': {'static': 12 * total,
                                 'per_shot': round(12 * (total - forney + forney * P_RUN), 1)},
            'saving_if_non_inversion_only_51': {
                'static': 12 * (total - inst.get('inversion_forney', 0)
                                - inst.get('inversion_eea_division', 0))}}


def main() -> None:
    sample = json.loads((KO / 'sample_count.json').read_text())
    gen = json.loads((KO / 'generator_count.json').read_text())
    cmp_ = json.loads((KO / 'gen_compare.json').read_text())
    runs = json.loads((KO / 'runs.json').read_text())
    ver = [r for r in runs['runs'] if r['label'].startswith('dqi_salt_')]
    outs = [r['output'] for r in ver]
    tof = [o['toffoli_count'] for o in outs]
    cost = [o['score'] for o in outs]
    eps = [o['effective_error_rate'] for o in outs]
    passed = all(o['status'] == 'PASS' for o in outs)
    bd = breakdown(sample)
    mean_cost = statistics.mean(cost)
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True,
                            cwd=HERE).stdout.strip()
    res = {
        'exp': 'exp-003',
        'commit': commit,
        'task': 'dqi',
        'verifier': 'verify_submission_dqi.py',
        'verifier_cmd': ' '.join(['python3', *[Path(c).name if i < 2 else c
                                               for i, c in enumerate(ver[0]['cmd'][1:], 1)]])
                        .replace('--salt exp003-a', '--salt <exp003-a|exp003-b|exp003-c>'),
        'verifier_cmd_full': [r['cmd'] for r in ver],
        'passed': passed,
        'metrics': {
            'Q': outs[0]['num_qubits'],
            'toffoli': statistics.mean(tof),
            'toffoli_per_salt': tof,
            'max_toffoli_count': outs[0]['max_toffoli_count'],
            't_gates': 0,
            'cost': mean_cost,
            'cost_per_salt': cost,
            'cost_range': [min(cost), max(cost)],
            'failures': [o['value_errors'] + o['phase_errors'] for o in outs],
            'shots': outs[0]['verified_shots'],
            'eps_plus': statistics.mean(eps),
            'eps_plus_range': [min(eps), max(eps)],
            'R': statistics.mean(o['repetition_factor'] for o in outs),
            'circuit_sha256': outs[0]['circuit_sha256'],
        },
        'baseline': BASELINE,
        'improvement_factor': BASELINE['cost'] / mean_cost,
        'score_delta_factor': (BASELINE['cost'] / mean_cost) ** (1 / 3),
        'runtime_s': {r['label']: r['wall_s'] for r in runs['runs']},
        'peak_proc_hwm_bytes': {r['label']: r['proc_hwm_peak_bytes'] for r in runs['runs']},
        'salts_or_seeds': [r['cmd'][-1] for r in ver],
        'accounting': {
            'sample': bd,
            'multiplies': multiplies(sample),
            'generator_vs_sample': {k: cmp_[k] for k in
                                    ('circuit_equal', 'canonical_sha_equal', 'op_counts_equal')},
            'generator_breakdown_equal_to_sample': breakdown(gen) == bd,
            'counter_total_matches_operation_statistics':
                sample['total_toffoli_like'] == sample['circuit_info']['num_toffoli_like'],
            'kmx_bytes': sample['kmx_bytes'], 'kmx_lines': sample['n_lines'],
            'per_shot_check': {
                'expected_mean': bd['total_per_shot_expected'],
                'sd_of_102400_shot_mean': round(351 * ((4095 * (1 / 4096) * P_RUN) / 102400) ** 0.5, 3),
                'measured_means': tof,
                'baseline_unsalted_mean': BASELINE['toffoli']},
        },
        'machine': runs['machine'],
    }
    (HERE / 'results.json').write_text(json.dumps(res, indent=2))
    print(json.dumps({'categories': bd['categories'], 'mult': res['accounting']['multiplies'],
                      'gen': res['accounting']['generator_vs_sample'],
                      'tof': tof, 'cost': cost}, indent=1))


if __name__ == '__main__':
    main()

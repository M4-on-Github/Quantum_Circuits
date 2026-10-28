"""Builds experiments/exp-005/results.json from the downloaded kernel outputs and the local analysis.

Usage (repo root): .venv/Scripts/python.exe -I experiments/exp-005/make_results.py

Inputs:
  kaggle_output/exp005/        kernel rainm4/exp-005-dqi-897q-accounting v1 (verifier runs, count, segsim)
  kaggle_output_dump/exp005dump/dump.json   kernel rainm4/exp-005-dqi-kmx-dump v1 (kmx export record)
  out/skeleton.npz             analysis/kmx_skeleton.py
  out/semantics*.json/.npz     analysis/kernel_semantics.py (plain and restart modes)
  out/field_test.json          analysis/field_test.py
  out/fingerprint_search.json  analysis/fingerprint_search.py
  controls.json                analysis/controls.py (controls, jet skeleton check, 126-Toffoli zero divisors)

Revision after the critic review (critic.md): the measured numbers are unchanged. `commit` is pinned to the
commit whose code produced them. The revision only adds provenance, the critic's default-salt run (labelled
as the critic's), the pre-registered GF(2^12) multiply share and annotations of the field-test summary.
"""
import collections
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
KO = HERE / 'kaggle_output' / 'exp005'
OUT = HERE / 'out'
SALTS = ['exp005-a', 'exp005-b', 'exp005-c']
RESULTS_COMMIT = '70659bf'  # code that produced the measured numbers (kernel outputs + local analysis)
_KMX = 'experiments/exp-005/kaggle_output_dump/exp005dump/dqi.kmx.xz'
_O = 'experiments/exp-005/out/'
_A = '.venv/Scripts/python.exe -I -B experiments/exp-005/analysis/'
# Run from the repo root. The original invocations were not logged; these reproduce out/ exactly
# (critic.md check 2; field_test.py needs max_per_label = 6, see controls.json field_test_input).
ANALYSIS_CMDS = [
    f'{_A}kmx_skeleton.py {_KMX} {_O}skeleton.npz',
    f'{_A}fingerprint_search.py {_O}skeleton.npz {_O}fingerprint_search.json',
    f'{_A}kernel_semantics.py {_O}skeleton.npz {_KMX} {_O}semantics.json {_O}semantics_gates.npz plain',
    f'{_A}kernel_semantics.py {_O}skeleton.npz {_KMX} {_O}semantics_restart.json {_O}semantics_restart_gates.npz restart',
    f'{_A}field_test.py {_O}skeleton.npz {_KMX} {_O}semantics.json {_O}field_test.json 6',
    f'{_A}controls.py {_O}skeleton.npz {_O}semantics.json {_KMX} experiments/exp-005/controls.json',
    '.venv/Scripts/python.exe -I experiments/exp-005/make_results.py',
]
STAGES = ['extract', 'synthesis', 'convert', 'scan', 'unconvert', 'unsynthesis', 'unextract']


def verifier(salt):
    t = (KO / f'dqi_salt_{salt}.stdout.txt').read_text()
    return json.loads(t[t.index('{'):])


def classes(g):
    kind, A, B, bip, comp = g['kind'], g['compA'], g['compB'], g['bip'], g['comp']
    out = np.empty(len(kind), dtype=object)
    for i in range(len(kind)):
        k = kind[i]
        if k == 2:
            out[i] = 'cswap'
        elif k == 3:
            out[i] = 'ccz'
        elif k == 1:
            out[i] = 'nonaffine_control'
        elif comp[i] < 0:
            out[i] = 'constant_control'
        elif not bip[i]:
            out[i] = 'quadratic_form'
        elif A[i] == 12 and B[i] == 12:
            out[i] = 'product_12x12'
        elif A[i] >= 12:
            out[i] = 'product_wider'
        else:
            out[i] = 'bilinear_small_operand'
    return out


def main():
    runs = json.loads((KO / 'runs.json').read_text())
    count = json.loads((KO / 'count.json').read_text())
    prepare = json.loads((KO / 'prepare.json').read_text())
    dump = json.loads((HERE / 'kaggle_output_dump' / 'exp005dump' / 'dump.json').read_text())
    segsim = [json.loads((KO / f'segsim_{k}.json').read_text()) for k in range(4)]
    ver = {s: verifier(s) for s in SALTS}
    T = [ver[s]['toffoli_count'] for s in SALTS]
    cost = [ver[s]['score'] for s in SALTS]
    eps = [ver[s]['effective_error_rate'] for s in SALTS]
    fails = [ver[s]['value_errors'] + ver[s]['phase_errors'] for s in SALTS]
    T_mean = sum(T) / 3

    skel = np.load(OUT / 'skeleton.npz')
    meta = json.loads(str(skel['meta']))
    paths = meta['paths']
    top = np.array([paths[i].split('/')[0] for i in skel['path']])
    full = np.array([paths[i] for i in skel['path']])
    cond = skel['cond'] > 0
    N = len(top)

    # per-shot execution weight of conditioned gates, per top-level path, from the 8,192 segsim shots
    w = np.ones(N)
    exec_frac = {}
    for P in ('unconvert', 'unsynthesis', 'unextract'):
        sc = segsim[0]['static_cond_by_path'][P]
        su = segsim[0]['static_uncond_by_path'][P]
        per = sum(s['per_shot_by_path'][P] for s in segsim) / 4
        exec_frac[P] = (per - su) / sc
        w[(top == P) & cond] = exec_frac[P]
    segsim_mean = sum(s['per_shot_total'] for s in segsim) / 4
    assert abs(w.sum() - segsim_mean) < 0.5, (w.sum(), segsim_mean)

    sem = {}
    for mode, gf, jf in (('restart', 'semantics_restart_gates.npz', 'semantics_restart.json'),
                         ('plain', 'semantics_gates.npz', 'semantics.json')):
        g = np.load(OUT / gf)
        cl = classes(g)
        tab = {}
        for c in sorted(set(cl)):
            m = cl == c
            tab[c] = {'static': int(m.sum()), 'per_shot': round(float(w[m].sum()), 1),
                      'share_of_T': round(float(w[m].sum()) / segsim_mean, 4)}
        by_stage = {}
        for st in STAGES:
            m = top == st
            by_stage[st] = {c: int((m & (cl == c)).sum()) for c in sorted(set(cl)) if (m & (cl == c)).any()}
        sem[mode] = {'by_class': tab, 'by_stage_static': by_stage}
        if mode == 'restart':
            cl_r, g_r = cl, g
    # component (kernel) Toffoli-count histograms, restart mode
    comp = g_r['comp']
    A, B, bip = g_r['compA'], g_r['compB'], g_r['bip']
    comp_sizes = collections.Counter(comp[comp >= 0].tolist())
    comp_wid = {}
    for i in np.nonzero(comp >= 0)[0]:
        comp_wid.setdefault(int(comp[i]), (int(A[i]), int(B[i]), bool(bip[i])))
    hist = collections.defaultdict(collections.Counter)
    for cid, n in comp_sizes.items():
        a_, b_, bp = comp_wid[cid]
        if bp and a_ >= 12:
            hist[f'{a_}x{b_}'][n] += 1
    kernel_hist = {k: dict(sorted(v.items(), key=lambda kv: -kv[1])[:8]) for k, v in
                   sorted(hist.items(), key=lambda kv: -sum(n * c for n, c in kv[1].items()))[:12]}
    units = collections.Counter()
    for cid, n in comp_sizes.items():
        a_, b_, bp = comp_wid[cid]
        if not (bp and a_ >= 12):
            continue
        if n % 42 == 0:
            units['gf2^12_product_42'] += n // 42
        elif n % 99 == 0:
            units['gf2^24_product_99'] += n // 99
        else:
            units['other_toffoli'] += n
    n12 = hist.get('12x12', collections.Counter())
    m63_semantic = n12.get(63, 0)
    over51 = sum(c for n, c in n12.items() if n > 51)
    over51_saving = sum((n - 51) * c for n, c in n12.items() if n > 51)

    fps = json.loads((OUT / 'fingerprint_search.json').read_text())
    field = json.loads((OUT / 'field_test.json').read_text())
    plain_g = np.load(OUT / 'semantics_gates.npz')
    pure_seg = {}
    for sg in json.loads((OUT / 'semantics.json').read_text())['segments']:
        sl = slice(sg['start'], sg['end'])
        cm = plain_g['comp'][sl]
        pure_seg[sg['k']] = bool((plain_g['kind'][sl] == 0).all() and plain_g['bip'][sl].all()
                                 and len(set(cm.tolist())) == 1 and cm[0] >= 0)
    field_sum = collections.Counter(
        (r['label'], r['n_toffoli'], r.get('A'), r.get('B'), pure_seg[r['segment']], bool(r.get('field_like')),
         r.get('output_rank'), r.get('zero_divisor_a_count'),
         tuple(r['rank_fix_small_min_max']) if r.get('rank_fix_small_min_max') else None,
         tuple(r['rank_fix_large_min_max']) if r.get('rank_fix_large_min_max') else None) for r in field)
    jets_fwd = [p for p in paths if p.startswith('extract/')]
    jets_rev = [p for p in paths if p.startswith('unextract/')]
    jet_static = int(np.isin(full, jets_fwd + jets_rev).sum())
    jet_per_shot = float(w[np.isin(full, jets_fwd + jets_rev)].sum())
    inst = count['instance_histograms']

    stage_tab = {}
    for st in STAGES:
        m = top == st
        stage_tab[st] = {'static': int(m.sum()), 'per_shot': round(float(w[m].sum()), 1),
                         'share_of_T': round(float(w[m].sum()) / segsim_mean, 4)}

    M63 = fps['searches']['ixor_gf2_mul']['hits'] + fps['searches']['ixor_gf2_mul_controlled']['hits']
    s_main = sem['restart']['by_class']
    s_12 = s_main.get('product_12x12', {}).get('share_of_T', 0.0)
    s_wide = s_main.get('product_wider', {}).get('share_of_T', 0.0)

    commit = RESULTS_COMMIT
    ctl = json.loads((HERE / 'controls.json').read_text())
    k126 = ctl['kernels_126']
    v0 = ver[SALTS[0]]
    base_cost = 24439471538812.85  # exp-003 results.json metrics.cost (reference decoder, 3 salts)
    res = {
        'exp': 'exp-005',
        'commit': commit,
        'commit_note': 'commit of the code that produced the measured numbers; later revisions add annotations only',
        'analysis_cmds': ANALYSIS_CMDS,
        'task': 'dqi',
        'verifier': 'verify_submission_dqi.py',
        'verifier_cmd': 'python3 verify_submission_dqi.py /tmp/exp005/dqi.kmb --salt <exp005-a|exp005-b|exp005-c>',
        'verifier_cmd_full': [r['cmd'] for r in runs['runs'] if r['label'].startswith('dqi_salt_')],
        'verifier_sha256': runs['machine']['verifier_sha256'],
        'circuit': {'source': 'heliosli/qcc-circuits-live (manifest portfolio v17_sjx), dqi.kmb.xz',
                    'xz_sha256': prepare['xz_sha256'], 'kmb_sha256': prepare['kmb_sha256'],
                    'kmb_bytes': prepare['kmb_bytes'], 'kmx_sha256': dump['kmx_sha256'],
                    'external_not_submittable': True,
                    'dataset_version_downloaded': 11,
                    'dataset_versions_with_same_dqi_bytes': [9, 10, 11],
                    'provenance_note': ('same dqi.kmb.xz bytes in heliosli/qcc-circuits-live versions 9, 10 and 11 '
                                        '(critic.md, fresh downloads). Version 12 (2026-10-28 21:44 UTC) lists a '
                                        'dqi.kmb.xz of the same size, bytes unchecked. This is the circuit behind the '
                                        'public dqi base cost. The digest figure "897Q, mean T 432,740.56" is that '
                                        'cost divided by R x 897^2, i.e. this circuit at the wrong width.')},
        'critic_default_salt_run': {
            'source': 'critic.md, kernel rainm4/exp-005-critic-reverify v2 (critic run, not ours)',
            'salt': None, 'status': 'PASS', 'Q': 889, 'max_toffoli_count': 454507, 'failures': 0,
            'toffoli_count': 440563.9552734375, 'score': 414781342770.7355,
            'note': 'equals the public dqi base cost 414,781,342,770.7355'},
        'passed': all(ver[s]['status'] == 'PASS' for s in SALTS),
        'metrics': {
            'Q': v0['num_qubits'],
            'toffoli': T_mean,
            'toffoli_per_salt': T,
            'max_toffoli_count': v0['max_toffoli_count'],
            't_gates': 0,
            'cost': sum(cost) / 3,
            'cost_per_salt': cost,
            'cost_range': [min(cost), max(cost)],
            'failures': fails,
            'value_errors': [ver[s]['value_errors'] for s in SALTS],
            'phase_errors': [ver[s]['phase_errors'] for s in SALTS],
            'shots': v0['verified_shots'],
            'eps_plus': sum(eps) / 3,
            'eps_plus_per_salt': eps,
            'eps_plus_range': [min(eps), max(eps)],
            'R_per_salt': [ver[s]['repetition_factor'] for s in SALTS],
            'reaction_depth': v0['reaction_depth'],
            'num_ops': v0['num_ops'],
        },
        'baseline': {'exp': 'exp-003', 'cost': base_cost, 'Q': 1893, 'toffoli': 5725110.245654297},
        'improvement_factor': base_cost / (sum(cost) / 3),
        'improvement_factor_note': 'external public circuit vs the reference decoder; not our circuit',
        'score_delta_factor': (base_cost / (sum(cost) / 3)) ** (1 / 3),
        'runtime_s': {r['label']: r['wall_s'] for r in runs['runs']} | {'kmx_dump_load_and_write': dump['load_and_kmx_s'],
                                                                       'kmx_dump_xz': dump['xz_s']},
        'peak_proc_hwm_bytes': {r['label']: r['proc_hwm_peak_bytes'] for r in runs['runs']},
        'salts_or_seeds': SALTS + [f"segsim seeds {segsim[0]['seed']}..{segsim[-1]['seed']} (4 x 2,048 shots)"],
        'accounting': {
            'static_toffoli': count['total_toffoli_like'],
            'static_conditioned_toffoli': count['conditioned_toffoli_like'],
            'counter_total_matches_stats': count['counter_total_matches_stats'],
            'segsim_per_shot_total_mean': segsim_mean,
            'segsim_per_shot_totals': [s['per_shot_total'] for s in segsim],
            'segsim_checks': [{k: s[k] for k in ('toffoli_equal', 'phase_equal', 'qubits_equal',
                                                 'full_value_errors', 'full_phase_errors')} for s in segsim],
            'conditioned_exec_fraction': exec_frac,
            'stages': stage_tab,
            'tag_instance_histograms': inst,
            'jets': {'forward_instances': inst['multiply v'], 'reverse_instances': inst['reverse multiply v'],
                     'forward_toffoli_each': 42 + 15 + 18 + 25 + 70 + 99,
                     'reverse_toffoli_each': 42 + 33 + 99 + 30 + 84 + 84 + 17,
                     'static_toffoli': jet_static, 'per_shot_toffoli': round(jet_per_shot, 1),
                     'share_of_T': round(jet_per_shot / segsim_mean, 4)},
        },
        'c010': {
            'M63_kickmix_fingerprint_hits': M63,
            'fingerprint_search': fps,
            'M63_semantic_12x12_kernels_with_63_toffoli': m63_semantic,
            'projected_51_saving_fraction': 12 * M63 / T_mean,
            'kernels_12x12_over_51_toffoli': over51,
            'saving_if_every_12x12_kernel_over_51_became_51': over51_saving,
            'multiply_share_12x12': s_12,
            'multiply_share_all_field_sized_products': round(s_12 + s_wide, 4),
            'multiply_share_gf2_12_preregistered': {
                'pure_12x12_kernels': s_12,
                'all_42_toffoli_gf2_12_units': round(42 * units['gf2^12_product_42'] / T_mean, 4),
                'note': ('the pre-registered s counts GF(2^12) multiplies: 12.1% (pure 12 x 12 kernels) to 48.0% '
                         '(all 42-Toffoli units, restart mode). s >= 50% holds only if GF(2^24) and wider '
                         'products count as multiplies (all products: 56.6% plain, 76.0% restart).')},
            'kernels_126_zero_divisors': {
                k: {'label': v['label'], 'A': v['A'], 'B': v['B'], 'zero_divisor_found': v['zero_divisor_found'],
                    'fix_A_basis_vector_min_rank': min(v['fix_A']['basis_vector_ranks']),
                    'fix_A_sampled_rank_deficient': v['fix_A']['sampled_rank_deficient'],
                    'fix_B_sampled_rank_deficient': v['fix_B']['sampled_rank_deficient'],
                    'sampled_per_side': v['fix_A']['sampled_nonzero_operands']}
                for k, v in k126.items()},
            'kernels_126_note': ('the 10 126-Toffoli 24 x 24 kernels are 3 x 42 GF(2^12) products in a split '
                                 'algebra with zero divisors, not GF(2^24) (controls.json kernels_126; critic.md)'),
            'untagged_99_note': ('the 662 untagged 24 x 24 99-Toffoli components are identified by Toffoli count '
                                 'and operand widths only. Only tagged multiply v kernels were field-tested'),
            'class_table_restart_mode': sem['restart']['by_class'],
            'class_table_plain_mode': sem['plain']['by_class'],
            'class_by_stage_static_restart_mode': sem['restart']['by_stage_static'],
            'kernel_toffoli_histograms_restart_mode': kernel_hist,
            'product_units_restart_mode': dict(units),
            'field_test_summary': [{'label': k[0], 'n_toffoli': k[1], 'A': k[2], 'B': k[3],
                                    'pure_bilinear_segment': k[4], 'field_like': k[5], 'output_rank_12x12': k[6],
                                    'zero_divisor_a_count_12x12': k[7], 'rank_fix_small_min_max': k[8],
                                    'rank_fix_large_min_max': k[9], 'segments': v}
                                   for k, v in field_sum.most_common()],
            'verdict': None,
        },
    }
    for row in res['c010']['field_test_summary']:
        if row['n_toffoli'] == 126:
            row['algebra_note'] = '3 x 42 product in a split algebra with zero divisors, not GF(2^24)'
            if row['field_like']:
                row['field_like_note'] = ('sampling false positive: zero divisors have density about 2^-11; '
                                          'explicit witnesses in controls.json kernels_126')
    holds = (s_12 + s_wide) >= 0.5 and res['c010']['projected_51_saving_fraction'] >= 0.08
    res['c010']['verdict'] = 'holds' if holds else 'refuted'
    (HERE / 'results.json').write_text(json.dumps(res, indent=1))
    print(json.dumps({'Q': res['metrics']['Q'], 'T': T_mean, 'cost': res['metrics']['cost'], 'fails': fails,
                      'M63': M63, 'm63_sem': m63_semantic, 's12': s_12, 'swide': s_wide,
                      'jets': res['accounting']['jets'], 'verdict': res['c010']['verdict']}, indent=1))


if __name__ == '__main__':
    main()

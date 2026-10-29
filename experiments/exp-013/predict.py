"""exp-013 pre-registration arithmetic: predicted LB score of S-003 from accepted verifier costs.

Usage (repo root): .venv/Scripts/python.exe -I -B experiments/exp-013/predict.py experiments/exp-013/prediction.json

Score = geomean over tasks of (sample verified cost / our verified cost) (C-001, supported form).
dqi cost at k failures: our mean cost at 0 failures (exp-011, two salts) x R(eps+(k)) / R(eps+(0)), with eps+ and R
from the official verifier's own clopper_pearson_upper_bound and repetition_overhead (imported, not copied).
Mean T changes with the salt by about 5e-8 relative (exp-011), which is below the 5th decimal of the score.
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(p):
    return json.loads((REPO / p).read_text(encoding='utf-8'))


def main(out):
    spec = importlib.util.spec_from_file_location('vdqi', REPO / 'data/verifiers/dqi/verify_submission_dqi.py')
    v = importlib.util.module_from_spec(spec)
    sys.modules["vdqi"] = v
    spec.loader.exec_module(v)
    e1, e9, e11 = load('experiments/exp-001/results.json'), load('experiments/exp-009/results.json'), \
        load('experiments/exp-011/results.json')
    ref = {'invsqrt': e1['tasks']['invsqrt']['metrics']['cost'], 'dqi': e1['tasks']['dqi']['metrics']['cost'],
           'dfthcsos': e1['tasks']['dfthcsos']['metrics']['cost']}
    inv = {'exp-009 (salt exp-009-S-002)': e9['metrics']['cost'], 'exp-008 (default salt)': e9['baseline']['cost']}
    dqi0 = e11['metrics']['cost']  # mean of the two 0-failure salts
    n = e11['metrics']['shots']
    r0 = v.repetition_overhead(v.clopper_pearson_upper_bound(0, n))
    rows = []
    for k in range(6):
        eps = v.clopper_pearson_upper_bound(k, n)
        r = v.repetition_overhead(eps)
        dqi = dqi0 * r / r0
        sc = {}
        for lab, ic in inv.items():
            f = {'invsqrt': ref['invsqrt'] / ic, 'dqi': ref['dqi'] / dqi, 'dfthcsos': 1.0}
            sc[lab] = math.prod(f.values()) ** (1 / 3)
        rows.append({'failures': k, 'eps_plus': eps, 'R': r, 'dqi_cost': dqi, 'dqi_factor': ref['dqi'] / dqi,
                     'score': sc, 'score_ratio_vs_0': None})
    for row in rows:
        row['score_ratio_vs_0'] = row['score']['exp-009 (salt exp-009-S-002)'] / rows[0]['score']['exp-009 (salt exp-009-S-002)']
    lam = 0.25  # lead's P(>=1 failure) about 22% <=> Poisson mean 0.25 per 102,400-shot run
    pk = [math.exp(-lam) * lam ** k / math.factorial(k) for k in range(6)]
    res = {'reference_costs_sample_exp001': ref, 'our_invsqrt_costs': inv, 'our_dqi_cost_0_failures_exp011': dqi0,
           'dqi_cost_per_salt_exp011': e11['metrics']['cost_per_salt'], 'dfthcsos_factor': 1.0,
           'invsqrt_factor': {k: ref['invsqrt'] / c for k, c in inv.items()},
           'rows': rows, 'poisson_mean_assumed': lam, 'poisson_p': pk}
    Path(out).write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8', newline='\n')
    for row in rows:
        print(row['failures'], f"{row['R']:.8f}", f"{row['dqi_cost']:.6e}", f"{row['dqi_factor']:.6f}",
              {k: f'{s:.6f}' for k, s in row['score'].items()}, f"{row['score_ratio_vs_0']:.6f}")
    print('P(k)', [round(p, 4) for p in pk], 'P(>=1)', round(1 - pk[0], 4), 'P(>=3)', round(1 - sum(pk[:3]), 5))


if __name__ == '__main__':
    main(sys.argv[1])

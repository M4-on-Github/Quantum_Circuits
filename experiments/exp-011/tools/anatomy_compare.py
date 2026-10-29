"""Compares the kernel anatomy of our exp-011 build (from its .kmx text) with exp-005's 889Q measurement.

Usage: python -I -B anatomy_compare.py <repo root> <out.json>

Inputs (all produced by our own analysis scripts from the .kmx text; nothing in the circuit is executed):
  experiments/exp-011/out/anatomy/skeleton.npz, semantics_restart_gates.npz, fingerprint_search.json, tag_count.json
  experiments/exp-005/out/skeleton.npz, semantics_restart_gates.npz, fingerprint_search.json; exp-005 results.json
Unit counting is exp-005 make_results.py's rule: restart-mode bipartite components with |A| >= 12; a component of
n Toffoli is n/42 GF(2^12) units if 42 | n, else n/99 GF(2^24) units if 99 | n, else 'other'.
"""
import collections
import json
import sys
from pathlib import Path

import numpy as np


def units_and_hist(gates_npz):
    g = np.load(gates_npz)
    comp, A, B, bip = g['comp'], g['compA'], g['compB'], g['bip']
    sizes = collections.Counter(comp[comp >= 0].tolist())
    wid = {}
    for i in np.nonzero(comp >= 0)[0]:
        wid.setdefault(int(comp[i]), (int(A[i]), int(B[i]), bool(bip[i])))
    hist = collections.defaultdict(collections.Counter)
    units = collections.Counter()
    for cid, n in sizes.items():
        a, b, bp = wid[cid]
        if not (bp and a >= 12):
            continue
        hist[f'{a}x{b}'][n] += 1
        if n % 42 == 0:
            units['gf2^12_product_42'] += n // 42
        elif n % 99 == 0:
            units['gf2^24_product_99'] += n // 99
        else:
            units['other_toffoli'] += n
    hist = {k: {str(n): c for n, c in sorted(v.items(), key=lambda kv: -kv[1])} for k, v in
            sorted(hist.items(), key=lambda kv: -sum(n * c for n, c in kv[1].items()))}
    kinds = collections.Counter(g['kind'].tolist())
    return dict(units), hist, {int(k): int(v) for k, v in sorted(kinds.items())}, int(len(comp))


def skeleton_summary(npz):
    s = np.load(npz)
    meta = json.loads(str(s['meta']))
    paths = meta['paths'] if isinstance(meta, dict) and 'paths' in meta else None
    out = dict(toffoli_like=int(len(s['op'])), op_counts={int(k): int(v) for k, v in
                                                           collections.Counter(s['op'].tolist()).items()},
               conditioned=int((s['cond'] > 0).sum()), hmr=int(len(s['hmr_line'])))
    if paths is not None:
        top = collections.Counter(paths[i].split('/')[0] for i in s['path'].tolist())
        out['by_top_tag'] = dict(sorted(top.items()))
    return out


def main():
    repo = Path(sys.argv[1]).resolve()
    a11 = repo / 'experiments' / 'exp-011' / 'out' / 'anatomy'
    a05 = repo / 'experiments' / 'exp-005' / 'out'
    r05 = json.loads((repo / 'experiments' / 'exp-005' / 'results.json').read_text())
    u11, h11, k11, n11 = units_and_hist(a11 / 'semantics_restart_gates.npz')
    u05, h05, k05, n05 = units_and_hist(a05 / 'semantics_restart_gates.npz')
    assert u05 == r05['c010']['product_units_restart_mode'], (u05, r05['c010']['product_units_restart_mode'])
    fp11 = json.loads((a11 / 'fingerprint_search.json').read_text())
    tc = json.loads((a11 / 'tag_count.json').read_text())
    out = dict(
        exp011=dict(skeleton=skeleton_summary(a11 / 'skeleton.npz'), units_restart=u11,
                    kernel_hist_restart=h11, kinds_restart=k11, fingerprint=fp11),
        exp005=dict(skeleton=skeleton_summary(a05 / 'skeleton.npz'), units_restart=u05,
                    kernel_hist_restart=h05, kinds_restart=k05,
                    fingerprint=json.loads((a05 / 'fingerprint_search.json').read_text())),
        unit_ratio={k: (u11.get(k, 0) / u05[k] if u05.get(k) else None) for k in sorted(set(u11) | set(u05))},
        tag_count_total=tc['total_toffoli_like'], tag_count_conditioned=tc['conditioned_toffoli_like'],
        tag_count_n_lines=tc['n_lines'],
        tag_instance_histograms_exp011=tc['instance_histograms'],
        tag_instance_histograms_exp005=r05['accounting']['tag_instance_histograms'],
    )
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(units11=u11, units05=u05, ratio=out['unit_ratio'],
                          fp11={k: v['hits'] for k, v in fp11['searches'].items()},
                          skel11=out['exp011']['skeleton'], skel05=out['exp005']['skeleton']), indent=1))


if __name__ == '__main__':
    main()

"""Measure a (downloaded) invsqrt circuit through kickmix only: stats, registers, op histogram, .kmx dump.

Usage: python -I -B analyze_public.py <circuit.kmb> <out_dir>
"""
import collections, json, pathlib, sys
import kickmix as km

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
c = km.Circuit.from_file(str(src), format='kmb')
st = c.operation_statistics()
info = {'num_qubits': c.num_qubits, 'num_ops': len(c), 'registers': {k: [repr(e) for e in v] for k, v in c.register_data.items()},
        'num_toffoli_like': st.num_toffoli_like, 'num_t_like': st.num_t_like,
        'num_z_pow_l4': st.num_z_pow(min_clifford_hierarchy_level=4),
        'reaction_depth': c.reaction_depth()}
info['stats_attrs'] = [a for a in dir(st) if not a.startswith('_')]
kmx = out / (src.stem + '.kmx')
c.to_file(str(kmx), format='kmx')
hist = collections.Counter()
for line in open(kmx, encoding='utf-8'):
    t = line.split()
    if t:
        hist[t[0] + (' if' if ' if ' in line else '')] += 1
info['kmx_op_hist'] = dict(hist.most_common())
print(json.dumps(info, indent=1))

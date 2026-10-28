"""Summarise a kmx_value_sim.py JSON: live-qubit profile and Toffolis per line window."""
import json, sys
r = json.load(open(sys.argv[1]))
win = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
prof = r['profile']; tl = r['tof_lines']
import collections
mx = collections.defaultdict(int); tof = collections.defaultdict(float); st = collections.defaultdict(int)
for ln, live in prof:
    mx[ln // win] = max(mx[ln // win], live)
for ln, op, f in tl:
    tof[ln // win] += f; st[ln // win] += 1
for k in sorted(set(mx) | set(tof)):
    print(f'{k*win:6d}-{(k+1)*win:6d}  live<= {mx.get(k,0):3d}  tof_exec {tof.get(k,0):8.2f}  static {st.get(k,0):4d}')
print('zpow lines', [z[0] for z in r['zpow_lines']])

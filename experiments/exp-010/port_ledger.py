"""exp-010: per-register width ledger of the src/invsqrt port, without changing the emitted circuit.

Usage: python -I -B experiments/exp-010/port_ledger.py <config.json> <work_dir> <out_dir>

The kickmix CircuitBuilder that src/invsqrt/build.build_hsplit uses is wrapped in a
recording proxy (in this process only: `build.B` is replaced by a subclass whose builder
is the proxy). Every call is forwarded unchanged. The proxy:
  * names every allocation by its call site in build.py (x, f1, flags, L, H, T, C2, pad,
    const, ext, guard, carry, counter, ptemp, thermo, onehot, unnorm_anc);
  * at every call records the builder's num_allocated_qubits, so kickmix-internal ancillas
    (allocated inside kickmix calls such as unary_iteration) show up as total - named;
  * records which named registers each gate touches, per stage label (build.B.label) and
    per sub-stage (row i / fold idx / high add, plus the adder width n).
generate.run is then called as in exp-008 (fit and calibration loaded from <work_dir>,
which must hold our own exp-008 cache), so the raw and final SHA-256 can be compared with
exp-008's c97569f5... (raw) and ff629b09... (exact pass on).

Writes <out_dir>/port_ledger.json and <out_dir>/port_ledger.kmb.
"""
import collections
import json
import linecache
import pathlib
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

# call-site names: (function, left-hand side) -> register name (or a list, one per qubit)
SITE = {
    ('add_ip', 'c0'): 'carry',
    ('add', 'carries'): 'carry',
    ('fused_phase', 'z'): 'ptemp',
    ('mdel', 'q0'): 'onehot',
    ('mdel', 'q1'): 'onehot',
    ('mdel', 'n'): 'onehot',
    ('win_step', 'cq'): 'counter',
    ('build_hsplit', 'x'): 'x',
    ('build_hsplit', 'f1, f2, f4, f8, f16'): ['f1', 'flags', 'flags', 'flags', 'flags'],
    ('thermo_compute', 'th'): 'thermo',
    ('build_hsplit', 'Lr'): 'L',
    ('build_hsplit', 'Hr'): 'H',
    ('build_hsplit', 'Tr'): 'T',
    ('build_hsplit', 'C2r'): 'C2',
    ('build_hsplit', 'pad'): 'pad',
    ('build_hsplit', 'cq'): 'const',
    ('build_hsplit', 'ext'): 'ext',
    ('build_hsplit', 'gA'): 'guard',
    ('build_hsplit', 'nf1'): 'f1',
    ('build_hsplit', 'anc'): 'unnorm_anc',
}
NON_GATES = {'alloc_qubits', 'alloc_bits', 'free', 'create_quantum_register', 'create_classical_register',
             'finish_circuit', 'unary_iteration', 'num_allocated_qubits', 'num_free_qubits', 'max_qubits',
             'set_max_qubits', 'debug_print', 'mark', 'info_tag', 'push_condition', 'pop_condition'}


def main(cfg_path, work, out_dir):
    import kickmix as km
    from invsqrt import build as Bd
    from invsqrt import generate as G

    def qids(o, acc):
        if isinstance(o, km.q):
            acc.append(o.id)
        elif isinstance(o, km.array):
            for e in o:
                if isinstance(e, km.q):
                    acc.append(e.id)
        elif isinstance(o, (list, tuple)):
            for e in o:
                qids(e, acc)
        return acc

    class Rec:
        def __init__(self, inner, owner):
            object.__setattr__(self, '_b', inner)
            object.__setattr__(self, '_o', owner)
            object.__setattr__(self, 'live', {})          # qid -> name
            object.__setattr__(self, 'seq', 0)
            object.__setattr__(self, 'events', [])        # alloc/free time series
            object.__setattr__(self, 'best', {})          # (label, sub) -> peak record
            object.__setattr__(self, 'touch', collections.defaultdict(collections.Counter))
            object.__setattr__(self, 'touch_sub', collections.defaultdict(collections.Counter))
            object.__setattr__(self, 'tof', collections.Counter())
            object.__setattr__(self, 'sub_order', [])

        # ---- context
        def _sub(self):
            f = sys._getframe(2)
            parts = []
            n = None
            while f is not None:
                co = f.f_code.co_name
                loc = f.f_locals
                if co in ('add', 'add_ip') and n is None and 'n' in loc:
                    n = loc['n']
                if co == 'row' and 'i' in loc:
                    parts.append(f'row{loc["i"]}')
                elif co == 'fold' and 'idx' in loc:
                    parts.append(f'fold{loc["idx"]}')
                elif co == 'sd_step':
                    if not any(p.startswith('row') for p in parts) and n is not None:
                        parts.append('high')
                    break
                elif co in ('win_step', 'build_hsplit', 'fused_phase', 'mdel', 'thermo_compute', 'norm'):
                    break
                f = f.f_back
            s = '/'.join(reversed(parts))
            if n is not None:
                s += f' add n={n}'
            return s

        def _snap(self, sub=None):
            o = object.__getattribute__(self, '_o')
            b = object.__getattribute__(self, '_b')
            tot = b.num_allocated_qubits
            label = o.label
            if sub is None:
                sub = self._sub()
            key = (label, sub)
            best = object.__getattribute__(self, 'best')
            if key not in best:
                self.sub_order.append(key)
            if key not in best or tot > best[key]['total']:
                c = collections.Counter(self.live.values())
                best[key] = {'total': tot, 'named': sum(c.values()), 'internal': tot - sum(c.values()),
                             'regs': dict(sorted(c.items())), 'seq': self.seq}
            return tot

        # ---- allocation
        def _name(self, k):
            f = sys._getframe(2)
            co = f.f_code.co_name
            line = linecache.getline(f.f_code.co_filename, f.f_lineno).strip()
            lhs = line.split('=')[0].strip() if '=' in line else ''
            nm = SITE.get((co, lhs))
            if nm is None:
                raise RuntimeError(f'unnamed allocation at {co}:{f.f_lineno}: {line}')
            return nm if isinstance(nm, list) else [nm] * k

        def _record_alloc(self, r, names):
            qs = qids(r, [])
            for q, nm in zip(qs, names):
                assert q not in self.live
                self.live[q] = nm
            object.__setattr__(self, 'seq', self.seq + 1)
            self._ev('alloc', names[0] if names else '?', len(qs))

        def _ev(self, kind, nm, k):
            o = object.__getattribute__(self, '_o')
            c = collections.Counter(self.live.values())
            sub = self._sub_ev()
            self.events.append({'seq': self.seq, 'kind': kind, 'reg': nm, 'k': k, 'label': o.label, 'sub': sub,
                                'total': object.__getattribute__(self, '_b').num_allocated_qubits,
                                'regs': dict(sorted(c.items()))})
            self._snap(sub)

        def _sub_ev(self):
            # same as _sub but called one frame deeper
            f = sys._getframe(3)
            parts = []
            n = None
            while f is not None:
                co = f.f_code.co_name
                loc = f.f_locals
                if co in ('add', 'add_ip') and n is None and 'n' in loc:
                    n = loc['n']
                if co == 'row' and 'i' in loc:
                    parts.append(f'row{loc["i"]}')
                elif co == 'fold' and 'idx' in loc:
                    parts.append(f'fold{loc["idx"]}')
                elif co == 'sd_step':
                    if not any(p.startswith('row') for p in parts) and n is not None:
                        parts.append('high')
                    break
                elif co in ('win_step', 'build_hsplit', 'fused_phase', 'mdel', 'thermo_compute', 'norm'):
                    break
                f = f.f_back
            s = '/'.join(reversed(parts))
            if n is not None:
                s += f' add n={n}'
            return s

        def alloc_qubits(self, k):
            names = self._name(k)
            r = object.__getattribute__(self, '_b').alloc_qubits(k)
            self._record_alloc(r, names)
            return r

        def create_quantum_register(self, k, name=None):
            names = self._name(k)
            r = object.__getattribute__(self, '_b').create_quantum_register(k, name=name)
            self._record_alloc(r, names)
            return r

        def free(self, arr):
            qs = qids(arr, [])
            nm = self.live.get(qs[0], '?') if qs else 'bits'
            r = object.__getattribute__(self, '_b').free(arr)
            for q in qs:
                del self.live[q]
            if qs:
                object.__setattr__(self, 'seq', self.seq + 1)
                self._ev('free', nm, len(qs))
            return r

        def __getattr__(self, name):
            attr = getattr(object.__getattribute__(self, '_b'), name)
            if name in NON_GATES or not callable(attr):
                if name == 'unary_iteration':
                    return attr
                return attr

            def gate(*a, **kw):
                r = attr(*a, **kw)
                o = object.__getattribute__(self, '_o')
                qs = qids(list(a) + list(kw.values()), [])
                live = self.live
                sub = self._sub()
                for q in qs:
                    nm = live.get(q, 'internal')
                    self.touch[o.label][nm] += 1
                    self.touch_sub[(o.label, sub)][nm] += 1
                if name in ('ccx', 'cswap', 'init_and', 'ccz'):
                    self.tof[o.label] += 1
                self._snap(sub)
                return r
            return gate

    recs = []

    class RB(Bd.B):
        def __init__(self):
            super().__init__()
            self.b = Rec(self.b, self)
            recs.append(self.b)

    Bd.B = RB
    with open(cfg_path, encoding='utf-8') as f:
        cfg = json.load(f)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    res = G.run(cfg, work, str(out_dir / 'port_ledger.kmb'))
    build_s = time.time() - t0
    assert len(recs) == 1
    R = recs[0]

    # ---- per stage
    labels = []
    for lab, _ in R.sub_order:
        if lab not in labels:
            labels.append(lab)
    stages = {}
    for lab in labels:
        keys = [k for k in R.sub_order if k[0] == lab]
        pk = max(keys, key=lambda k: R.best[k]['total'])
        rec = R.best[pk]
        touched = set(R.touch[lab])
        idle_stage = sorted(r for r in rec['regs'] if r not in touched)
        tsub = set(R.touch_sub.get(pk, {}))
        idle_sub = sorted(r for r in rec['regs'] if r not in tsub)
        stages[lab] = {'peak': rec['total'], 'peak_sub': pk[1], 'regs_at_peak': rec['regs'],
                       'internal_at_peak': rec['internal'],
                       'idle_in_stage_at_peak': idle_stage,
                       'idle_qubits_in_stage_at_peak': sum(rec['regs'][r] for r in idle_stage),
                       'idle_in_peak_substage': idle_sub,
                       'idle_qubits_in_peak_substage': sum(rec['regs'][r] for r in idle_sub),
                       'touched_in_stage': dict(sorted(R.touch[lab].items())),
                       'toffoli_like_calls': R.tof[lab],
                       'n_substages_at_peak': sum(1 for k in keys if R.best[k]['total'] == rec['total'])}
    subs = [{'label': k[0], 'sub': k[1], **R.best[k],
             'touched': dict(sorted(R.touch_sub.get(k, {}).items()))} for k in R.sub_order]
    out = {
        'config': cfg_path, 'work': work, 'build_seconds': round(build_s, 1),
        'raw_sha256': res['raw']['sha256'], 'final_sha256': res['final']['sha256'],
        'raw_report': {k: v for k, v in res['raw'].items()},
        'final_report': {k: v for k, v in res['final'].items()},
        'windows': res['windows'],
        'generator_peak': res['raw'].get('peak'),
        'stages': stages,
        'substages': subs,
        'events': R.events,
    }
    with open(out_dir / 'port_ledger.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, default=str)
    print('raw', out['raw_sha256'], 'final', out['final_sha256'], f'{build_s:.1f}s')
    for lab, s in stages.items():
        print(f"{lab:9s} peak {s['peak']:3d} at '{s['peak_sub']}' regs {s['regs_at_peak']} internal {s['internal_at_peak']}"
              f" idle(stage) {s['idle_in_stage_at_peak']}={s['idle_qubits_in_stage_at_peak']}")


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(*sys.argv[1:4])

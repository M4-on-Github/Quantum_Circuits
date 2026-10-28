"""Streaming per-subroutine Toffoli accounting for kickmix .kmx text circuits.

Reads a .kmx file line by line (constant memory apart from the tallies) and
attributes every Toffoli-like gate (CCX, CCZ, CSWAP) to the stack of
`INFO_TAG "@enter:<name>"` / `"@exit:<name>"` marks that encloses it. kickmix
emits such marks for its own arithmetic (gf_mul, c_gf_mul, gf_inverse_chain,
gf_div, ...) and `CircuitBuilder.mark(...)` emits them for user code.

It also tracks the classical condition stack (`PUSH_CONDITION if bK` /
`POP_CONDITION`, plus inline `... if bK`) so that conditioned Toffolis can be
reported separately, together with how each condition bit was last defined
(the BIT_STORE1 sources since its last BIT_STORE0, or an HMR measurement).
That is what is needed to turn static counts into expected per-shot counts.

Usage:
    python src/kmx_tag_count.py circuit.kmx out.json
"""

from __future__ import annotations

import collections
import json
import sys

TOFFOLI_LIKE = {'CCX': 3, 'CCZ': 3, 'CSWAP': 3}


def count(path: str) -> dict:
    stack: list[str] = []          # open tag names
    inst_tof: list[int] = []       # inclusive Toffoli count of each open tag instance
    cond_stack: list[str] = []     # condition bits currently pushed
    by_path = collections.Counter()            # full path -> Toffolis
    by_path_cond = collections.Counter()       # (full path, cond tuple) -> Toffolis
    inst_hist = collections.defaultdict(collections.Counter)  # tag -> {inclusive tof: n instances}
    bit_def: dict[str, tuple] = {}             # bit -> definition
    push_defs = collections.Counter()          # definition shape at each PUSH -> n pushes
    cur_def: list[tuple] = []                  # definition of each pushed condition
    reg_bits: dict[str, str] = {}              # bit -> 'Ename[idx]'
    reg_members = collections.defaultdict(list)
    pending_reg: dict[str, list] = collections.defaultdict(list)
    op_counts = collections.Counter()

    def describe(d: tuple) -> dict:
        # Shape of a condition-bit definition: which registers feed the OR, and
        # how many bits of each (register names collapsed to their letter prefix).
        if d[0] != 'or_of':
            return {'kind': d[0]}
        regs = collections.Counter(reg_bits.get(b, b).split('[')[0] for b in d[1])
        prefixes = collections.Counter(''.join(ch for ch in r if not ch.isdigit()) for r in regs)
        return {'kind': 'or_of', 'n_sources': len(d[1]), 'n_registers': len(regs),
                'bits_per_register': sorted(set(regs.values())),
                'register_prefixes': dict(prefixes)}

    total_tof = 0
    cond_tof = 0
    n_lines = 0

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            n_lines += 1
            if not line or line[0] == '#':
                continue
            parts = line.split()
            if not parts:
                continue
            op = parts[0]
            op_counts[op] += 1
            if op == 'INFO_TAG':
                tag = line.split('"', 2)[1]
                if tag.startswith('@enter:'):
                    stack.append(tag[7:])
                    inst_tof.append(0)
                elif tag.startswith('@exit:'):
                    name = tag[6:]
                    if not stack or stack[-1] != name:
                        raise ValueError(f'line {n_lines}: exit {name} does not match {stack[-1:]}')
                    stack.pop()
                    t = inst_tof.pop()
                    inst_hist[name][t] += 1
                continue
            if op in TOFFOLI_LIKE:
                args = parts[1:]
                inline = None
                if 'if' in args:
                    k = args.index('if')
                    inline = args[k + 1:]
                    args = args[:k]
                n = len(args) // TOFFOLI_LIKE[op]
                total_tof += n
                for i in range(len(inst_tof)):
                    inst_tof[i] += n
                key = '/'.join(stack)
                by_path[key] += n
                conds = tuple(cond_stack) + (tuple(inline) if inline else ())
                if conds:
                    cond_tof += n
                    sig = json.dumps([describe(d) for d in cur_def]
                                     + [{'kind': 'inline', 'bits': inline}] * bool(inline),
                                     sort_keys=True)
                    by_path_cond[(key, sig)] += n
                continue
            if op == 'PUSH_CONDITION':
                bit = parts[2]
                cond_stack.append(bit)
                d = bit_def.get(bit, ('undefined',))
                cur_def.append(d)
                push_defs[json.dumps(describe(d), sort_keys=True)] += 1
                continue
            if op == 'POP_CONDITION':
                cond_stack.pop()
                cur_def.pop()
                continue
            if op == 'BIT_STORE0':
                for b in parts[1:]:
                    if b == 'if':
                        break
                    bit_def[b] = ('store0',)
                continue
            if op == 'BIT_STORE1':
                if 'if' in parts:
                    k = parts.index('if')
                    tgts, srcs = parts[1:k], parts[k + 1:]
                else:
                    tgts, srcs = parts[1:], []
                for b in tgts:
                    prev = bit_def.get(b, ('store0',))
                    if prev[0] == 'or_of':
                        bit_def[b] = ('or_of', prev[1] + tuple(srcs))
                    elif srcs:
                        bit_def[b] = ('or_of', tuple(srcs))
                    else:
                        bit_def[b] = ('store1',)
                continue
            if op == 'HMR':
                # HMR q b: X-basis measurement into bit b (random outcome).
                for b in parts[1:]:
                    if b.startswith('b'):
                        bit_def[b] = ('measured',)
                continue
            if op == 'APPEND_TO_REGISTER':
                pending_reg[parts[2]].append(parts[1])
                continue
            if op == 'REGISTER':
                rid = parts[1]
                name = line.split('"')[1] if '"' in line else rid
                for i, b in enumerate(pending_reg.get(rid, [])):
                    reg_bits[b] = f'{name}[{i}]'
                continue

    if stack:
        raise ValueError(f'unclosed tags at EOF: {stack}')

    cond_summary = collections.defaultdict(lambda: {'toffolis': 0, 'definitions': collections.Counter()})
    for (key, sig), n in by_path_cond.items():
        top = key.split('/')[0] if key else ''
        cond_summary[top]['toffolis'] += n
        cond_summary[top]['definitions'][sig] += n

    return {
        'file': path,
        'n_lines': n_lines,
        'total_toffoli_like': total_tof,
        'conditioned_toffoli_like': cond_tof,
        'op_counts': dict(op_counts),
        'by_path': dict(sorted(by_path.items(), key=lambda kv: -kv[1])),
        'instance_histograms': {k: {str(t): c for t, c in sorted(v.items())}
                                for k, v in sorted(inst_hist.items())},
        'conditioned_by_top_mark': {k: {'toffolis': v['toffolis'],
                                        'definitions': dict(v['definitions'])}
                                    for k, v in cond_summary.items()},
        'push_condition_definitions': dict(push_defs),
        'conditioned_by_path': {f'{k} | {c}': n for (k, c), n in
                                sorted(by_path_cond.items(), key=lambda kv: -kv[1])[:200]},
    }


def main() -> None:
    res = count(sys.argv[1])
    with open(sys.argv[2], 'w') as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ('n_lines', 'total_toffoli_like',
                                          'conditioned_toffoli_like')}))


if __name__ == '__main__':
    main()

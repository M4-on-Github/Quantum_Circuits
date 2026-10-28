"""Empirical per-shot Toffoli accounting by tag path, from a .kmx circuit.

The verifier's T is the mean number of Toffoli-like gates that a shot executes. In kickmix,
classical control (`PUSH_CONDITION if bK` ... `POP_CONDITION`, or an inline `... if bK`) is
the only thing that changes what a shot executes. A Toffoli outside every condition runs
exactly once in every shot. So the per-shot count of a tag path is its unconditioned static
count plus the executed count of its conditioned Toffolis.

This module streams a .kmx, cuts it into segments, and simulates the segments one after another
on one `km.Simulator(counting_operations=True)`, reading and clearing the counters after each
segment. Each outermost conditioned region that holds Toffolis becomes its own segment, and so
do runs of consecutive such regions whose Toffolis share one tag path. Everything in between
becomes an unconditioned segment.

Attribution:
- In an unconditioned segment every Toffoli is executed once per shot, so each path gets its
  static count. The measured count is checked against this.
- In a conditioned segment the executed Toffolis go to the segment's paths in proportion to
  their static counts. That is exact when the segment has one path, or when it is a single
  region whose Toffolis all sit directly under its one outer condition (they then run in the
  same shots). The module reports the executed mass in the remaining segments ("inexact").

Usage as a library:
    sim = km.Simulator(batch_size=N, counting_operations=True, seed=S)
    sim.use_same_registers_as(circuit); <write inputs>
    res = run_segmented(kmx_path, sim)
The final simulator state equals that after `sim.do(circuit)`; the caller checks this.
"""

from __future__ import annotations

import collections
import time

TOFFOLI_LIKE = {'CCX': 3, 'CCZ': 3, 'CSWAP': 3}
DECL = ('REGISTER', 'APPEND_TO_REGISTER')


def _tof_in_line(parts: list[str]) -> int:
    args = parts[1:]
    if 'if' in args:
        args = args[:args.index('if')]
    return len(args) // TOFFOLI_LIKE[parts[0]]


def run_segmented(kmx_path: str, sim, km=None, progress_every_s: float = 60.0) -> dict:
    if km is None:
        import kickmix as km
    stack: list[str] = []
    depth = 0                      # condition depth
    run_lines: list[str] = []      # pending unconditioned text
    run_static = collections.Counter()
    reg_lines: list[str] = []      # current outermost conditioned region
    reg_static = collections.Counter()
    reg_uniform = [True]           # no Toffoli of the region sits under a nested/inline condition
    cseg_uniform = [True]
    cseg_lines: list[str] = []     # pending conditioned segment (merged regions)
    cseg_static = collections.Counter()

    static_uncond = collections.Counter()
    static_cond = collections.Counter()
    exec_cond = collections.Counter()      # path -> executed Toffolis summed over shots
    inexact_exec = 0.0
    n_seg = {'uncond': 0, 'cond': 0, 'cond_multi_path': 0}
    uncond_mismatch = []
    total_exec = 0
    shots = sim.batch_size
    t0 = last = time.time()

    def execute(lines: list[str]) -> int:
        nonlocal total_exec
        if not lines:
            return 0
        sim.clear_operation_statistics()
        sim.do(km.Circuit('\n'.join(lines)))
        n = int(sim.operation_statistics().num_toffoli_like)
        total_exec += n
        return n

    def flush_run() -> None:
        if not run_lines:
            return
        n = execute(run_lines)
        exp = sum(run_static.values()) * shots
        if n != exp and len(uncond_mismatch) < 20:
            uncond_mismatch.append({'expected': exp, 'measured': n})
        static_uncond.update(run_static)
        n_seg['uncond'] += 1
        run_lines.clear()
        run_static.clear()

    def flush_cseg() -> None:
        nonlocal inexact_exec
        if not cseg_lines:
            return
        n = execute(cseg_lines)
        tot = sum(cseg_static.values())
        for p, s in cseg_static.items():
            exec_cond[p] += n * s / tot
        static_cond.update(cseg_static)
        n_seg['cond'] += 1
        if len(cseg_static) > 1:
            n_seg['cond_multi_path'] += 1
            if not cseg_uniform[0]:
                inexact_exec += n
        cseg_lines.clear()
        cseg_static.clear()
        cseg_uniform[0] = True

    def close_region() -> None:
        # An outermost conditioned region (or one inline-conditioned line) has ended.
        if not reg_static:
            run_lines.extend(reg_lines)           # no Toffolis: keep it in the run
        else:
            mergeable = (cseg_lines and not run_static and len(reg_static) == 1
                         and len(cseg_static) == 1 and set(reg_static) == set(cseg_static))
            if not mergeable:
                flush_cseg()
                flush_run()
            elif run_lines:                       # Toffoli-free text between merged regions
                cseg_lines.extend(run_lines)
                run_lines.clear()
            # A lone uniform region is exact even with several paths (one condition gates all).
            # Merged regions are single-path by construction.
            cseg_uniform[0] = (not cseg_lines) and reg_uniform[0] or (cseg_uniform[0] and len(reg_static) == 1)
            cseg_lines.extend(reg_lines)
            cseg_static.update(reg_static)
        reg_lines.clear()
        reg_static.clear()
        reg_uniform[0] = True

    with open(kmx_path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.rstrip('\n')
            if not s or s[0] == '#':
                continue
            parts = s.split()
            op = parts[0]
            if op in DECL:
                continue
            if op == 'INFO_TAG':
                tag = s.split('"', 2)[1]
                if tag.startswith('@enter:'):
                    stack.append(tag[7:])
                elif tag.startswith('@exit:'):
                    stack.pop()
                (reg_lines if depth else run_lines).append(s)
                continue
            if op == 'PUSH_CONDITION':
                depth += 1
                reg_lines.append(s)
                continue
            if op == 'POP_CONDITION':
                depth -= 1
                reg_lines.append(s)
                if depth == 0:
                    close_region()
                continue
            if op in TOFFOLI_LIKE:
                n = _tof_in_line(parts)
                path = '/'.join(stack)
                inline = 'if' in parts
                if depth:
                    reg_lines.append(s)
                    reg_static[path] += n
                    if depth > 1 or inline:
                        reg_uniform[0] = False
                elif inline:
                    reg_lines.append(s)
                    reg_static[path] += n
                    close_region()
                else:
                    run_lines.append(s)
                    run_static[path] += n
            else:
                (reg_lines if depth else run_lines).append(s)
            # If a cond segment is pending and unconditioned Toffolis arrive, flush order matters:
            # the cond segment must execute before the run that follows it.
            if run_static and cseg_lines:
                pending = run_lines[:]
                pstatic = run_static.copy()
                run_lines.clear()
                run_static.clear()
                flush_cseg()
                run_lines.extend(pending)
                run_static.update(pstatic)
            if time.time() - last > progress_every_s:
                last = time.time()
                print(f'  segsim {time.time() - t0:.0f}s segments {n_seg}', flush=True)
    if depth:
        raise ValueError('unbalanced conditions at EOF')
    flush_cseg()
    flush_run()

    paths = set(static_uncond) | set(static_cond)
    per_shot = {p: static_uncond[p] + exec_cond[p] / shots for p in paths}
    return {
        'shots': shots,
        'segments': n_seg,
        'wall_s': round(time.time() - t0, 1),
        'total_executed_toffoli': total_exec,
        'per_shot_total': total_exec / shots,
        'inexact_executed_fraction': inexact_exec / total_exec if total_exec else 0.0,
        'uncond_segment_mismatches': uncond_mismatch,
        'static_uncond_by_path': dict(static_uncond),
        'static_cond_by_path': dict(static_cond),
        'per_shot_by_path': dict(sorted(per_shot.items(), key=lambda kv: -kv[1])),
    }

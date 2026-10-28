"""Relabelled Toffoli-skeleton patterns and template search (shared by the exp-005 analysis scripts).

A window of Toffoli-like gates is relabelled by replacing every qubit with the index of its first
appearance inside the window (-1 stays -1, for two-operand gates). Two windows match when op codes and
relabelled operands are identical, i.e. the same gate structure on possibly different qubits.
"""
import numpy as np


def relabel(op, a, b, c):
    m = {}
    out = []
    for o, x, y, z in zip(op, a, b, c):
        t = [int(o)]
        for q in (x, y, z):
            q = int(q)
            if q < 0:
                t.append(-1)
            else:
                if q not in m:
                    m[q] = len(m)
                t.append(m[q])
        out.append(tuple(t))
    return tuple(out)


def prefix_key(op, a, b, c, k=3):
    """Vectorised key of the first k gates of every window: op codes and operand equality pattern."""
    n = len(op) - k + 1
    cols = []
    for j in range(k):
        cols.append(op[j:j + n].astype(np.int64))
    ops3 = [a, b, c]
    operands = [ops3[r][j:j + n].astype(np.int64) for j in range(k) for r in range(3)]
    eq_bits = np.zeros(n, np.int64)
    bit = 0
    for u in range(len(operands)):
        for v in range(u + 1, len(operands)):
            eq_bits |= (operands[u] == operands[v]).astype(np.int64) << bit
            bit += 1
    key = eq_bits
    for j, col in enumerate(cols):
        key = key * 4 + col
    return key


def find(template, op, a, b, c, non_overlapping=True):
    """Start indices where the relabelled template occurs in the skeleton arrays."""
    L = len(template)
    if L == 0 or L > len(op):
        return []
    k = min(3, L)
    keys = prefix_key(op, a, b, c, k)
    t_op = np.array([g[0] for g in template[:k]])
    t_a = np.array([g[1] for g in template[:k]])
    t_b = np.array([g[2] for g in template[:k]])
    t_c = np.array([g[3] for g in template[:k]])
    tkey = prefix_key(t_op, t_a, t_b, t_c, k)[0]
    cand = np.nonzero(keys[: len(op) - L + 1] == tkey)[0]
    hits = []
    last_end = -1
    for i in cand:
        if non_overlapping and i < last_end:
            continue
        if relabel(op[i:i + L], a[i:i + L], b[i:i + L], c[i:i + L]) == template:
            hits.append(int(i))
            last_end = i + L
    return hits

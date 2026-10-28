"""Streams a (possibly .xz) .kmx and writes a compact Toffoli skeleton for structural analysis.

Usage: python -I kmx_skeleton.py <dqi.kmx[.xz]> <out.npz>

Text parsing only; nothing in the input is executed. Per Toffoli-like gate (CCX, CCZ, CSWAP) it records
the line number, op code, three qubit operands, tag-path id, condition depth and the number of
CX/SWAP lines since the previous Toffoli-like gate. It also records HMR lines, register membership of
every qubit, and the list of tag paths. Totals per op are kept as a check against operation_statistics.
"""
import json
import lzma
import sys
from pathlib import Path

import numpy as np

TOF = {'CCX': 0, 'CCZ': 1, 'CSWAP': 2}


def qid(tok: str) -> int:
    assert tok[0] == 'q', tok
    return int(tok[1:])


def main(src: str, dst: str) -> None:
    opener = lzma.open if src.endswith('.xz') else open
    reg_members: dict[str, list[int]] = {}
    reg_names: dict[str, str] = {}
    paths: list[str] = ['']
    path_id = {'': 0}
    stack: list[str] = []
    cur = 0
    cond = 0
    since = 0
    rec_line, rec_op, rec_a, rec_b, rec_c, rec_path, rec_cond, rec_gap = [], [], [], [], [], [], [], []
    hmr_line, hmr_q, hmr_path = [], [], []
    op_hist: dict[str, int] = {}
    with opener(src, 'rt', encoding='utf-8') as f:
        for ln, line in enumerate(f):
            parts = line.split()
            if not parts:
                continue
            op = parts[0]
            op_hist[op] = op_hist.get(op, 0) + 1
            if op == 'CX' or op == 'SWAP':
                since += 1
                continue
            t = TOF.get(op)
            if t is not None:
                rec_line.append(ln)
                rec_op.append(t)
                qs = [qid(p) for p in parts[1:4]]
                if len(qs) == 2:
                    qs.append(-1)
                rec_a.append(qs[0]); rec_b.append(qs[1]); rec_c.append(qs[2])
                rec_path.append(cur); rec_cond.append(cond); rec_gap.append(since)
                since = 0
                continue
            if op == 'HMR':
                hmr_line.append(ln); hmr_q.append(qid(parts[1])); hmr_path.append(cur)
            elif op == 'PUSH_CONDITION':
                cond += 1
            elif op == 'POP_CONDITION':
                cond -= 1
            elif op == 'INFO_TAG':
                tag = line.split('"', 2)[1]
                if tag.startswith('@enter:'):
                    stack.append(tag[7:])
                elif tag.startswith('@exit:'):
                    assert stack and stack[-1] == tag[6:], (ln, tag, stack[-3:])
                    stack.pop()
                else:
                    continue
                p = '/'.join(stack)
                if p not in path_id:
                    path_id[p] = len(paths)
                    paths.append(p)
                cur = path_id[p]
            elif op == 'APPEND_TO_REGISTER':
                reg_members.setdefault(parts[2], []).append(parts[1])
            elif op == 'REGISTER':
                reg_names[parts[1]] = line.split('"', 2)[1]
    qubit_reg = {}
    for r, members in reg_members.items():
        for k, m in enumerate(members):
            if m.startswith('q'):
                qubit_reg[int(m[1:])] = [reg_names.get(r, r), k]
    np.savez_compressed(
        dst, line=np.array(rec_line, np.int64), op=np.array(rec_op, np.int8),
        a=np.array(rec_a, np.int32), b=np.array(rec_b, np.int32), c=np.array(rec_c, np.int32),
        path=np.array(rec_path, np.int32), cond=np.array(rec_cond, np.int16), gap=np.array(rec_gap, np.int32),
        hmr_line=np.array(hmr_line, np.int64), hmr_q=np.array(hmr_q, np.int32), hmr_path=np.array(hmr_path, np.int32),
        meta=np.array(json.dumps({'paths': paths, 'qubit_reg': qubit_reg, 'op_hist': op_hist})))
    print(json.dumps({'toffoli_like': len(rec_line), 'paths': len(paths), 'hmr': len(hmr_line),
                      'registered_qubits': len(qubit_reg), 'op_hist': op_hist}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

"""exp-010: write a .kmx from a .kmb with kickmix's own loader (no other code touches the input).

Usage: python -I -B experiments/exp-010/to_kmx.py <in.kmb> <out.kmx>
Prints the input SHA-256, kickmix's num_qubits / Toffoli-like count and the output SHA-256.
"""
import hashlib
import sys

import kickmix as km

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    h = hashlib.sha256(open(src, 'rb').read()).hexdigest()
    c = km.Circuit.from_file(src, format='kmb')
    c.to_file(dst, format='kmx')
    st = c.operation_statistics()
    print(src, h, 'qubits', c.num_qubits, 'toffoli_like', st.num_toffoli_like)
    print(dst, hashlib.sha256(open(dst, 'rb').read()).hexdigest())

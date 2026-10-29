"""Generator for the dqi benchmark circuit (reversible RS(4095, 4025) syndrome decoder over GF(2^12)).

Lineage and licence
-------------------
pro_q2_897/ is an unmodified Apache-2.0 port of the 897-qubit decoder builder "pro-q2-897" embedded in
Agniv Banerjee's (Kaggle somejoint) public notebook "Quantum Circuits | 22.34 Local GM: 897-Qubit DQI"
(version 14 of somejoint/quantum-circuits-22-77-local-gm-889-qubit-dqi). See NOTICE for full credits,
the provenance caveat about its design lineage, and LICENSE for the licence text. MANIFEST.json pins
the SHA-256 of every ported file.

Use
---
    python -I -B src/dqi/generate.py OUT.kmb

Builds the circuit with kickmix and writes OUT.kmb plus OUT.build.json (sha256, Q, T_static, num_ops,
num_bits, seconds). The upstream build states SHA-256 b3354f60e459dcebe67910363e96498f8bb0aa7f699bc016ef962015c3732fd6.
It needs about 5 GB of memory (upstream README), so run it on a Kaggle kernel, not on a small machine.

Do not add modules here whose names could shadow the kit's: the kit puts this directory on sys.path and resolves
bare-name imports (common, decode, field, kernels, scan, ...) through it.
"""

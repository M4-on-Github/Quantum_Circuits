"""Generator for the invsqrt benchmark circuit (|x>|0> -> exp(2 pi i / sqrt(x)) |x>|0>).

Lineage and licence
-------------------
This package started as a port of the public, Apache-2.0 notebook
"VQCC invsqrt 13.94x - full source" by marsyas (Houssem Alayet),
https://www.kaggle.com/code/marsyas/vqcc-invsqrt-13-94x-full-source
(read 2026-10-28; ipynb SHA-256 4da93524...). That notebook credits, as ideas it
re-implemented: Sumit Chongder and kozykappa (signed-digit rows), anazemcev (H/L split,
exact compilation), Dmitrii Gluzdov (merged unlookup), Artem (exact-domain pass),
auqib92 (nested windows), mizeroluckygall and lightningv08 (angle calibration),
rudrabhaskar (direct polynomial phasing).

The port was re-typed from the notebook text (never executed). Changes from the
original are marked "change:" in the module docstrings. Copyright of the original
code remains with its author; it is used under the Apache License, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0).

Modules
-------
model     exact integer model of the arithmetic and phase (all legal x)
fit       per-segment coefficient tables (LP + integer neighbourhood search)
calib     LP calibration of the rotation angles against the exact model
build     the kickmix circuit builder (normalization, lookup, Horner rows, phasing)
exact     exact-domain post-pass over all legal inputs
check     kickmix simulation of a built circuit against the model
generate  end-to-end pipeline driven by a JSON config
"""

"""kickmix builder for the invsqrt circuit (the arithmetic is the one in model.py).

Stages: thermometer of leading zeros -> 5 CSWAP normalization stages -> 8-bit lookup of
(u, H, C1, C2) -> phase H (and the constant 1/2 bit) and erase H by measurement ->
step A (T = C1 - rows of C2) -> step B (L += rows of T, nested windows) -> phase L ->
uncompute B, A -> one merged measurement-based unlookup -> un-normalize with flags
cleared by HMR and conditioned multi-controlled Z.

Ported from marsyas's Apache-2.0 notebook (build.py and hsplit.py there; see the package
docstring). change: only the signed-digit + H/L-split + nested-window + measured
unlookup path of the 13.94x build is kept; Booth rows, plain rows, product temps and the
unfused shift register are dropped. The adder and stages are unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np
import kickmix as km

from . import fit as Fm
from . import model as M


@dataclass
class Opts:
    WA: int | None = None      # step A window top
    gA: int = 1                # step A guard qubits (1: offset scheme)
    mdel: bool = True          # merged measurement-based unlookup
    wins: list | None = None   # nested step-B windows [(K, rows)], outer -> inner
    wcb: list | None = None    # window counter bits
    kbig: int = 0              # in-place prefix positions for the big (non-window) rows
    qcap: int | None = None    # qubit cap for in-place adder prefixes in step B
    cap: int | None = None


class B:
    def __init__(self):
        self.b = km.CircuitBuilder()
        self.peak = (0, '')
        self.label = ''
        self.cap = None
        self.phasefix = True

    def note(self, where=''):
        n = self.b.num_allocated_qubits
        if n > self.peak[0]:
            self.peak = (n, self.label + where)

    # ---------------- adder -----------------
    def add_ip(self, srcs, tgt, cin, k):
        """tgt += srcs + cin with a k-position Cuccaro (in-place MAJ) prefix: saves k carry
        ancillas (k-1 if cin is None) for +k Toffolis. srcs[0..k-1] must be plain qubits."""
        b = self.b
        n = len(tgt)
        srcs = list(srcs) + [None] * (n - len(srcs))
        assert all(isinstance(s_, km.q) for s_ in srcs[:k]) and k < n - 1
        own = cin is None
        c0 = b.alloc_qubits(1)[0] if own else cin
        cs = [c0] + list(srcs[:k])
        for i in range(k):
            c, bb, a = cs[i], tgt[i], srcs[i]
            b.cx(a, bb); b.cx(a, c); b.ccx(c, bb, a)
        self.add(srcs[k:], list(tgt[k:]), cin=srcs[k - 1])
        for i in reversed(range(k)):
            c, bb, a = cs[i], tgt[i], srcs[i]
            b.ccx(c, bb, a); b.cx(a, c); b.cx(c, bb)
        if own:
            b.free(km.array([c0]))

    def add(self, srcs, tgt, subtract=False, cin=None, cout=None):
        """tgt += sum_i src_i 2^i + cin (mod 2^len(tgt)); with cout, the carry out of the top
        position is XORed into cout. srcs[i] is None (zero) or a qubit; repeats allowed.
        Gidney-style: carries computed with init_and and erased with del_and."""
        b = self.b
        n = len(tgt)
        srcs = list(srcs) + [None] * (n - len(srcs))
        assert len(srcs) == n
        assert all(s_ is None or isinstance(s_, km.q) for s_ in srcs)
        lo = 0
        if cin is None:
            while lo < n and srcs[lo] is None:
                lo += 1
        if lo == n:
            return
        srcs = srcs[lo:]
        tgt = list(tgt[lo:])
        n = len(tgt)
        if subtract:
            b.x(km.array(tgt))
        K = n - 1 if cout is not None else n - 2   # internal carries c_1..c_K
        K = max(K, 0)
        carries = b.alloc_qubits(K) if K else []

        def cin_of(i):
            if i == 0:
                return cin
            return carries[i - 1] if i - 1 < K else None

        for i in range(n):
            a = srcs[i]
            bb = tgt[i]
            c = cin_of(i)
            if i < K:
                dest, init = carries[i], True
            elif cout is None and i == n - 2:
                dest, init = tgt[n - 1], False
            elif cout is not None and i == n - 1:
                dest, init = cout, False
            else:
                dest = None
            if dest is None:
                if a is not None:
                    b.cx(a, bb)
                if c is not None and (cout is not None or n == 1):
                    b.cx(c, bb)
                self.note(f' add n={n}')
                continue
            if a is None:
                if init:
                    b.init_and(bb, c, dest)
                else:
                    b.ccx(bb, c, dest)
                b.cx(c, bb)
            else:
                if c is not None:
                    b.cx(c, a); b.cx(c, bb)
                if init:
                    b.init_and(a, bb, dest)
                else:
                    b.ccx(a, bb, dest)
                if c is not None:
                    b.cx(c, dest)
                if c is not None:
                    b.cx(c, a)
                b.cx(a, bb)
            self.note(f' add n={n}')
        for i in reversed(range(K)):
            bb = tgt[i]
            c = cin_of(i)
            a = srcs[i]
            if a is None:
                b.cx(c, bb)
                b.del_and(bb, c, carries[i])
                b.cx(c, bb)
            else:
                if c is not None:
                    b.cx(c, carries[i])
                b.cx(a, bb)
                if c is not None:
                    b.cx(c, a)
                b.del_and(a, bb, carries[i])
                if c is not None:
                    b.cx(c, a)
                b.cx(a, bb)
        if carries:
            b.free(carries)
        if subtract:
            b.x(km.array(tgt))


def sd_step(bb: B, x, rows, op, acc, e_of, W, guard, fwd):
    """Signed-digit rows: fwd: acc -= sum_i (2b_i-1) rd(op, e_i+1); else the exact inverse."""
    b = bb.b
    g1 = len(guard) == 1
    win = (list(acc[:W + 1]) if g1 else list(acc[:W])) + list(guard)
    high = list(acc[W + 1:]) if g1 else list(acc[W:])
    gsrc = [guard[0]] + [guard[1]] * (len(high) - 1) if len(guard) == 2 else None

    def row(i):
        e = e_of(i) + 1
        srcs = [op[p + e] if 0 <= p + e < len(op) else None for p in range(len(win))]
        assert len(op) - e <= len(win), ('window too small', len(op) - e, len(win))
        cin = op[e - 1] if 1 <= e <= len(op) else None
        if all(q is None for q in srcs) and cin is None:
            return
        ctl = x[i]
        if not fwd:
            b.x(ctl)
        for q in win:
            b.cx(ctl, q)
        bb.add(srcs, win, cin=cin)
        for q in win:
            b.cx(ctl, q)
        if not fwd:
            b.x(ctl)

    order = list(rows) if fwd else list(reversed(rows))
    if g1:
        top = acc[W]
        g = guard[0]
        if fwd:
            b.x(top); b.cx(top, g)
            for i in order:
                row(i)
            if high:
                bb.add([top], high)
                bb.add([g], high, subtract=True)
            b.x(top)
        else:
            b.x(top)
            if high:
                bb.add([g], high)
                bb.add([top], high, subtract=True)
            for i in order:
                row(i)
            b.cx(top, g); b.x(top)
        return
    if not fwd and high:
        bb.add(gsrc, high, subtract=True)
    for i in order:
        row(i)
    if fwd and high:
        bb.add(gsrc, high, subtract=False)


def fused_phase(bb: B, R, h0, angfn, flags4):
    """Phase sum_j ang(j) * bit_j(R << s), s = f2 + 2 f4 + 4 f8 + 8 f16 (s <= 10).
    R: data qubits R[0..h0] followed by 3 clean ext qubits. f2, f4 in place (CSWAP);
    f8/f16 fused: Z_j = R_j ^ f8 (R_j ^ R_{j-4}) ^ f16 (R_j ^ R_{j-8}) into one temp,
    Z_POW, then HMR with Clifford fix-up. angfn(j) -> Fraction half-turns or None."""
    b = bb.b
    f2, f4, f8, f16 = flags4
    assert len(R) == h0 + 4
    hiR = h0 + 3
    shifts = [(1, f2, h0), (2, f4, h0 + 1)]
    empty = {(1, h0), (2, h0 + 1), (2, h0)}   # targets above every earlier write are zero
    for k, f, hi in shifts:
        for i in range(hi, -1, -1):
            if (k, i) in empty:
                b.init_and(f, R[i], R[i + k]); b.cx(R[i + k], R[i])
            else:
                b.cswap(f, R[i], R[i + k])
    z = b.alloc_qubits(1)[0]
    bb.note(' fused phase')

    def term(f, j, k, act):
        qa = R[j] if j <= hiR else None
        qb = R[j - k] if 0 <= j - k <= (hiR if k == 4 else h0 + 2) else None
        if qa is None and qb is None:
            return False
        if qa is not None and qb is not None:
            b.cx(qb, qa); act(f, qa); b.cx(qb, qa)
        else:
            act(f, qa if qa is not None else qb)
        return True

    for j in range(h0 + 11):
        ex = angfn(j)
        if ex is None or ex % 2 == 0:
            continue
        b.reset(z)
        has_r = j <= hiR
        if has_r:
            b.cx(R[j], z)
        t8 = term(f8, j, 4, lambda f, q: b.ccx(f, q, z))
        t16 = term(f16, j, 8, lambda f, q: b.ccx(f, q, z))
        if not (has_r or t8 or t16):
            continue
        b.z_pow(z, ex)
        m = b.alloc_bits(1)[0]
        b.hmr(z, m)
        b.push_condition(m)
        if has_r:
            b.z(R[j])
        term(f8, j, 4, lambda f, q: b.cz(f, q))
        term(f16, j, 8, lambda f, q: b.cz(f, q))
        b.pop_condition()
        b.free(km.array([m]))
    b.free(km.array([z]))
    for k, f, hi in reversed(shifts):
        for i in range(0, hi + 1):
            if (k, i) in empty:
                b.cx(R[i + k], R[i]); b.del_and(f, R[i], R[i + k])
            else:
                b.cswap(f, R[i], R[i + k])


def mdel(b, address, groups):
    """Measurement-based unlookup fix-up for several already-measured registers sharing one
    8-bit address: applies prod_g (-1)^{m_g . table_g[addr]} with a 16-way one-hot of the low
    nibble (14 ANDs, freed by measurement) and a unary iteration over the high nibble."""
    lo, hi = list(address[:4]), list(address[4:8])
    oh = [None] * 16
    q0 = b.alloc_qubits(1)[0]
    q1 = b.alloc_qubits(1)[0]
    b.x(q0); b.cx(lo[0], q1); b.cx(q1, q0)
    oh[0], oh[1] = q0, q1
    made = []
    for j in range(1, 4):
        for e in range(1 << j):
            n = b.alloc_qubits(1)[0]
            b.init_and(oh[e], lo[j], n)
            b.cx(n, oh[e])
            oh[e + (1 << j)] = n
            made.append((j, e, n))
    with b.unary_iteration(km.array(hi)) as it:
        for v, mu in it:
            for l in range(16):
                a = v * 16 + l
                for bits, tab in groups:
                    val = int(tab[a])
                    k = 0
                    while val:
                        if val & 1:
                            b.push_condition(bits[k])
                            b.cz(mu, oh[l])
                            b.pop_condition()
                        val >>= 1
                        k += 1
    for j, e, n in reversed(made):
        b.cx(n, oh[e])
        b.del_and(oh[e], lo[j], n)
        b.free(km.array([n]))
    b.cx(q1, q0); b.cx(lo[0], q1); b.x(q0)
    b.free(km.array([q0, q1]))


def measure(b, qs):
    bits = b.alloc_bits(len(qs))
    b.hmr(km.array(list(qs)), bits)
    return bits


# ---------------------------------------------------------------- nested windows for step B
def parse_plan(spec):
    """'15:9,8,7;12:6,5,4;9:3,2,1,0' -> [(K, rows)] outer -> inner."""
    out = []
    for part in spec.split(';'):
        K, rows = part.split(':')
        out.append((int(K), [int(r) for r in rows.split(',')]))
    return out


def sim_windows(tables, prm, lay, wins, cbits):
    """Bit-exact simulation of big rows + nested windows + folds; True if L ends correct."""
    a, p, xn, bounds = Fm.domains()
    b = xn & 0x3FFF
    C0, C1, C2 = tables[a, 0], tables[a, 1], tables[a, 2]
    T = M.eval_T(C1, C2, b, prm)
    Ltrue = lay.u[a] + (M.eval_Y(C0, T, b, prm) - C0)
    LB = lay.LB
    m = lambda k: (1 << k) - 1
    L = lay.u[a].copy()
    winrows = set(r for _, rs in wins for r in rs)
    vals = {}
    for i in prm.rowsB:
        sig = 2 * ((b >> i) & 1) - 1
        vals[i] = -sig * M.rd(T, prm.eB(i) + 1)
    for i in prm.rowsB:
        if i not in winrows:
            L = (L + vals[i]) & m(LB)
    cnt = []
    for (K, rows), c in zip(wins, cbits):
        cb = np.zeros_like(L)
        for i in rows:
            v = (L & m(K)) + (cb << K) + vals[i]
            v &= m(K + c)
            L = (L & ~m(K)) | (v & m(K))
            cb = v >> K
        cnt.append(cb)
    for idx in reversed(range(len(wins))):
        K, _ = wins[idx]
        c = cbits[idx]
        sval = cnt[idx] - ((cnt[idx] >> (c - 1)) & 1) * (1 << c)   # signed
        if idx > 0:
            Kp, _ = wins[idx - 1]
            cp = cbits[idx - 1]
            t = ((L >> K) & m(Kp - K)) + (cnt[idx - 1] << (Kp - K))
            t = (t + sval) & m(Kp - K + cp)
            L = (L & ~(m(Kp - K) << K)) | ((t & m(Kp - K)) << K)
            cnt[idx - 1] = t >> (Kp - K)
        else:
            t = ((L >> K) + sval) & m(LB - K)
            L = (L & m(K)) | (t << K)
    return bool(np.array_equal(L, Ltrue))


def choose_cbits(tables, prm, lay, wins, cmax=3):
    n = len(wins)
    cb = [2] * n
    while not sim_windows(tables, prm, lay, wins, cb):
        if min(cb) >= cmax:
            return None
        cb = [c + 1 for c in cb]
    for k in range(n):
        if cb[k] > 1:
            t = list(cb)
            t[k] -= 1
            if sim_windows(tables, prm, lay, wins, t):
                cb = t
    return cb


def win_step(bb, x, prm, op, L, wins, cbits, fwd, store, kbig=0, qcap=None):
    b = bb.b

    def row(i, win, k=0):
        e = prm.eB(i) + 1
        srcs = [op[q + e] if 0 <= q + e < len(op) else None for q in range(len(win))]
        assert len(op) - e <= len(win), ('window too small', i, len(op) - e, len(win))
        cin = op[e - 1] if 1 <= e <= len(op) else None
        ctl = x[i]
        if not fwd:
            b.x(ctl)
        for q in win:
            b.cx(ctl, q)
        if qcap:
            need = b.num_allocated_qubits + len(win) - 2
            k = max(0, need - qcap)
            if k and cin is None:
                k += 1
        if k and all(isinstance(s_, km.q) for s_ in srcs[:k]) and k < len(win) - 1:
            bb.add_ip(srcs, win, cin, k)
        else:
            bb.add(srcs, win, cin=cin)
        for q in win:
            b.cx(ctl, q)
        if not fwd:
            b.x(ctl)

    winrows = set(r for _, rs in wins for r in rs)
    big = [i for i in prm.rowsB if i not in winrows]

    def fold(idx, sub):
        K, _ = wins[idx]
        cq = store[idx]
        c = len(cq)
        if idx > 0:
            Kp, _ = wins[idx - 1]
            tgt = list(L[K:Kp]) + list(store[idx - 1])
        else:
            tgt = list(L[K:])
        src = list(cq) + [cq[-1]] * (len(tgt) - c)
        bb.add(src[:len(tgt)], tgt, subtract=sub)

    if fwd:
        for i in big:
            row(i, list(L), kbig)
        for idx, (K, rows) in enumerate(wins):
            cq = list(b.alloc_qubits(cbits[idx]))
            store.append(cq)
            for i in rows:
                row(i, list(L[:K]) + cq)
        for idx in reversed(range(len(wins))):
            fold(idx, False)
    else:
        for idx in range(len(wins)):
            fold(idx, True)
        for idx in reversed(range(len(wins))):
            K, rows = wins[idx]
            for i in reversed(rows):
                row(i, list(L[:K]) + store[idx])
            b.free(km.array(store[idx]))
        store.clear()
        for i in reversed(big):
            row(i, list(L), kbig)


def build_hsplit(tables, prm, o: Opts, lay, angs):
    """sd-mode circuit with the H/L output split (f1 parked in x_n[21], fused phasing)."""
    bb = B()
    bb.cap = o.cap
    b = bb.b
    x = b.create_quantum_register(22, name='x')
    f1, f2, f4, f8, f16 = list(b.alloc_qubits(5))
    F = {'f1': f1}

    def thermo_compute():
        f1_ = F['f1']
        th = b.alloc_qubits(21)
        b.x(x[1:22]); b.cx(x[21], th[0])
        for k in range(1, 21):
            b.init_and(th[k - 1], x[21 - k], th[k])
        for k in range(1, 22):
            q = th[k - 1]
            b.cx(q, f1_)
            if k % 2 == 0:
                b.cx(q, f2)
            if k % 4 == 0:
                b.cx(q, f4)
            if k % 8 == 0:
                b.cx(q, f8)
            if k == 16:
                b.cx(q, f16)
        for k in range(20, 0, -1):
            b.del_and(th[k - 1], x[21 - k], th[k])
        b.cx(x[21], th[0]); b.x(x[1:22])
        b.free(th)

    def norm(fwd):
        stages = [(16, f16), (8, f8), (4, f4), (2, f2), (1, F['f1'])]
        for k, f in (stages if fwd else reversed(stages)):
            idx = range(21 - k, -1, -1) if fwd else range(0, 22 - k)
            for i in idx:
                b.cswap(f, x[i], x[i + k])

    bb.label = 'thermo'
    thermo_compute()
    bb.label = 'norm'
    norm(True)
    b.cx(f1, x[21]); b.x(x[21]); b.cx(x[21], f1)
    b.free(km.array([f1]))
    address = km.array(list(x[14:21]) + [x[21]])

    nT, n2, LB, nH = prm.nT, prm.F2 - 1, lay.LB, lay.nH
    Lr = b.alloc_qubits(LB)
    Hr = b.alloc_qubits(nH)
    Tr = b.alloc_qubits(nT)
    C2r = b.alloc_qubits(n2)
    target = km.array(list(Lr) + list(Hr) + list(Tr) + list(C2r))
    packed = [int(lay.u[a]) | (int(lay.H[a]) << LB) | (int(tables[a, 1]) << (LB + nH)) | (int(tables[a, 2]) << (LB + nH + nT))
              for a in range(256)]
    bb.label = 'lookup'
    b.init_lookup(table=packed, address=address, target=target)
    bb.note(' lookup')
    flags4 = (f2, f4, f8, f16)

    def angfn(ang, off):
        def g(j):
            a = int(ang[off + j]) % (1 << 64) if off + j < len(ang) else 0
            return None if a == 0 else Fraction(2 * a, 1 << 64)
        return g

    # phase H (+ the constant 1/2 bit) right away, then free H by measurement
    pad = b.alloc_qubits(lay.nHf - nH) if lay.nHf > nH else []
    cq = b.alloc_qubits(1)[0]
    b.x(cq)
    ext = b.alloc_qubits(3)
    RH = list(Hr) + list(pad) + [cq] + list(ext)
    bb.label = 'Hphase'
    fused_phase(bb, RH, lay.nHf, angfn(angs[0], lay.S - prm.G0), flags4)
    b.free(ext)
    b.x(cq)
    b.free(km.array([cq]))
    if len(pad):
        b.free(pad)
    Htab = [int(lay.H[a]) for a in range(256)]
    assert o.mdel
    mH = measure(b, Hr)
    b.free(Hr)

    # Horner
    WA = o.WA if o.WA is not None else nT
    gA = b.alloc_qubits(o.gA) if WA < nT else []
    bb.label = 'A'
    sd_step(bb, x, prm.rowsA, C2r, Tr, prm.eA, WA, gA, True)
    bb.label = 'B'
    wstore = []
    if o.wins:
        win_step(bb, x, prm, Tr, Lr, o.wins, o.wcb, True, wstore, o.kbig, o.qcap)
    else:
        sd_step(bb, x, prm.rowsB, Tr, Lr, prm.eB, LB, [], True)
    # phase L
    ext = b.alloc_qubits(3)
    RL = list(Lr[prm.G0:]) + list(ext)
    bb.label = 'Lphase'
    fused_phase(bb, RL, LB - prm.G0 - 1, angfn(angs[1], 0), flags4)
    b.free(ext)
    bb.label = 'B-1'
    if o.wins:
        win_step(bb, x, prm, Tr, Lr, o.wins, o.wcb, False, wstore, o.kbig, o.qcap)
    else:
        sd_step(bb, x, prm.rowsB, Tr, Lr, prm.eB, LB, [], False)
    bb.label = 'A-1'
    sd_step(bb, x, prm.rowsA, C2r, Tr, prm.eA, WA, gA, False)
    if gA:
        b.free(gA)
    utab = [int(lay.u[a]) | (int(tables[a, 1]) << LB) | (int(tables[a, 2]) << (LB + nT)) for a in range(256)]
    tgt2 = km.array(list(Lr) + list(Tr) + list(C2r))
    bb.label = 'unlookup'
    mR = measure(b, tgt2)
    b.free(tgt2)
    mdel(b, address, [(mH, Htab), (mR, utab)])
    nf1 = b.alloc_qubits(1)[0]
    b.cx(x[21], nf1); b.x(x[21]); b.cx(nf1, x[21])
    F['f1'] = nf1
    # stage-wise un-normalization; each flag equals [top d bits zero] of the restored state,
    # so it is cleared by HMR + a conditional multi-controlled Z (avg half the Toffolis)
    bb.label = 'unnorm'
    for d, f in [(1, nf1), (2, f2), (4, f4), (8, f8), (16, f16)]:
        for i in range(0, 22 - d):
            b.cswap(f, x[i], x[i + d])
        top = list(x[22 - d:22])
        if d == 1:
            b.x(f); b.cx(x[21], f)
            continue
        m = b.alloc_bits(1)[0]
        b.hmr(f, m)
        b.push_condition(m)
        b.x(km.array(top))
        if d == 2:
            b.cz(top[0], top[1])
        else:
            anc = b.alloc_qubits(d - 2)
            b.init_and(top[0], top[1], anc[0])
            for j in range(1, d - 2):
                b.init_and(anc[j - 1], top[j + 1], anc[j])
            b.cz(anc[d - 3], top[d - 1])
            for j in reversed(range(1, d - 2)):
                b.del_and(anc[j - 1], top[j + 1], anc[j])
            b.del_and(top[0], top[1], anc[0])
            b.free(anc)
        b.x(km.array(top))
        b.pop_condition()
        b.free(km.array([m]))
    b.free(km.array([nf1, f2, f4, f8, f16]))
    return b.finish_circuit(), bb.peak

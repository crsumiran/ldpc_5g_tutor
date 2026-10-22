"""Layered offset-Min-Sum decoder, three ways, bit-exact equal (chapter 07).

  decode_dense : textbook version on the expanded H matrix (edge lists).
  decode_qc    : hardware view. Memory holds one Z-lane word per base column.
                 For every non-empty block: READ word -> ROTATE by P -> CNU
                 lanes -> ROTATE BACK by P -> WRITE.  Two rotators.
  decode_delta : same datapath with ONE rotator. Each column is left in
                 memory in the rotation of its last use; the next reader
                 rotates by the difference (P_new - P_old) mod Z.

All arithmetic is integer with saturation, so the three must agree exactly.
The base matrix is a random toy, NOT a 5G base graph.

Run `python3 layered_qc.py`.
"""
import random

from rotators import rotl_ref

QMAX = 31                         # 6-bit signed LLR range [-31, 31]
OFFSET = 1                        # offset Min-Sum: |R| = max(min - 1, 0)


def sat(v, q=QMAX):
    return max(-q, min(q, v))


def rotl(x, s):
    return rotl_ref(x, s % len(x))


def rotr(x, s):
    return rotl(x, -s)


def expand(base, z):
    """Dense H: block (r, c) with shift P puts a 1 at row r*z+i, column c*z+(i+P)%z."""
    rows, cols = len(base), len(base[0])
    h = [[0] * (cols * z) for _ in range(rows * z)]
    for r in range(rows):
        for c in range(cols):
            p = base[r][c]
            if p >= 0:
                for i in range(z):
                    h[r * z + i][c * z + (i + p) % z] = 1
    return h


def cnu(q_msgs):
    """Check-node unit for one check: offset Min-Sum, exclude-the-recipient.

    Hardware form: compute min1, min2, index of min1 and total sign once,
    then each outgoing message is (min2 if I am the min1 edge else min1)
    with sign = total_sign XOR my_sign.
    """
    mags = [abs(q) for q in q_msgs]
    idx = min(range(len(mags)), key=lambda e: mags[e])
    min1 = mags[idx]
    min2 = min(m for e, m in enumerate(mags) if e != idx)
    neg = sum(q < 0 for q in q_msgs) & 1
    out = []
    for e, q in enumerate(q_msgs):
        mag = max((min2 if e == idx else min1) - OFFSET, 0)
        sign = neg ^ (q < 0)
        out.append(-mag if sign else mag)
    return out


def decode_dense(base, z, llr, iters):
    h = expand(base, z)
    L = list(llr)
    R = {}                                          # (row, col) -> message
    for _ in range(iters):
        for layer in range(len(base)):
            for row in range(layer * z, (layer + 1) * z):
                cols = [c for c, v in enumerate(h[row]) if v]
                q = [sat(L[c] - R.get((row, c), 0)) for c in cols]
                r = cnu(q)
                for c, qq, rr in zip(cols, q, r):
                    R[(row, c)] = rr
                    L[c] = sat(qq + rr)
    return L


def _layer_update(words, R, layer, edges, z):
    """Lane-parallel CNU over one layer. words[e] is already rotated by P."""
    q = [[sat(words[e][i] - R[(layer, c)][i]) for i in range(z)] for e, (c, _) in enumerate(edges)]
    new = [[0] * z for _ in edges]
    for i in range(z):                              # Z identical CNU lanes
        r = cnu([q[e][i] for e in range(len(edges))])
        for e in range(len(edges)):
            new[e][i] = r[e]
    for e, (c, _) in enumerate(edges):
        R[(layer, c)] = new[e]
    return [[sat(q[e][i] + new[e][i]) for i in range(z)] for e in range(len(edges))]


def _edges(base, layer):
    return [(c, p) for c, p in enumerate(base[layer]) if p >= 0]


def decode_qc(base, z, llr, iters):
    cols = len(base[0])
    mem = [llr[c * z:(c + 1) * z] for c in range(cols)]          # L memory, natural order
    R = {(r, c): [0] * z for r in range(len(base)) for c, p in enumerate(base[r]) if p >= 0}
    for _ in range(iters):
        for layer in range(len(base)):
            edges = _edges(base, layer)
            words = [rotl(mem[c], p) for c, p in edges]          # read-side rotator
            out = _layer_update(words, R, layer, edges, z)
            for (c, p), w in zip(edges, out):
                mem[c] = rotr(w, p)                              # write-side rotator
    return sum(mem, [])


def decode_delta(base, z, llr, iters):
    cols = len(base[0])
    mem = [llr[c * z:(c + 1) * z] for c in range(cols)]
    cur = [0] * cols                                             # rotation each column is stored in
    R = {(r, c): [0] * z for r in range(len(base)) for c, p in enumerate(base[r]) if p >= 0}
    for _ in range(iters):
        for layer in range(len(base)):
            edges = _edges(base, layer)
            words = [rotl(mem[c], p - cur[c]) for c, p in edges]  # ONE rotator, delta shift
            out = _layer_update(words, R, layer, edges, z)
            for (c, p), w in zip(edges, out):
                mem[c], cur[c] = w, p                            # write back un-rotated
    return sum((rotr(mem[c], cur[c]) for c in range(cols)), [])  # final realign for output


def _check():
    rng = random.Random(7)
    for trial in range(30):
        z = rng.choice([2, 3, 5, 8, 13])
        rows, cols = rng.randint(2, 4), rng.randint(5, 8)
        base = [[rng.randrange(z) if rng.random() < 0.6 else -1 for _ in range(cols)] for _ in range(rows)]
        for r in base:                              # every check needs >= 2 edges
            while sum(p >= 0 for p in r) < 2:
                r[rng.randrange(cols)] = rng.randrange(z)
        llr = [rng.randint(-QMAX, QMAX) for _ in range(cols * z)]
        a = decode_dense(base, z, llr, iters=3)
        b = decode_qc(base, z, llr, iters=3)
        c = decode_delta(base, z, llr, iters=3)
        assert a == b == c, (trial, base, z)
    print("dense, two-rotator and one-rotator (delta-shift) decoders agree bit-exactly on 30 random QC codes")


if __name__ == "__main__":
    _check()

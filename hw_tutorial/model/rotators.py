"""Golden models for the circular-shift (rotation) networks in this tutorial.

Every function here mirrors one RTL module in ../rtl/ stage by stage, so you
can print intermediate values while debugging a waveform.

Convention used everywhere in the hardware tutorial (see chapter 02):

    rotl(x, s)[i] = x[(i + s) mod Z]        "left rotation by s"

This is exactly what a 5G circulant I(P) needs: row i of I(P) has its single
1 in column (i + P) mod Z, so check-node lane i must receive variable lane
(i + P) mod Z.  (The Python course, LDPC-11, uses right rotation; rotl by P
equals its rotate-right by -P.)

Run `python3 rotators.py` to self-check every construction.
"""

# 5G NR lifting sizes, TS 38.212 Table 5.3.2-1 (51 values, 2..384)
NR_LIFTING_SETS = ((2, 4, 8, 16, 32, 64, 128, 256), (3, 6, 12, 24, 48, 96, 192, 384),
                   (5, 10, 20, 40, 80, 160, 320), (7, 14, 28, 56, 112, 224),
                   (9, 18, 36, 72, 144, 288), (11, 22, 44, 88, 176, 352),
                   (13, 26, 52, 104, 208), (15, 30, 60, 120, 240))
NR_Z = sorted(z for s in NR_LIFTING_SETS for z in s)


# --------------------------------------------------------------------------
# 0. The specification: what any rotator must compute
# --------------------------------------------------------------------------
def rotl_ref(x, s, z=None):
    """Reference: rotate the first z lanes of x left by s. Lanes >= z are don't-care (None)."""
    z = len(x) if z is None else z
    return [x[(i + s) % z] for i in range(z)] + [None] * (len(x) - z)


# --------------------------------------------------------------------------
# 1. Barrel rotator (chapter 04): ceil(log2 N) stages of 2:1 muxes
# --------------------------------------------------------------------------
def rotl_barrel(x, s, trace=None):
    """Stage k rotates by 2**k (mod N) when bit k of s is set. Works for ANY N."""
    n = len(x)
    stages = max(1, (n - 1).bit_length())
    for k in range(stages):
        if (s >> k) & 1:
            x = [x[(i + (1 << k)) % n] for i in range(n)]   # one 2:1 mux per lane
        if trace is not None:
            trace.append(list(x))
    return x


def shl_logical(x, s):
    """Non-circular left shift: lane i gets x[i+s], zero-fill at the top."""
    return [x[i + s] if i + s < len(x) else 0 for i in range(len(x))]


def shr_logical(x, s):
    """Non-circular right shift: lane i gets x[i-s], zero-fill at the bottom."""
    return [x[i - s] if i - s >= 0 else 0 for i in range(len(x))]


# --------------------------------------------------------------------------
# 2. QSN-style variable-size rotator (chapter 05): two shifters + merge
# --------------------------------------------------------------------------
def rotl_qsn(x, s, z):
    """Rotate the first z lanes of an N-lane bus left by s (0 <= s < z <= N).

    left  = x shifted left  by s      -> correct for lanes i <  z - s
    right = x shifted right by z - s  -> correct for lanes i >= z - s
    merge picks per lane with a thermometer mask (i < z - s).
    """
    left = shl_logical(x, s)
    right = shr_logical(x, z - s)
    out = [left[i] if i < z - s else right[i] for i in range(z)]
    return out + [None] * (len(x) - z)


def rotl_bypass(x, s, z, rot=rotl_barrel):
    """Same idea as rotl_qsn but built from two N-lane CYCLIC rotators.

    This is the form used by the hybrid 5G network (chapter 06): any
    full-size cyclic rotator `rot` (barrel, Banyan or IBN) can be reused.
    """
    n = len(x)
    a = rot(x, s)                     # lanes i <  z-s : x[i+s]
    b = rot(x, (n - z + s) % n)       # lanes i >= z-s : x[i+s-z]
    out = [a[i] if i < z - s else b[i] for i in range(z)]
    return out + [None] * (n - z)


# --------------------------------------------------------------------------
# 3. Switch primitives (chapter 03)
# --------------------------------------------------------------------------
def switch2(a, b, cross):
    """2x2 switch: bar passes straight (a,b); cross swaps (b,a). Two 2:1 muxes."""
    return (b, a) if cross else (a, b)


def switch3(v, r):
    """3x3 rotating switch: out[q] = v[(q + r) mod 3], r in {0,1,2}. Three 3:1 muxes."""
    return [v[(q + r) % 3] for q in range(3)]


# --------------------------------------------------------------------------
# 4. Banyan (butterfly) rotator for N = 2**n (chapter 06)
# --------------------------------------------------------------------------
def rotl_banyan(x, s, trace=None, depth=0):
    """Recursive Banyan network rotating left by s.

    Stage 1: N/2 2x2 switches, switch k joins lanes k and k+H (H = N/2).
             Switch k crosses when  s[n-1] XOR (k < b),  b = s mod H.
    Then   : two H-input Banyans (upper half, lower half), BOTH rotate by b.

    Because H is a power of two, b = s mod H is just the low bits of s:
    no modulo hardware anywhere. All switches in a stage share the same b,
    so one thermometer decoder per stage generates every control signal.
    """
    n = len(x)
    if n == 1:
        return list(x)
    h = n // 2
    a, b = s // h, s % h               # a = MSB of s, b = low bits
    up, lo = [None] * h, [None] * h
    for k in range(h):
        cross = a ^ (k < b)
        up[k], lo[k] = switch2(x[k], x[k + h], cross)
    if trace is not None:
        trace.append((depth, up + lo))
    return rotl_banyan(up, b, trace, depth + 1) + rotl_banyan(lo, b, trace, depth + 1)


# --------------------------------------------------------------------------
# 5. Improved Banyan Network (IBN) for N = 3 * 2**n (chapter 06, Song et al.)
# --------------------------------------------------------------------------
def rotl_ibn(x, s, radix=3):
    """IBN: first a stage of M radix-r switches, then r power-of-two Banyans.

    N = r*M, M = 2**n.  Write s = a*M + b  (a = s >> n, b = s mod M = low bits).
    Switch k (lanes k, k+M, k+2M) rotates the r blocks by a, or by a+1 when k < b.
    Then every M-lane Banyan rotates its block left by the same b.
    """
    n = len(x)
    m = n // radix
    assert m * radix == n and m & (m - 1) == 0, "N must be radix * 2**n"
    a, b = s // m, s % m
    blocks = [[None] * m for _ in range(radix)]
    for k in range(m):
        r = (a + (k < b)) % radix
        v = [x[q * m + k] for q in range(radix)]
        out = [v[(q + r) % radix] for q in range(radix)]
        for q in range(radix):
            blocks[q][k] = out[q]
    return sum((rotl_banyan(blk, b) for blk in blocks), [])


# --------------------------------------------------------------------------
# 6. Multi-frame Banyan (chapter 06): 2**f independent frames of size N/2**f
# --------------------------------------------------------------------------
def rotl_banyan_multiframe(x, shifts):
    """Force the first f stages to 'bar' and give every sub-Banyan its own shift."""
    f = len(shifts)
    size = len(x) // f
    out = []
    for j, s in enumerate(shifts):
        out += rotl_banyan(x[j * size:(j + 1) * size], s)
    return out


# --------------------------------------------------------------------------
# Hardware cost (counted in 2:1-mux equivalents per data bit)
# --------------------------------------------------------------------------
def cost_barrel(n):
    return n * max(1, (n - 1).bit_length())


def cost_banyan(n):
    return 0 if n == 1 else n + 2 * cost_banyan(n // 2)     # N/2 switches * 2 muxes


def cost_ibn3(n):
    m = n // 3
    return 3 * m * 2 + 3 * cost_banyan(m)                    # 3:1 mux ~ two 2:1 muxes


def cost_bypass(n, inner):
    return 2 * inner(n) + n


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------
def _check():
    import random
    rng = random.Random(1)

    # fixed-size rotators, exhaustive over shifts
    for n in list(range(1, 40)) + [96, 128, 384]:
        x = list(range(100, 100 + n))
        for s in range(n):
            assert rotl_barrel(x, s) == rotl_ref(x, s), ("barrel", n, s)
            if n & (n - 1) == 0:
                assert rotl_banyan(x, s) == rotl_ref(x, s), ("banyan", n, s)
            if n % 3 == 0 and (n // 3) & (n // 3 - 1) == 0:
                assert rotl_ibn(x, s) == rotl_ref(x, s), ("ibn", n, s)
            if n % 5 == 0 and (n // 5) & (n // 5 - 1) == 0:
                assert rotl_ibn(x, s, radix=5) == rotl_ref(x, s), ("ibn5", n, s)

    # variable-size rotators: every 5G Z and every shift on a 384-lane bus
    n = 384
    count = 0
    for z in NR_Z:
        x = [rng.randrange(256) for _ in range(n)]
        for s in range(z):
            want = rotl_ref(x, s, z)
            assert rotl_qsn(x, s, z) == want, ("qsn", z, s)
            assert rotl_bypass(x, s, z, rotl_ibn) == want, ("bypass-ibn", z, s)
            count += 1

    # multi-frame: 4 frames of 32 lanes on a 128-lane Banyan
    x = list(range(128))
    sh = [3, 0, 31, 17]
    want = sum((rotl_ref(x[j * 32:(j + 1) * 32], sh[j]) for j in range(4)), [])
    assert rotl_banyan_multiframe(x, sh) == want

    assert len(NR_Z) == 51 and NR_Z[0] == 2 and NR_Z[-1] == 384
    print(f"all rotator models agree with the reference ({count} (Z, shift) pairs at N=384)")
    print("2:1-mux equivalents per bit at N=384: "
          f"barrel={cost_barrel(384)}, IBN={cost_ibn3(384)}, "
          f"bypass(barrel)={cost_bypass(384, cost_barrel)}, bypass(IBN)={cost_bypass(384, cost_ibn3)}")


if __name__ == "__main__":
    _check()

# 06 · Banyan, IBN and the 5G network

> Goal: derive, from scratch, how a Banyan network rotates and how its control
> bits are generated. Then extend it to 384 = 3 × 128 lanes the way the
> Song/Cui/Wang paper does, and assemble a complete 5G rotator.
> RTL: `rtl/rot_banyan.v`, `rtl/rot_ibn3.v`, `rtl/rot_5g.v`.
> Model: `rotl_banyan`, `rotl_ibn`, `rotl_bypass`, `rotl_banyan_multiframe`.

---

## 1. Why bother, when the barrel rotator already works?

Two reasons, both from chapter 04 §6:

1. **Multi-frame.** A Banyan can be split into independent smaller rotators.
   At small Z this keeps the 384 lanes busy instead of 90% idle.
2. **Non-power-of-two sizes done well.** 5G's maximum Z is 384 = 3 × 2^7.
   The right recursive structure fits it exactly.

Neither is free. The Banyan's switches need **generated** control bits, unlike
the barrel's raw shift bits. The whole design problem is making that control
logic small and fast. That is the topic of the paper.

## 2. Deriving the Banyan rotator

Take N = 2H lanes and split the shift into its top bit and the rest:

```
s = a·H + b        a = s[n−1] (0 or 1),   b = s mod H = s[n−2:0]
```

**Plan:** stage 0 (H switches, switch k joins lanes k and k+H) produces an
upper half and a lower half. Then each half goes through an H-lane rotator
that rotates left by the **same** amount b. If we can find switch settings
that make this give the right answer, recursion does the rest.

**What must the halves contain?** Output lane `q·H + j` (half q, position j)
must receive `x[(qH + j + s) mod N]`. Half q is rotated left by b, so its
lane k ends up at output position `j = (k − b) mod H`. Work backwards from k:

* If **k ≥ b**, that element did not wrap inside the half (`j = k − b`). It must be
  `x[(qH + k + aH) mod N]`, i.e. lane k of input half `(q + a) mod 2`.
* If **k < b**, it wrapped (`j = k − b + H`). It must be
  `x[(qH + k + H + aH) mod N]`, i.e. lane k of input half `(q + a + 1) mod 2`.

In both cases half q takes **lane k from one of the two input halves**, and
that is exactly what switch k can deliver. Switch k sends the upper input to
the lower half (swap) when:

```
swap[k] = a XOR (k < b)
```

**Intuition.** Stage 0 never moves anything *within* a half. Its only job is
to send every value to the half where it must end up. The smaller rotators
then fix positions inside the half. "k < b" marks the lanes whose values wrap
around inside the half, and those need the opposite half from the others.

## 3. Worked example: N = 8, s = 5

`s = 5 = 1·4 + 1`, so a = 1 and b = 1. Then `swap = a XOR (k < 1)` = `[0, 1, 1, 1]`.

```
input                 A B C D | E F G H
stage 0 swap=[0,1,1,1]
  switch 0 (A,E) bar   → upper[0]=A, lower[0]=E
  switch 1 (B,F) swap  → upper[1]=F, lower[1]=B
  switch 2 (C,G) swap  → upper[2]=G, lower[2]=C
  switch 3 (D,H) swap  → upper[3]=H, lower[3]=D
halves                A F G H | E B C D
each half rotl by b=1 F G H A | B C D E
expected rotl(x,5)    F G H A B C D E   ✓
```

The upper half {A, F, G, H} is exactly the set of values that output lanes 0–3
need (F G H A), just not yet in order. The 4-lane sub-rotators handle that
with s = 1, and the same derivation repeats with H = 2, then H = 1.

## 4. Control generation and sharing

At stage d, the block size is `B = N >> d` and the switch span is `H = B/2`.
In single-frame mode, **every block at stage d uses the same (a, b)**, because
every sub-rotator received the same b from the level above:

```
a_d = shift[n−1−d]              one wire
b_d = shift & (H − 1)           just the low bits: no arithmetic
swap_d[k] = a_d XOR (k < b_d)   k = 0..H−1, shared by all 2^d blocks
```

`(k < b_d)` for all k is a **thermometer decoder** of `b_d`. Each output is a
compare-with-constant, which synthesis reduces to a few gates. The per-stage
control cost is one H-output thermometer, so across all stages it is about N
small comparators in total. **Note what is absent: no modulo, no subtractor,
no lookup table.** This is only true because every sub-network size is a
power of two, so `s mod H` is free bit slicing. Remember this for section 6.

From `rtl/rot_banyan.v`:

```verilog
localparam [SW-1:0] MASK = {SW{1'b1}} >> (d + 1);   // = H - 1
wire          a = shift[SW-1-d];
wire [SW-1:0] b = shift & MASK;
for (k = 0; k < H; k = k + 1)
    assign swap[k] = a ^ (k < b);
// then N/2 sw2 instances, switch (j*B + k, j*B + k + H) driven by swap[k]
```

Cost is identical to the barrel rotator: (N/2)·log2 N switches = N·log2 N
2:1 muxes per bit.

## 5. Multi-frame mode

If the first f stages are forced to **bar**, no value ever crosses a 2^(n−f)
boundary. The network becomes 2^f independent rotators of size N/2^f, and
each can be given **its own shift**:

```
128-lane Banyan, f = 2: stage 0 and stage 1 forced to bar
→ four independent 32-lane rotators with shifts s0, s1, s2, s3
```

`rotl_banyan_multiframe` in the model does exactly this, and the self-check
verifies four 32-lane frames with shifts 3, 0, 31, 17.

What it buys you in 5G:

* **Several code blocks at once.** Several small code blocks (from one user or
  several) decode in lockstep on one 384-lane datapath.
* **Several base-matrix blocks of one code block at once.** In the 384-lane
  IBN (section 6), at Z = 48 each 64-lane sub-network can carry one 48-lane
  frame. Six **different blocks of a layer** then go through in one cycle,
  each with its own shift. The exact options per Z are in the paper's Table II.
  This is why the paper insists on *different* SVs per frame. Boutillon's EBS
  (chapter 05) can split into frames, but they must share one SV.

A barrel rotator cannot do this, because every one of its stages mixes the
whole bus.

## 6. 384 is not a power of two: VBN vs IBN

384 = 3 × 128. There are two ways to add a factor of 3.

### VBN (variation Banyan network, Peng et al. 2010): the 3×3 stage **last**

```
 384 lanes → 2×2 stage (halves of 192) → 2×2 stage (quarters of 96) → … → 3×3 stage
```

The sub-network sizes are 192, 96, 48, …, i.e. **3·2^j**. Each stage's control
needs `b = s mod (3·2^j)`, and that is **real modulo hardware**: one per stage,
on the critical path. The paper's Algorithm 1 is this controller. Their Table I
reports 127 modular operations for the reconfigurable 5G network of [11].

### IBN (improved Banyan network, Song et al. 2022): the 3×3 stage **first**

```
 384 lanes → 3×3 stage (128 switches) → three 128-lane power-of-two Banyans
```

Repeat the section 2 derivation with three blocks of M = 128 instead of two
halves:

```
s = a·M + b          a = s[8:7] ∈ {0,1,2},   b = s[6:0]
3×3 switch k joins lanes k, k+M, k+2M and rotates the three blocks by
        r_k = (a + (k < b)) mod 3
then all three Banyans rotate left by b (shared control, section 4)
```

Every sub-network is now a power of two, so **every modulo disappears**. The
only arithmetic left is `a + 1` (mod 3) on a 2-bit value. That is the paper's
key trick: *"through an ingenious modification on the order of permutations…
the sizes of all subnetworks are powers of 2."*

Worked example, N = 12 (M = 4, the paper's Fig. 3b size), s = 7, so a = 1
and b = 3:

```
input                       A B C D | E F G H | I J K L
r_k = (1 + (k<3)) mod 3  →  k=0,1,2: r=2   k=3: r=1
after 3x3 stage             I J K H | A B C L | E F G D
each block rotl by b=3      H I J K | L A B C | D E F G
expected rotl(x, 7)         H I J K L A B C D E F G   ✓
```

The same construction works for 5 × 2^n with 5×5 switches. The model
self-check verifies radix 5 as well.

From `rtl/rot_ibn3.v`:

```verilog
wire [1:0]    a = shift[SW-1:MW];          // 0..2
wire [MW-1:0] b = shift[MW-1:0];
// per lane k of the 3x3 stage:
wire [1:0] sum = a + (k < b);              // at most 3
wire [1:0] r   = (sum == 2'd3) ? 2'd0 : sum;
sw3 u_sw (.in0(din[k]), .in1(din[k+M]), .in2(din[k+2M]), .r(r), ...);
// then three rot_banyan #(.N(M)) instances, all with shift = b
```

**Datapath cost check** (per bit, N = 384). The 3×3 stage is 384 3:1 muxes,
about 768 2:1 muxes. The three Banyans are 3 × 128 × 7 = 2,688. The total,
3,456, is the same as the barrel rotator. The IBN's advantages are its control logic,
which has no modulo, and its multi-frame flexibility.

## 7. The complete 5G rotator: IBN + bypass

An IBN rotates all 384 lanes. To rotate any Z ≤ 384, reuse the chapter 05
trick, but build it from two **cyclic** N-lane rotators:

```
A = rotl_384(din, s)                       correct for lanes i <  Z − s
B = rotl_384(din, (384 − Z + s) mod 384)   correct for lanes i ≥  Z − s
dout[i] = (i < Z − s) ? A[i] : B[i]        for i < Z
```

Why B works: for i ≥ Z − s, `(i + 384 − Z + s) mod 384 = i − Z + s`, which is
exactly the wrapped source lane.

This is the structure of the paper's **Fig. 6(a)**: two 3·2^7-input IBNs
followed by a Merge Network. It is `rtl/rot_5g.v`, and the testbench passes
all 51 lifting sizes × every shift.

```
           ┌──────────── IBN-384 (shift s) ───────────┐
din ──┬───►│ 3x3 stage → 3 × Banyan-128               ├──► A ─┐
      │    └──────────────────────────────────────────┘       │  merge:
      │    ┌──────────── IBN-384 (shift s2) ──────────┐       ├─ i < Z−s ? A : B ──► dout
      └───►│ 3x3 stage → 3 × Banyan-128               ├──► B ─┘
           └──────────────────────────────────────────┘
s2 = (384 − Z + s) mod 384   (one add, one conditional subtract;
                              precompute it with s in the shift table)
```

### The paper's general "hybrid" network

The paper generalizes this with an **Elementary Unit (EU)**: the smallest
sub-network, of size p = the smallest Z in the standard, built as a barrel
shifter (cheapest, and its control is free). IBN layers are stacked above the EUs
for multi-frame splitting, and bypass/merge handles Z values that do not
fill a sub-network exactly.

* **5G:** p = 2 is tiny, so the EUs merge into the IBNs. The result is the
  structure above. It has **eight parallelism options** and handles up to
  **192 frames** at Z = 2 (their Table II).
* **802.11n:** Z ∈ {27, 54, 81}, so p = 27. Three 27-lane barrel EUs under a
  3-input IBN give an 81-lane network. A plain Banyan would need 128 lanes and
  the VBN 96.

Their reported result (TSMC 90 nm): 25% area reduction and 46% better
area-efficiency than the previous best 5G network. Most of the gain comes
from the much smaller and shorter controller, and frequency goes up 33–40%.

## 8. Comparison of everything so far (N = 384, per data bit)

| Network | 2:1-mux equiv. | Depth (mux levels) | Control logic | Any Z ≤ N | Multi-frame, different shifts |
|---|---|---|---|---|---|
| Crossbar | ≈ 147,000 | 9 | per-output select | yes (with mod) | yes |
| Barrel rotator | 3,456 | 9 | none | **no** | no |
| QSN (2 shifters + merge) | ≈ 7,300 | 10 + subtract | subtract + thermometer | yes | no |
| Banyan (power of 2 only, 512) | 4,608 | 9 | thermometer per stage | no | yes |
| VBN 384 | ≈ 3,456 | 9 | **modulo per stage** | with bypass | yes |
| IBN 384 | 3,456 | 9 | thermometer per stage + 2-bit add | no | yes |
| **IBN + bypass (5G)** | 7,296 | 10 | as IBN + merge thermometer | **yes** | **yes** |

(Mux counts come from the cost functions in `model/rotators.py`. They are a
first-order comparison, not synthesis results.)

---

### Exercises

1. Draw the 4-lane Banyan for s = 3 and derive all switch settings with
   `swap = a XOR (k < b)`. Check the result.
2. **Multi-frame RTL.** Add an input `frame_log2` (0..3) and per-frame shift
   inputs to `rot_banyan.v`. Stages `d < frame_log2` are forced to bar, and the
   later stages of block j use the shift of the frame that block j belongs to.
   Use `rotl_banyan_multiframe` as the golden model.
3. In the IBN, why may `a + (k < b)` reach 3 but never more?
4. Write `rot_ibn5.v` for N = 5 × 2^n using a 5×5 rotating switch. The model
   already supports `radix=5`.
5. Read the paper's Algorithm 2 and equation (1). Map their `SV_k`, `Th_k`,
   `C_k[j]` onto `b_d`, the thermometer and `swap_d[k]` in this chapter. Their
   network may rotate the other way; use chapter 02 §3.

<details><summary>Answer to 1</summary>

N = 4, s = 3 → a = 1, b = 1. Stage 0: swap = [1 XOR (0<1), 1 XOR (1<1)] = [0, 1].
Input A B C D: switch 0 (A,C) bar → up A, lo C. Switch 1 (B,D) swap → up D, lo B.
Halves: A D | C B. Each rotates by b = 1. In the 2-lane level, a = 1 and b = 0,
so every switch swaps: D A | B C. Expected rotl(ABCD, 3) = D A B C ✓.
</details>

<details><summary>Answer to 3</summary>

s < 3M means a ≤ 2, and (k < b) is 0 or 1. So the sum is at most 3, and 3 mod 3 = 0.
That is why one compare-and-replace replaces a modulo.
</details>

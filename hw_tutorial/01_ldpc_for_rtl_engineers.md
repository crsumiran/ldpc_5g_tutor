# 01 · LDPC for RTL engineers

> Goal: understand just enough of the algorithm to see it as a datapath.
> No probability theory beyond "a signed number that means *probably 0* or
> *probably 1*".

---

## 1. Parity checks: rules the codeword must satisfy

An LDPC code is defined by a binary **parity-check matrix H**. Rows are rules
(*checks*), columns are bits (*variables*). A bit vector `x` is a valid codeword
when every row XORs to zero:

```
        x0 x1 x2 x3 x4 x5
H = [   1  1  0  1  0  0 ]   check 0:  x0 ^ x1 ^ x3 = 0
    [   0  1  1  0  1  0 ]   check 1:  x1 ^ x2 ^ x4 = 0
    [   1  0  1  0  0  1 ]   check 2:  x0 ^ x2 ^ x5 = 0
```

The **syndrome** `s = H·x mod 2` holds one bit per check. All zeros means
every rule holds. In hardware that is an XOR-reduce per row.

**Low-density** means each row touches only a few bits. A 5G row touches at
most 19 of 68 base columns, so the total work is proportional to the number
of 1s in H, not to its full size.

## 2. The graph view (Tanner graph)

Draw a node for every check and every variable, and connect them where H has
a 1. Each edge is a wire along which two messages travel, one in each direction.

```
  checks:      c0        c1        c2
              / | \     / | \     / | \
  variables: x0 x1 x3  x1 x2 x4  x0 x2 x5
```

*Number of edges = number of 1s in H.* That is the decoder's total work per
iteration.

## 3. Soft bits: LLRs

The demapper does not hand us bits. It hands us **LLRs**:

| LLR | Meaning |
|---|---|
| +12 | very likely 0 |
| +1  | slightly favours 0 |
| −3  | fairly likely 1 |
| 0   | no idea (used for punctured bits that were never transmitted) |

The **sign is the guess** and the **magnitude is the confidence**. In hardware
this is a small saturating signed integer (6–8 bits is typical).

## 4. The check-node rule (Min-Sum)

A check node receives one message from every connected variable. It sends
back to each variable a message that answers this question: *given what the
**other** variables say, what must you be for this check to pass?*

* **Sign:** the XOR of the other inputs' signs (parity must come out even).
* **Magnitude:** the **minimum** of the other inputs' magnitudes. A chain is
  only as strong as its weakest link.

Worked example, one check with four inputs `Q = [+5, −2, +7, −9]`:

| edge | others' signs | others' min magnitude | message out |
|---|---|---|---|
| 0 (+5) | − + − → + | min(2,7,9) = 2 | **+2** |
| 1 (−2) | + + − → − | min(5,7,9) = 5 | **−5** |
| 2 (+7) | + − − → + | min(5,2,9) = 2 | **+2** |
| 3 (−9) | + − + → − | min(5,2,7) = 2 | **−2** |

**Hardware trick (min1/min2).** You never need a separate minimum per edge.
Compute once per check:

* `min1` = smallest magnitude, `idx` = which edge it came from,
* `min2` = second smallest magnitude,
* `S` = XOR of all signs.

Then message to edge e is `sign = S ^ sign_e` and `mag = (e == idx) ? min2 : min1`.
In the example, min1 = 2 (edge 1), min2 = 5, S = 0. That is a compare-tree plus
an XOR-tree, and it also compresses storage: the messages for a whole check
fit in `{min1, min2, idx, sign bits}`.

Plain Min-Sum is a little over-confident, so real decoders subtract an
offset (*offset Min-Sum*, `mag = max(mag − β, 0)`) or multiply by a factor
around 0.75 (*normalized Min-Sum*). Both are cheap in hardware.

## 5. Layered decoding: the schedule hardware uses

Keep one running LLR per bit, `L[v]` (the **APP** value, "a-posteriori").
Keep the last message every check sent to every bit, `R[c,v]`.

Process the checks one **layer** (group of rows) at a time:

```
for each layer:
    for each check c in the layer, for each bit v on c:
        Q[v]      = L[v] − R_old[c,v]      # remove this check's own old opinion
    R_new[c,·]    = MinSum(Q[·])           # check-node rule, section 4
    for each bit v on c:
        L[v]      = Q[v] + R_new[c,v]      # add the fresh opinion back
repeat until syndrome == 0 or max iterations
hard decision: bit v = (L[v] < 0)
```

Three things matter for hardware:

1. **Subtract-old / add-new.** Every edge costs one subtract and one add, and
   there is a single memory (`L`) that is read and then written.
2. Updated `L` values are used **immediately** by the next layer. This
   converges in roughly half the iterations of the textbook "flooding"
   schedule. It also creates a **read-after-write dependency** between
   consecutive layers that share a column (chapter 07).
3. Checks inside one layer must not share bits, so they can all run in parallel.
   The QC structure (next section) guarantees this.

## 6. Quasi-cyclic (QC) structure: where Z comes from

A real 5G H matrix has up to 46×384 = 17,664 rows and 68×384 = 26,112 columns.
Nobody stores that. It is described by a small **base graph** where every
entry is either *empty* or a **shift value P**:

```
base (2×3), Z = 4:                expanded H (8×12):

   [ 1   −   3 ]                   P=1        empty      P=3
   [ 0   2   − ]                  0 1 0 0 | 0 0 0 0 | 0 0 0 1
                                  0 0 1 0 | 0 0 0 0 | 1 0 0 0
                                  0 0 0 1 | 0 0 0 0 | 0 1 0 0
                                  1 0 0 0 | 0 0 0 0 | 0 0 1 0
                                  -------------------------------
                                  P=0       P=2        empty
                                  1 0 0 0 | 0 0 1 0 | 0 0 0 0
                                  0 1 0 0 | 0 0 0 1 | 0 0 0 0
                                  0 0 1 0 | 1 0 0 0 | 0 0 0 0
                                  0 0 0 1 | 0 1 0 0 | 0 0 0 0
```

Each non-empty entry becomes a **Z×Z circulant**: the identity matrix with its
columns rotated right by P. Each empty entry becomes a Z×Z zero block.

* One base **row** = one **layer** of Z checks. Those Z checks never share a
  bit, so they run in **Z parallel lanes**.
* One base **column** = a group of Z bits. Store them as **one wide memory
  word** of Z lanes.
* The circulant says *which* lane of the column word goes to *which* check lane.
  It is a rotation by P, and that is the whole reason this tutorial exists
  (chapter 02).

## 7. The 5G numbers (TS 38.212 §5.3.2)

| | BG1 | BG2 |
|---|---|---|
| Base matrix size | 46 × 68 | 42 × 52 |
| Non-empty blocks (edges per lane) | 316 | 197 |
| Information columns | 22 | up to 10 |
| Max row weight | 19 (row 0) | smaller |
| Max information bits K | 22 × 384 = 8448 | 10 × 384 = 3840 |
| Lifting sizes Z | 51 values, 2…384 | same |

The 51 lifting sizes are `Z = a × 2^j` with `a ∈ {2,3,5,7,9,11,13,15}`
(Table 5.3.2-1). The standard stores one value V per block per set `a`, and
the shift actually used is **P = V mod Z**.

The first 2Z information bits are never transmitted (*punctured*). Their LLRs
start at 0 and the decoder fills them in. High-rate transmissions use only
the first few base rows. Low-rate ones add more *extension* rows, so the number
of layers to process depends on the code rate.

(The counts 316 and 197 were checked by counting the entries of Tables
5.3.2-2 and 5.3.2-3 in the downloaded `ETSI_TS_138212_v17.9.0.pdf`.)

## 8. The datapath, finally

Put sections 4–6 together for one block of one layer, Z lanes wide:

```
L memory word for column c (Z lanes, natural order)
        │
        ▼
  ROTATE by P            ← chapters 02–06
        │
        ▼
  Q = L − R_old          Z subtractors
        │
        ▼
  CNU: min1/min2/idx/S   Z lanes, each accumulating over the row's blocks
        │
        ▼
  L_new = Q + R_new      Z adders
        │
        ▼
  ROTATE BACK by P       (or the one-rotator trick, chapter 07)
        │
        ▼
L memory word for column c
```

Every arithmetic box is "Z identical lanes, no interaction between lanes".
**The rotator is the only block where lanes talk to each other.**

`model/layered_qc.py` implements this exact flow and checks it bit-exactly
against a textbook dense-matrix decoder.

---

### Check yourself

<details><summary>A check has inputs [−4, +1, +6]. What are min1, min2, idx, S, and the three outgoing messages (plain Min-Sum)?</summary>

min1 = 1 (idx 1), min2 = 4, S = 1 (one negative).
Edge 0: sign = 1^1 = 0 → +, mag = min1 = 1 → **+1**.
Edge 1: sign = 1^0 = 1 → −, mag = min2 = 4 → **−4**.
Edge 2: sign = 1^0 = 1 → −, mag = min1 = 1 → **−1**.
</details>

<details><summary>Why can all Z checks of one layer be processed in parallel?</summary>

Each circulant is a permutation matrix: each check row in the block has
exactly one 1, in a different column. So the Z checks of a layer touch disjoint
bits inside every column group. No two lanes ever write the same L value.
</details>

<details><summary>For BG1 at Z = 384, how many check-to-bit messages are there per iteration?</summary>

316 blocks × 384 = 121,344 edges. A decoder that handles one block (384 edges)
per clock needs about 316 clocks per iteration, plus pipeline overhead.
</details>

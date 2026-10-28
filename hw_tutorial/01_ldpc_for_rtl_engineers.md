# 01 · LDPC for RTL Engineers

> **Goal:** Understand just enough of the LDPC decoding algorithm to see it as a datapath. No probability theory is needed beyond "a signed number that means *probably 0* or *probably 1*".
>
> * **Python Model:** `model/layered_qc.py`
> * **Standard:** TS 38.212 §5.3.2 (`ETSI_TS_138212_v17.9.0.pdf`)

---

## 1. Parity Checks: Rules the Codeword Must Satisfy

The transmitter does not send arbitrary bit patterns. It only sends *codewords*: bit vectors that satisfy a fixed set of parity rules. The decoder's whole job is to find the codeword that best matches what it received, so we start with those rules.

An LDPC code is defined by a binary **parity-check matrix H**. Rows are rules (*checks*), columns are bits (*variables*). A bit vector `x` is a valid codeword when every row XORs to zero:

```
        x0 x1 x2 x3 x4 x5
H = [   1  1  0  1  0  0 ]   check 0:  x0 ^ x1 ^ x3 = 0
    [   0  1  1  0  1  0 ]   check 1:  x1 ^ x2 ^ x4 = 0
    [   1  0  1  0  0  1 ]   check 2:  x0 ^ x2 ^ x5 = 0
```

The **syndrome** `s = H·x mod 2` holds one bit per check. All zeros means every rule holds. In hardware that is an XOR-reduce per row.

For example, with the H above:

* **A valid codeword:** `x = 1 1 0 0 1 1` gives syndrome `0 0 0`, so every check passes.
* **One bit flipped:** Flipping x2 gives `x = 1 1 1 0 1 1` and syndrome `0 1 1`. Checks 1 and 2 fail, and they are exactly the two checks that involve x2.

**Low-density** means each row touches only a few bits. A 5G row touches at most 19 of 68 base columns, so **the total work is proportional to the number of 1s in H, not to its full size.**

## 2. The Graph View (Tanner Graph)

The decoder works by sending messages between checks and bits, so it is useful to redraw H as a graph. Draw a node for every check and every variable, and connect them where H has a 1. Each edge is a wire along which two messages travel, one in each direction.

```
  checks:      c0        c1        c2
              / | \     / | \     / | \
  variables: x0 x1 x3  x1 x2 x4  x0 x2 x5
```

How to read the graph:

* **Each check fans out to the bits in its row:** c0 connects to x0, x1 and x3, matching row 0 of H.
* **A bit can appear under several checks:** x0, x1 and x2 each appear twice because each of them sits in two rows of H. In a real graph they are the same node, with two edges.

***Number of edges = number of 1s in H.*** That is the decoder's total work per iteration.

## 3. Soft Bits: LLRs

The demapper does not hand us bits. It hands us **LLRs** (log-likelihood ratios):

| LLR | Meaning |
|---|---|
| +12 | very likely 0 |
| +1  | slightly favours 0 |
| −3  | fairly likely 1 |
| 0   | no idea (used for punctured bits that were never transmitted) |

**The sign is the guess and the magnitude is the confidence.** In hardware this is a small saturating signed integer (6–8 bits is typical).

## 4. The Check-Node Rule (Min-Sum)

### The Rule

A check node receives one message from every connected variable. It sends back to each variable a message that answers this question: *given what the **other** variables say, what must you be for this check to pass?*

* **Sign:** The XOR of the other inputs' signs (parity must come out even).
* **Magnitude:** The **minimum** of the other inputs' magnitudes. A chain is only as strong as its weakest link.

### Worked Example

Take one check with four inputs `Q = [+5, −2, +7, −9]`. For each edge, leave that edge out and apply the rule to the other three:

| edge | others' signs | others' min magnitude | message out |
|---|---|---|---|
| 0 (+5) | − + − → + | min(2,7,9) = 2 | **+2** |
| 1 (−2) | + + − → − | min(5,7,9) = 5 | **−5** |
| 2 (+7) | + − − → + | min(5,2,9) = 2 | **+2** |
| 3 (−9) | + − + → − | min(5,2,7) = 2 | **−2** |

### Hardware Trick: min1/min2

Notice in the table that every edge except edge 1 gets magnitude 2, and edge 1 (the one holding the 2) gets the next smallest value, 5. **You never need a separate minimum per edge.** Compute once per check:

* **`min1`:** The smallest magnitude, with `idx` = which edge it came from.
* **`min2`:** The second smallest magnitude.
* **`S`:** The XOR of all signs.

Then the message to edge e is:

```
sign = S ^ sign_e
mag  = (e == idx) ? min2 : min1
```

In the example, min1 = 2 (edge 1), min2 = 5, S = 0. That is a compare-tree plus an XOR-tree, and it also compresses storage: the messages for a whole check fit in `{min1, min2, idx, sign bits}`.

### Offset and Normalized Min-Sum

Plain Min-Sum is a little over-confident, so real decoders correct the magnitude in one of two ways. Both are cheap in hardware:

* **Offset Min-Sum:** Subtract an offset, `mag = max(mag − β, 0)`.
* **Normalized Min-Sum:** Multiply by a factor around 0.75.

## 5. Layered Decoding: The Schedule Hardware Uses

The check-node rule says what to compute. The schedule says in which order to compute it and what state to keep. Hardware uses the *layered* schedule, which keeps two kinds of state:

* **`L[v]`:** One running LLR per bit (the **APP** value, "a-posteriori").
* **`R[c,v]`:** The last message every check sent to every bit.

Process the checks one **layer** (group of rows) at a time:

```
for each layer:
    for each check c in the layer:
        for each bit v on c:
            Q[v]   = L[v] − R_old[c,v]     # remove this check's own old opinion
        R_new[c,·] = MinSum(Q[·])          # check-node rule, section 4
        for each bit v on c:
            L[v]   = Q[v] + R_new[c,v]     # add the fresh opinion back
repeat until syndrome == 0 or max iterations
hard decision: bit v = (L[v] < 0)
```

Three things matter for hardware:

1. **Subtract-old / add-new:** Every edge costs one subtract and one add, and there is a single memory (`L`) that is read and then written.
2. **Immediate reuse:** Updated `L` values are used **immediately** by the next layer. This converges in roughly half the iterations of the textbook "flooding" schedule. It also creates a **read-after-write dependency** between consecutive layers that share a column (chapter 07).
3. **No sharing inside a layer:** Checks inside one layer must not share bits, so they can all run in parallel. The QC structure (next section) guarantees this.

## 6. Quasi-Cyclic (QC) Structure: Where Z Comes From

### The Problem: H Is Huge

A real 5G H matrix has up to 46×384 = 17,664 rows and 68×384 = 26,112 columns. Nobody stores that. Instead it is described by a small **base graph** where every entry is either *empty* or a **shift value P**.

### Expanding a Base Graph

To get H back, replace every base entry with a Z×Z block:

* **Non-empty entry P:** Becomes a **Z×Z circulant**: the identity matrix with its columns rotated right by P.
* **Empty entry:** Becomes a Z×Z zero block.

Here is a 2×3 base graph expanded with Z = 4:

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

How to read the expansion:

* **P = 0 is the plain identity:** The bottom-left block has its 1s on the diagonal.
* **P shifts the diagonal right:** In the P=1 block, row 0 has its 1 in column 1; in the P=3 block, row 0 has its 1 in column 3. Rows near the bottom wrap around to the left edge.
* **Each row and column of a non-empty block holds exactly one 1:** Each circulant is a permutation, so every check in a block touches exactly one bit of that column group.

### What This Means for Hardware

* **One base row = one layer of Z checks:** Those Z checks never share a bit, so they run in **Z parallel lanes**.
* **One base column = a group of Z bits:** Store them as **one wide memory word** of Z lanes.
* **The circulant is a rotation:** It says *which* lane of the column word goes to *which* check lane. **It is a rotation by P, and that is the whole reason this tutorial exists** (chapter 02).

## 7. The 5G Numbers (TS 38.212 §5.3.2)

5G NR defines two base graphs. They compare as follows:

| | BG1 | BG2 |
|---|---|---|
| Base matrix size | 46 × 68 | 42 × 52 |
| Non-empty blocks (edges per lane) | 316 | 197 |
| Information columns | 22 | 10 |
| Max row weight | 19 (row 0) | smaller |
| Max information bits K | 22 × 384 = 8448 | 10 × 384 = 3840 |
| Lifting sizes Z | 51 values, 2…384 | same |

(The counts 316 and 197 were checked by counting the entries of Tables 5.3.2-2 and 5.3.2-3 in the downloaded `ETSI_TS_138212_v17.9.0.pdf`.)

### Lifting Sizes and Shift Values

The 51 lifting sizes are `Z = a × 2^j` with `a ∈ {2,3,5,7,9,11,13,15}` (Table 5.3.2-1). The standard stores one value V per block per set `a`, and the shift actually used is **P = V mod Z**.

### Short BG2 Payloads and Filler Bits

BG2 always has 10 information columns, so K = 10Z. TS 38.212 also defines K_b = 6, 8 or 9 for short BG2 payloads. That value only selects Z; the matrix does not shrink. Information positions the payload doesn't fill are *filler bits*: known zeros that are not transmitted, which the decoder treats as certain.

### Puncturing and Code Rate

* **Punctured bits:** The first 2Z information bits are never transmitted (*punctured*). Their LLRs start at 0 and the decoder fills them in.
* **Rate sets the number of layers:** High-rate transmissions use only the first few base rows. Low-rate ones add more *extension* rows, so the number of layers to process depends on the code rate.

## 8. The Datapath, Finally

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

How to read the datapath:

* **Top and bottom:** The same L memory word is read in natural order and written back in natural order.
* **The two rotators:** They line the column word up with the check lanes (rotate by P) and then undo it (rotate back by P).
* **Everything in between:** The subtract, the CNU and the add are the layered-decoding steps from section 5, one copy per lane.

Every arithmetic box is "Z identical lanes, no interaction between lanes". **The rotator is the only block where lanes talk to each other.**

`model/layered_qc.py` implements this exact flow and checks it bit-exactly against a textbook dense-matrix decoder.

## 9. Exercises

1. **Min-Sum by hand:** A check has inputs [−4, +1, +6]. What are min1, min2, idx, S, and the three outgoing messages (plain Min-Sum)?
2. **Layer parallelism:** Why can all Z checks of one layer be processed in parallel?
3. **Message count:** For BG1 at Z = 384, how many check-to-bit messages are there per iteration?

### Solutions to Selected Exercises

> **Solution to Exercise 1:** min1 = 1 (idx 1), min2 = 4, S = 1 (one negative).
>
> * **Edge 0:** sign = 1^1 = 0 → +, mag = min1 = 1 → **+1**.
> * **Edge 1:** sign = 1^0 = 1 → −, mag = min2 = 4 → **−4**.
> * **Edge 2:** sign = 1^0 = 1 → −, mag = min1 = 1 → **−1**.

> **Solution to Exercise 2:** Each circulant is a permutation matrix: each check row in the block has exactly one 1, in a different column. So the Z checks of a layer touch disjoint bits inside every column group. No two lanes ever write the same L value.

> **Solution to Exercise 3:** 316 blocks × 384 = 121,344 edges. A decoder that handles one block (384 edges) per clock needs about 316 clocks per iteration, plus pipeline overhead.

# 02 · Why rotation? From circulant matrix to shifter

> Goal: see exactly why the decoder needs a circular shifter, which direction
> it must rotate, and why a general-purpose crossbar would be wasteful.

---

## 1. Read the circulant as a wiring table

Take one non-empty block with Z = 4 and P = 1. Its circulant is the identity
with columns rotated right by 1:

```
               variable lane (inside column group c)
                 0  1  2  3
check lane 0  [  0  1  0  0 ]   check 0 uses variable 1
check lane 1  [  0  0  1  0 ]   check 1 uses variable 2
check lane 2  [  0  0  0  1 ]   check 2 uses variable 3
check lane 3  [  1  0  0  0 ]   check 3 uses variable 0
```

Rule: **check lane i uses variable lane (i + P) mod Z.**

The memory word for column group c holds the variables in natural order:

```
memory word:   [ v0  v1  v2  v3 ]
CNU lanes need: [ v1  v2  v3  v0 ]     ← lane i gets v[(i+1) mod 4]
```

That is a **left rotation by P**. In this tutorial:

```
rotl(x, s)[i] = x[(i + s) mod Z]
```

When the CNU lanes are done, the updated values must go back to their home
lanes before the word is written to memory: a **right rotation by P**, which is
`rotl(x, Z − P)`. (Chapter 07 shows how to avoid this second rotation.)

## 2. Every block needs a different rotation

A layer of BG1 can have up to 19 blocks, each with its own P. A block-serial
decoder reads one column word per clock, so the rotator gets a **new shift
value every clock**. When the next code block arrives with a different Z,
the length of the rotation changes as well.

So the rotator needs two inputs besides the data: the shift `s` (changes every
cycle) and the size `Z` (changes per code block).

## 3. Direction conventions will bite you

Papers, standards and code use every combination of left/right and
matrix/vector conventions. Some examples:

| Source | What it says | Equivalent in this tutorial |
|---|---|---|
| TS 38.212 | "I(P) is the identity circularly shifted **to the right** P times" (matrix columns) | vector `rotl(x, P)` |
| Python course LDPC-11 | `output[i] = input[(i − shift) mod Z]` (right rotation) | `rotl(x, −shift)` |
| Song et al. bypass network | one shifter shifts "to right by SV", the other "to left by IN − SV" | same structure as chapter 05, mirrored |

The reliable habit: **before trusting any formula, run Z = 4, P = 1 through it
by hand** and compare against the 4×4 matrix above. This takes two minutes and
prevents a whole class of bugs that are very hard to see in waveforms.

## 4. Why not a crossbar?

A crossbar lets any output take any input: Z output muxes, each Z:1. It can
realise any permutation, and broadcasts as well.

At Z = 384 and W = 8 bits per lane:

| | Crossbar | Rotator (chapters 04–06) |
|---|---|---|
| Patterns it can make | all 384! permutations (and more) | the 384 rotations (×51 sizes) |
| 2:1-mux equivalents per bit | 384 × 383 ≈ 147,000 | 384 × 9 = 3,456 |
| × 8 bits | ≈ 1.18 M | ≈ 27,600 |
| Select bits | 384 × 9 = 3,456 | 9 (the shift value itself) |

The rotator needs only **N log N** hardware because it only has to produce
**N** patterns, not N!. Chapters 03 and 06 explain why log-depth networks of
2×2 switches are enough.

## 5. Could memory addressing do the rotation instead?

The Python course asks this in LDPC-11, and it is a good question.

* With **one lane** (fully serial decoder), yes. To read check lane i you fetch
  variable `(i + P) mod Z` from the memory. Rotation becomes address arithmetic
  and needs no network.
* With **Z lanes in parallel**, the Z values of a column sit in one wide word,
  or in Z separate banks, one per lane. Lane i of the CNU needs data that is
  physically stored in lane `(i + P) mod Z`. An address offset can choose
  *which row* of a bank to read, but it cannot move data *between* banks. The
  data has to cross lanes, and that takes a network.
* Mixed designs exist: P lanes with P < Z, several words per block. There
  addressing handles part of the rotation and a smaller network does the rest.
  This is more complicated; see chapter 07 §7.

## 6. What "a rotator for 5G" must do: the spec for chapters 04–06

```
inputs : din[N lanes × W bits], z (2..384, one of 51 values), shift (0..z−1)
output : dout[i] = din[(i + shift) mod z]   for i < z
         dout[i] = don't care (we drive 0)   for z ≤ i < N
N = 384, W = 6..8
new shift every clock; z changes per code block
```

`model/rotators.py::rotl_ref` is this spec as code, and every design in this
tutorial is checked against it.

---

### Check yourself

<details><summary>Z = 5, P = 3, memory word [a b c d e]. What must the CNU lanes see?</summary>

Lane i gets x[(i + 3) mod 5] → **[d e a b c]**.
</details>

<details><summary>After the CNU, the word [d' e' a' b' c'] must be written back. What rotation, and what is the result?</summary>

Right rotation by 3 (= left rotation by 5 − 3 = 2) → **[a' b' c' d' e']**.
</details>

# 02 · Why Rotation? From Circulant Matrix to Shifter

> **Goal:** See exactly why the decoder needs a circular shifter, which direction it must rotate, and why a general-purpose crossbar would be wasteful.
>
> * **Python Model:** `model/rotators.py::rotl_ref` (the executable spec from §6)

## 1. Read the Circulant as a Wiring Table

A QC-LDPC parity-check matrix is built from Z × Z blocks, and every non-empty block is a circulant: an identity matrix whose columns have been rotated by a shift value P. To a hardware engineer, the most useful way to read such a block is as a **wiring table**: row i tells you which variable lane check lane i must be connected to.

### A Concrete Block (Z = 4, P = 1)

Take one non-empty block with Z = 4 and P = 1. Its circulant is the identity with columns rotated right by 1:

```
               variable lane (inside column group c)
                 0  1  2  3
check lane 0  [  0  1  0  0 ]   check 0 uses variable 1
check lane 1  [  0  0  1  0 ]   check 1 uses variable 2
check lane 2  [  0  0  0  1 ]   check 2 uses variable 3
check lane 3  [  1  0  0  0 ]   check 3 uses variable 0
```

Reading off the single `1` in each row gives the general rule:

* **Wiring rule:** **check lane i uses variable lane (i + P) mod Z.**

### From Wiring Rule to Rotation

The memory word for column group c holds the variables in natural order, but the CNU lanes need them in the order the wiring rule dictates:

```
memory word:   [ v0  v1  v2  v3 ]
CNU lanes need: [ v1  v2  v3  v0 ]     ← lane i gets v[(i+1) mod 4]
```

Every value moves up by one lane, and the value that falls off the top wraps around to the bottom. That is a **left rotation by P**. In this tutorial we write it as:

```
rotl(x, s)[i] = x[(i + s) mod Z]
```

### The Return Trip

When the CNU lanes are done, the updated values must go back to their home lanes before the word is written to memory. That needs the opposite movement, a **right rotation by P**, which is the same as `rotl(x, Z − P)`. In the example above, rotating `[v1 v2 v3 v0]` left by Z − P = 3 restores `[v0 v1 v2 v3]`. (Chapter 07 shows how to avoid this second rotation.)

## 2. Every Block Needs a Different Rotation

A single rotation would be easy to hard-wire. The difficulty is that the shift keeps changing:

* **Per block:** A layer of BG1 can have up to 19 blocks, each with its own P. A block-serial decoder reads one column word per clock, so the rotator gets a **new shift value every clock**.
* **Per code block:** When the next code block arrives with a different Z, the length of the rotation changes as well.

So the rotator needs two inputs besides the data:

| Input | Meaning | Changes |
|---|---|---|
| `s` | the shift | every cycle |
| `Z` | the size of the rotation | per code block |

## 3. Direction Conventions Will Bite You

Section 1 fixed one convention: a left rotation, `rotl(x, s)[i] = x[(i + s) mod Z]`. Papers, standards and code use every combination of left/right and matrix/vector conventions, so the same operation shows up under different names. Some examples:

| Source | What it says | Equivalent in this tutorial |
|---|---|---|
| TS 38.212 | "I(P) is the identity circularly shifted **to the right** P times" (matrix columns) | vector `rotl(x, P)` |
| Python course LDPC-11 | `output[i] = input[(i − shift) mod Z]` (right rotation) | `rotl(x, −shift)` |
| Song et al. bypass network | one shifter shifts "to right by SV", the other "to left by IN − SV" | same structure as chapter 05, mirrored |

The first row is the one that trips people up most often: the standard's *matrix* columns rotate right, yet the *vector* of variables has to rotate left, exactly as the Z = 4 example in Section 1 shows.

**The reliable habit: before trusting any formula, run Z = 4, P = 1 through it by hand** and compare against the 4×4 matrix above. This takes two minutes and prevents a whole class of bugs that are very hard to see in waveforms.

## 4. Why Not a Crossbar?

A crossbar is the obvious general-purpose answer: Z output muxes, each Z:1, so any output can take any input. It can realise any permutation, and broadcasts as well. The question is what that flexibility costs compared with a network that only rotates.

At Z = 384 and W = 8 bits per lane:

| | Crossbar | Rotator (chapters 04–06) |
|---|---|---|
| Patterns it can make | all 384! permutations (and more) | the 384 rotations (×51 sizes) |
| 2:1-mux equivalents per bit | 384 × 383 ≈ 147,000 | 384 × 9 = 3,456 |
| × 8 bits | ≈ 1.18 M | ≈ 27,600 |
| Select bits | 384 × 9 = 3,456 | 9 (the shift value itself) |

The crossbar is more than 40 times larger in the datapath and needs hundreds of times more select bits. **The rotator needs only N log N hardware because it only has to produce N patterns, not N!.** Chapters 03 and 06 explain why log-depth networks of 2×2 switches are enough.

## 5. Could Memory Addressing Do the Rotation Instead?

The Python course asks this in LDPC-11, and it is a good question. The answer depends on how many lanes the decoder processes in parallel:

* **One lane (fully serial decoder):** Yes. To read check lane i you fetch variable `(i + P) mod Z` from the memory. Rotation becomes address arithmetic and needs no network.
* **Z lanes in parallel:** No. The Z values of a column sit in one wide word, or in Z separate banks, one per lane. Lane i of the CNU needs data that is physically stored in lane `(i + P) mod Z`. An address offset can choose *which row* of a bank to read, but it cannot move data *between* banks. **The data has to cross lanes, and that takes a network.**
* **Mixed designs:** These exist too: P lanes with P < Z, several words per block. There addressing handles part of the rotation and a smaller network does the rest. This is more complicated; see chapter 07 §7.

## 6. What "a Rotator for 5G" Must Do: the Spec for Chapters 04–06

Putting Sections 1–5 together gives the specification that every rotator in the following chapters must meet:

```
inputs : din[N lanes × W bits], z (2..384, one of 51 values), shift (0..z−1)
output : dout[i] = din[(i + shift) mod z]   for i < z
         dout[i] = don't care (we drive 0)   for z ≤ i < N
N = 384, W = 6..8
new shift every clock; z changes per code block
```

* **The rotation:** Output lane i takes input lane (i + shift) mod z, which is the left rotation from Section 1, but only over the first z lanes.
* **The unused lanes:** Lanes z … N − 1 carry no data; their outputs are don't-care, and the designs here drive them to 0.
* **The timing:** The shift changes every clock and z changes per code block, as described in Section 2.

`model/rotators.py::rotl_ref` is this spec as code, and every design in this tutorial is checked against it.

## 7. Exercises

1. Z = 5, P = 3, memory word [a b c d e]. What must the CNU lanes see?
2. After the CNU, the word [d' e' a' b' c'] must be written back. What rotation, and what is the result?

### Solutions to Selected Exercises

> **Solution to Exercise 1:** Lane i gets x[(i + 3) mod 5] → **[d e a b c]**.

> **Solution to Exercise 2:** Right rotation by 3 (= left rotation by 5 − 3 = 2) → **[a' b' c' d' e']**.

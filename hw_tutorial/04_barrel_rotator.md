# 04 · The barrel rotator

> Goal: build the simplest real rotator, see why its control is free, and
> learn the physical-design issue that its textbook diagram hides.
> RTL: `rtl/rot_barrel.v`. Model: `model/rotators.py::rotl_barrel`.

---

## 1. The idea: binary decomposition of the shift

Any shift `s < N` is a sum of powers of two, given by its bits:
`s = s[0]·1 + s[1]·2 + s[2]·4 + …`. Rotating by s therefore means:

> rotate by 1 if `s[0]`, then by 2 if `s[1]`, then by 4 if `s[2]`, …

Each step is one column of N 2:1 muxes. **The select of stage k is just
`shift[k]`.** No decoding, no lookup, no arithmetic. That is why the Song paper
says that for the barrel shifter "the SV is the natural control signal".

## 2. Walk through N = 8, s = 5 (binary 101)

```
input                          A B C D E F G H
stage 0  rotate by 1? s[0]=1 → B C D E F G H A
stage 1  rotate by 2? s[1]=0 → B C D E F G H A   (pass through)
stage 2  rotate by 4? s[2]=1 → F G H A B C D E
expected rotl(x, 5)          → F G H A B C D E   ✓
```

(This trace is printed by the model, and the RTL testbench checks every shift.)

## 3. The RTL

```verilog
for (k = 0; k < SW; k = k + 1) begin : g_stage
    for (i = 0; i < N; i = i + 1) begin : g_lane
        localparam SRC = (i + (1 << k)) % N;          // fixed wire, computed at elaboration
        assign stage[k+1][i*W +: W] = shift[k] ? stage[k][SRC*W +: W]
                                               : stage[k][i*W +: W];
    end
end
```

Points to notice:

* `SRC` is a **constant**. Each mux has one input that is a straight wire and
  one that is a fixed long wire. All the "intelligence" is in the wiring.
* **N does not have to be a power of two.** Stage k rotates by `2^k mod N`,
  and rotations compose, so any shift `< N` works. The paper's Fig. 2 is a 7×7
  barrel shifter, and the testbench checks both N = 7 and N = 384.
* Rotations commute, so **the stage order is free.** You can put the 2^8 stage
  first or last. That matters for layout (section 5).

## 4. Cost and timing

| | Value | N = 384, W = 8 |
|---|---|---|
| Stages (mux levels on critical path) | ⌈log2 N⌉ | 9 |
| 2:1 muxes per bit | N·⌈log2 N⌉ | 3,456 |
| Total 2:1 muxes | × W | 27,648 |
| Control logic | none (shift bits drive selects directly) | 0 |
| Fan-out of each shift bit | N × W mux selects | 3,072 → needs a buffer tree |

Nine mux levels plus wire delay fit in one cycle at moderate clock rates. For
high clock rates, put a pipeline register after stage 4 or so. Because the
stages commute, you can choose where to cut without changing the function.
The shift bits for the later stages must then be delayed to match.

## 5. What the textbook picture hides: wires

In stage k, every lane has a wire to the lane 2^k away. In the last stage of
a 384-lane rotator that is 256 lanes away. With 8-bit lanes laid out
side by side, **every lane has a wire crossing about two-thirds of the
datapath**, and in some places hundreds of these wires overlap. At large N,
barrel shifters are usually **wire-limited, not gate-limited**.

Practical consequences:

* Place the long-span stages where routing resources are richest, or
  fold the layout (interleave lanes `0, N−1, 1, N−2, …`) to shorten the worst wires.
* After synthesis, compare post-route timing with post-synthesis timing.
  Expect them to disagree for rotators.
* This is another reason Banyan-style networks are attractive. Their
  recursive structure maps to a recursive floorplan.

## 6. What the barrel rotator **cannot** do

1. **Rotate a vector shorter than N.** With N = 8 and a 5-element vector
   `[A B C D E . . .]`, rotation by 2 should give `[C D E A B]`, but the barrel
   rotator gives `[C D E . . . A B]`. Its wrap-around point is fixed at lane N.
   Chapter 05 fixes this.
2. **Process several small vectors independently.** Every stage moves data
   across the whole bus, so you cannot split it into two half-size rotators
   with different shifts. Chapter 06 fixes this with a Banyan.

---

### Exercises

1. Run `python3 -c "from rotators import *; t=[]; rotl_barrel(list('ABCDEFG'),6,t); print(t)"`
   inside `model/`. Check the 7-lane trace by hand.
2. Change `rot_barrel.v` so that the stages run from largest shift to smallest.
   Rerun `./run_tests.sh`. It should still pass, because rotations commute.
3. Add a parameter `PIPE_AFTER` that inserts a register after that stage, with
   matching delay on the remaining shift bits. Extend the testbench to account
   for the latency.

<details><summary>Answer to 1</summary>

s = 6 = 110b. Stage 0 does nothing. Stage 1 gives C D E F G A B. Stage 2
(rotate by 4) gives G A B C D E F. Check: rotl(ABCDEFG, 6)[0] = x[6] = G ✓.
</details>

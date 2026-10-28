# 03 · Switching Basics for RTL Engineers

> **Goal:** Learn the vocabulary and mental models of switching networks, built up from the 2:1 mux you already know. After this chapter, "a rearrangeably non-blocking Benes network" and "a Banyan has the unique-path property" will mean something concrete.
>
> * **RTL:** `rtl/switches.v`
> * **Figure scripts:** `figures/make_banyan8.py`, `figures/make_benes8.py`

## 1. The Problem a Switching Network Solves

You have N input lanes and N output lanes. Each cycle you want a **permutation**: every output takes exactly one input and every input goes to exactly one output. The network's **configuration** (its control bits) decides which permutation you get.

Three questions decide whether a network is a good fit:

| Question | Metric |
|---|---|
| Which permutations can it make? | *capability*: all N!? only rotations? |
| How big and how deep is the datapath? | *cost*: mux count × W bits; *depth*: mux levels on the critical path |
| How hard is it to work out the control bits from what you want? | *control complexity*: often the hidden cost |

**The third row is easy to overlook, and it is the main topic of the Song et al. paper.**

## 2. From Mux to 2×2 Switch

### The 2×2 Switch

A **2×2 switch** has two inputs, two outputs, and one control bit. It either passes its inputs straight through (**bar**) or trades them (**cross**):

```
   bar (swap=0)            cross (swap=1)

 in0 ───────── out0       in0 ─╲   ╱─ out0
                                 ╳
 in1 ───────── out1       in1 ─╱   ╲─ out1
```

In RTL it is just **two 2:1 muxes sharing a select**:

```verilog
assign out0 = swap ? in1 : in0;
assign out1 = swap ? in0 : in1;
```

The module lives in `rtl/switches.v`. The word `cross` is reserved in SystemVerilog, so the port is called `swap`.

### The 3×3 Rotating Switch

A **3×3 rotating switch** (used in chapter 06) takes three inputs and produces one of the three cyclic orders `(0,1,2)`, `(1,2,0)`, `(2,0,1)`. It is three 3:1 muxes with a 2-bit control.

## 3. The Crossbar: Maximum Flexibility, Maximum Cost

The simplest network that can make any permutation is the crossbar: give every output its own N:1 mux over all inputs.

```
          in0  in1  in2  in3
out0  ──── ●────●────●────●      each output = one N:1 mux
out1  ──── ●────●────●────●      N² crosspoints
out2  ──── ●────●────●────●      any permutation, even broadcast
out3  ──── ●────●────●────●      control: log2 N select bits per output
```

* **Cost and depth:** Cost N² (≈ N(N−1) 2:1 muxes), depth ⌈log₂ N⌉ mux levels.
* **Control:** Trivial *if* you already know, for every output, which input it wants.
* **Scaling:** Fine for N = 8. At N = 384 it costs about 147k muxes per bit (chapter 02).

## 4. Multistage Networks: Trading Flexibility for Cost

The crossbar's N² cost comes from building everything in one huge stage. The alternative is to use **several stages of small switches** with fixed wiring between them. Typically there are log₂ N stages of N/2 2×2 switches each.

### Counting Argument: How Many Switches Do You Need for *Every* Permutation?

Before looking at specific networks, a simple count tells us which ones *could* possibly make every permutation. A network with S binary switches has at most 2^S configurations. To produce all N! permutations you need

```
2^S ≥ N!   ⟹   S ≥ log2(N!) ≈ N·log2 N − 1.44·N
```

Comparing that bound with the switch counts of the two networks in this chapter:

| N | log2(N!) | Banyan switches (N/2)·log2 N | Benes switches (N/2)(2·log2 N − 1) |
|---|---|---|---|
| 8 | 15 | 12 | 20 |
| 64 | 296 | 192 | 352 |
| 384 (using ⌈log2 384⌉ = 9) | 2748 | 1728 | 3264 |

* **Banyan:** Has too few switches to make every permutation; it is *blocking*.
* **Benes:** Has enough, and it can in fact make every permutation.

**For LDPC we only need the N rotations, and a Banyan can make all of them** (chapter 06 proves this by construction).

## 5. The Banyan (Butterfly) Network

### Recursive Structure

A Banyan is built recursively. An N-lane Banyan is one column of N/2 switches followed by **two** N/2-lane Banyans:

```
8-lane Banyan: which lanes each 2x2 switch joins

            stage 0               stage 1                stage 2
            span 4                span 2                 span 1
            (whole bus)           (each half)            (each quarter)

switches    (0,4) (1,5)           (0,2) (1,3)            (0,1) (2,3)
            (2,6) (3,7)           (4,6) (5,7)            (4,5) (6,7)

            └─ one 8-lane ─┘      └ two 4-lane Banyans ┘  └ four 2-lane ┘
```

In this tutorial's version, switch k of stage 0 joins lane k with lane k + N/2. Each switch sends one value to the upper half and one to the lower half. The two halves are then handled independently.

### Worked Example: Rotating A…H Left by 3

The figure shows the same 8-lane Banyan, wired and carrying data, set up to rotate A…H left by 3. The output it must produce is `out[i] = in[(i + 3) mod 8]`, which is D E F G H A B C. Each box is one 2×2 switch. The label on a box (for example `0↔4`) gives the two lanes it joins, and the circles show the value on every lane between stages.

![8-lane Banyan, 3 stages of four 2×2 switches, rotating left by 3. Orange boxes cross, black boxes pass straight (bar). Generated by figures/make_banyan8.py, which checks the result against the reference rotation.](figures/banyan8.svg)

Follow it stage by stage:

| Stage | Pairs | Setting for shift 3 | Lanes afterwards |
|---|---|---|---|
| in | | | A B C D · E F G H |
| 0 (span 4) | 0↔4, 1↔5, 2↔6, 3↔7 | first three cross, last bar | E F G D · A B C H |
| 1 (span 2) | 0↔2, 1↔3 in each half | first bar, second cross | E D G F · A H C B |
| 2 (span 1) | 0↔1, 2↔3, … | all cross | **D E F G · H A B C** |

### How to Read the Banyan Diagram

* **Every stage has the same hardware:** Four 2×2 switches, which is 8 two-input muxes per data bit. Three stages give `(N/2)·log2 N = 12` switches. Only the wiring span changes: 4, then 2, then 1.
* **Stage 0 sorts values into halves:** After it, the upper half holds E F G D. These are exactly the four values that outputs 0–3 need (D E F G), just in the wrong order. The lower half likewise holds the four values for outputs 4–7.
* **The two halves never mix again:** Stages 1 and 2 are two separate 4-lane Banyans. Both of them rotate their half left by `3 mod 4 = 3`. This is the recursion from the start of this section.
* **Control is cheap and shared:** In every stage, switch k's setting follows one rule, `swap = a XOR (k < b)`. Here `a` is one bit of the shift and `b` is the shift mod the span, which is just the lower bits of the shift. Both halves of stage 1 get the *same* control vector. Chapter 06 derives this rule. For now, notice that the rule only ever produces a run of switches with one setting followed by a run with the other ("first three cross, last bar"), never an arbitrary pattern.

To try other shifts, open the **Rotator lab** on the web page (`site/serve.sh`), pick Banyan, and change the shift. It shows the lane values after every stage.

### The Unique-Path Property

From any input to any output there is exactly one route. At each stage the route must turn toward the half that contains the destination. This has two consequences:

* **Routing is simple:** Each switch decides from local information.
* **The network is *blocking*:** When two values need the same internal link, one of them loses.

### Blocking Example (N = 4)

A 4-lane Banyan has 4 switches, so 2^4 = 16 configurations, but there are 24 permutations. Some permutations must therefore be impossible. Ask for output order **A C B D** (lane 0 ← A, lane 1 ← C, lane 2 ← B, lane 3 ← D):

1. Stage 0 pairs lanes (0,2) = (A,C) and (1,3) = (B,D).
2. Outputs 0 and 1 (the upper half) need **A and C**. Both are in the *same* stage-0 switch, which can send only one value up. **Blocked.**

Enumerating all 16 configurations (try it in Python) shows that 8 permutations are unreachable: ACBD, ACDB, BDAC, BDCA, CABD, CADB, DBAC, DBCA. **All four rotations (ABCD, BCDA, CDAB, DABC) are reachable. That is the property LDPC relies on.**

### Why a Banyan Instead of a Barrel Shifter?

Both cost N·log₂ N, so the difference is not area. It is the Banyan's recursive structure: **if the first f stages are forced to "bar", the network splits cleanly into 2^f independent smaller rotators.** That is how one 384-lane network can process several small code blocks at once (chapter 06).

## 6. The Benes Network

### Structure

A Benes network is a Banyan followed by a mirrored Banyan, sharing the middle stage: 2·log₂ N − 1 stages.

```
 input        upper N/2 Benes         output
 switch  ──►                      ──► switch
 column  ──►  lower N/2 Benes     ──► column
```

### Worked Example: Routing an Order a Banyan Cannot Make

To see what the extra stages buy, take a target the 8-lane Banyan cannot reach: the FFT *bit-reversal* order. Output lane i takes input lane `reverse_bits(i)`, giving A E C G B F D H. A Banyan can't do this, for the same reason as the 4-lane A C B D example above: A and E enter the same stage-0 switch (`0↔4`), yet both must reach the upper half (outputs 0 and 1).

![8-lane Benes network, 5 stages of four 2×2 switches, routing A–H into bit-reversed order A E C G B F D H. The shaded middle stages are two 4-lane Benes networks. Generated by figures/make_benes8.py, which routes it with the looping algorithm and checks the result.](figures/benes8.svg)

### How to Read the Benes Diagram

* **Five stages, spans 4 · 2 · 1 · 2 · 4:** These are a Banyan's stages plus the same stages mirrored, sharing the span-1 stage in the middle. That makes 5 × 4 = 20 switches, compared with 12 for the Banyan (the last column of the counting table above).
* **The recursion is visible:** Stage 0 is the input column, stage 4 is the output column, and the shaded middle is two complete 4-lane Benes networks. Each of those is again an input column, two 2-lane networks (one switch each), and an output column.
* **How A and E get past the conflict:** In stage 0, A stays in the upper sub-network and E goes to the lower one, just as in a Banyan. The difference is the extra output column. Output lanes 0 and 1 belong to *different* output switches (`0↔4` and `1↔5`), and each output switch takes one value from the upper sub-network and one from the lower. So A arrives at lane 0 from above, and E arrives at lane 1 from below through switch `1↔5`, which crosses.
* **No formula sets the switches:** Compare the Banyan figure, where every stage followed `swap = a XOR (k < b)`. Here the settings come from the looping algorithm. Only 6 of the 20 switches cross, in no regular pattern.

### The Looping Algorithm on This Example

The looping algorithm decides, for every value, whether it travels through the upper or the lower sub-network. Two rules constrain the choice:

1. The two values at one *input* switch must go to different sub-networks.
2. The two values wanted at one *output* switch must arrive from different sub-networks.

Start with any value and follow the chain of rules until it closes into a loop:

| Step | Value | Side | Reason |
|---|---|---|---|
| 1 | A | upper | free choice |
| 2 | E | lower | shares input switch `0↔4` with A (rule 1) |
| 3 | F | upper | output switch `1↔5` wants E (lane 1) and F (lane 5); E comes from below (rule 2) |
| 4 | B | lower | shares input switch `1↔5` with F (rule 1) |
| — | A | upper ✓ | output switch `0↔4` wants A and B; B is lower, so A must be upper. That agrees with step 1, so the loop closes |
| 5 | C | upper | free choice: start a new loop |
| 6 | G | lower | shares input switch `2↔6` with C |
| 7 | H | upper | output switch `3↔7` wants G and H |
| 8 | D | lower | shares input switch `3↔7` with H; then output switch `2↔6` wants C and D, so C upper ✓, loop closes |

The upper sub-network gets A F C H and the lower one gets E B G D. That is exactly the second column of values in the figure. The input-column switches follow directly: `0↔4` and `2↔6` are bar, and `1↔5` and `3↔7` cross. Then the same procedure runs again inside each 4-lane sub-network, and so on down to single switches.

Every loop is a chain of steps, and each step depends on the previous one. That is fine in software, but you can't evaluate the chain in parallel in one clock cycle. This sequential control is the price of the Benes network's flexibility.

### What "Rearrangeably Non-Blocking" Means

* **Rearrangeably non-blocking:** The network can realise *any* permutation, provided you are allowed to choose all switch settings together. Some other permutation's settings may have to be rearranged first, hence "rearrangeably".
* **Why that is enough here:** For a datapath that is reconfigured from scratch every clock, "rearrangeable" is all you need. (*Strictly* non-blocking, where new connections never disturb existing ones, matters in telephone switches, not here.)
* **The catch is control:** Finding switch settings for an arbitrary permutation needs the *looping algorithm*, a sequential procedure that is hard to do in one clock cycle. Hardware usually precomputes the settings and stores them in a ROM.

### Benes Networks Elsewhere

Huang & Walrand (arXiv 1208.0561, next to this repo) use exactly this topology (their Fig. 2 and Section III-A) to connect servers in a data center. The rest of their paper is about queues and scheduling packets through it. For LDPC the key point is simple: **a Benes network can do far more than rotations, and you pay for that in stages and control logic.** That is why LDPC decoders use Banyan-type networks or barrel shifters.

## 7. Shift vs Rotate

The two operations differ only in what happens to the lanes that fall off the end:

| Operation | Lane i receives | Lanes that "fall off" |
|---|---|---|
| logical left shift by s | x[i + s] or 0 | lost; zeros come in |
| left **rotate** by s | x[(i + s) mod N] | wrap around to the other end |

Chapter 05 builds a variable-size rotator out of two *shifters*, so keep both in mind.

## 8. Vocabulary Summary

| Term | Meaning |
|---|---|
| lane / port | one W-bit data element position |
| stage | one column of switches; one mux level of delay |
| bar / cross | the two states of a 2×2 switch |
| configuration | the full set of control bits for one cycle |
| blocking | some permutations are impossible because two paths need one link |
| rearrangeably non-blocking | every permutation is possible if all switches are set together |
| unique path | exactly one route from each input to each output (Banyan) |
| control generation | the logic that turns "shift by s, size Z" into switch bits |
| multi-frame | splitting one network into several independent smaller ones |

## 9. Exercises

1. A 2×2 switch is two 2:1 muxes. How many 2:1 muxes per bit does an 8-lane Banyan use, and how many does an 8-lane barrel rotator use?
2. Why is a Benes network overkill for a QC-LDPC decoder?

### Solutions to Selected Exercises

> **Solution to Exercise 1:** Banyan: 3 stages × 4 switches × 2 = 24. Barrel: 3 stages × 8 lanes = 24. They are the same. The two differ in structure and control, not in mux count.

> **Solution to Exercise 2:** It can make all N! permutations, but QC-LDPC needs only rotations. You would pay about twice the stages, plus a hard control problem (the looping algorithm), for flexibility you never use.

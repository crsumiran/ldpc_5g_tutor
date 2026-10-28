# 07 · Decoder Architecture: Putting the Rotator to Work

> **Goal:** Build a top-level architecture for a block-serial, Z-parallel, layered 5G decoder: where each memory and unit sits, how wide it is, where the pipeline hazards are, and how to estimate throughput.
>
> * **Python Model:** `model/layered_qc.py` (dense vs two-rotator vs one-rotator, bit-exact)

## 1. The Architecture Family

The rotator from chapter 06 is only one block of a decoder, so the first question is how the rest of the decoder is organized around it. Decoders differ mainly in **how many blocks of H they process per clock**, and that one choice fixes how many rotators you need:

| Style | Blocks per clock | Rotators | Notes |
|---|---|---|---|
| Fully parallel | all 316 | 316 (hard-wired for one code) | Fixed codes only; impractical for 5G's 51 Z values |
| Row-parallel | one whole layer (up to 19) | up to 19 | Fast, large, wasted at low row weights |
| **Block-serial, Z-parallel** | **1** | **1** | **The usual starting point for a flexible 5G decoder** |
| Partially parallel (P < Z lanes) | a slice of a block | 1 smaller | Small area; rotation spans several words (§7) |

This chapter uses **block-serial, Z-parallel with N = 384 lanes**. It is the simplest design that handles all of 5G, and every serious design is a variation on it.

## 2. Top Level

The block diagram below shows the whole decoder. A controller walks the base graph and feeds column addresses and shifts to the datapath; the datapath reads a column word from the L memory, rotates it, subtracts the old check-to-variable message, and feeds the result to 384 check-node units (CNUs):

```
                    ┌──────────────── controller ────────────────┐
                    │ base-graph ROM: (row, col, V) for BG1/BG2   │
                    │ shift table:   P = V mod Z  (per Z config)  │
                    │ layer schedule, iteration count, stop logic │
                    └───┬──────────────┬─────────────┬────────────┘
                        │ col addr     │ shift/Z     │ layer, edge idx
                        ▼              ▼             ▼
 LLR in ─► ┌──────────┐ rd ┌────────┐   ┌───────────────┐   ┌──────────────┐
           │ L memory │───►│ROTATOR │──►│ Q = L − R_old │──►│ CNU × 384    │
           │ 68 × 384 │    │ (ch.6) │   └──────┬────────┘   │ min1 min2    │
           │ × W_L    │    └────────┘          │            │ idx sign     │
           └──────────┘                        ▼            └──────┬───────┘
                ▲                        ┌──────────┐              │
                │ wr                     │ Q FIFO   │              ▼
                │                        └────┬─────┘       ┌─────────────┐
                │   ┌────────────────┐        │             │ R memory    │
                └───│ L = Q + R_new  │◄───────┴─────────────│ (compressed)│
                    └────────────────┘   R_new decompress   └─────────────┘
```

### Per-Layer Flow (Two Phases)

Each layer is processed in two phases. The first streams every block of the row through the CNUs to find the row's minima; the second uses those finished minima to update every column the row touches.

**Phase 1, read and reduce** (one clock per block in the row, d_c clocks):

1. Read column word `L[c]` (384 × W_L bits).
2. Rotate by P (or by the delta, §4).
3. `Q = L − R_old`, where R_old is decompressed from this layer's entry in R memory.
4. Push Q into the FIFO. The CNU lanes update their running min1, min2, idx and sign.

**Phase 2, update and write** (d_c clocks):

1. Form R_new for each edge from the finished {min1, min2, idx, signs} (chapter 01 §4).
2. `L_new = Q + R_new` (saturating).
3. Rotate back (or not, §4) and write `L[c]`.
4. Store the compressed R_new in R memory.

Run back to back, the two phases cost 2·d_c clocks per layer. **Overlapping phase 2 of layer ℓ with phase 1 of layer ℓ+1 brings the cost down to about d_c clocks per layer**, at the price of the hazards in §5.

## 3. Memories and Word Widths

Before sizing anything, fix the word widths. Typical values are:

* **Channel LLR:** 6 bits.
* **APP value:** W_L = 8 bits.
* **Message:** W_R = 6 bits.

All add and subtract operations **saturate** (Python course LDPC-14/15). With these widths, the memories for the largest case come out as follows:

| Memory | Contents | Size for BG1, Z = 384 |
|---|---|---|
| L (APP) | 68 column words × 384 lanes × 8 b | 208,896 b ≈ 25.5 KiB |
| R, uncompressed | 316 blocks × 384 × 7 b (sign + 6) | 849,408 b ≈ 104 KiB |
| R, compressed | per layer & lane: min1, min2 (6 b each), idx (5 b); plus 1 sign bit per edge | 46·384·17 + 316·384 = 421,632 b ≈ 51 KiB |
| Q FIFO | up to 19 words × 384 × 8 b (depends on pipeline) | ≈ 58 kb |
| Shift table | 316 × 9-bit P (+ precomputed Z − P, §5 of ch. 05) | ≈ 6 kb |

### Where the Area Goes

* **Memories dominate area:** Ren et al. (2023, in `references/`) spend real effort compressing them.
* **The rotator is the largest *logic* block:** At W = 8, one IBN+bypass rotator is about 58k 2:1 muxes (7,296 × 8).
* **The 384 CNU lanes are mostly comparators.**

**Memory port note:** the L memory needs one read and one write per clock, each 384 × 8 = 3,072 bits wide. That is usually several SRAM macros side by side, or a register file. It is a physical-design decision worth making early.

## 4. One Rotator Instead of Two: The Delta-Shift Trick

The naive flow rotates **forward by P on read** and **back by P on write**, which needs two 384-lane rotators. Since the rotator is the largest logic block (§3), removing one of them is worth a little bookkeeping.

**The trick: never rotate back.** Write the word back **in its rotated order** and record that rotation, `cur[c] = P`. The next time column c is read, with shift P′, you need `rotl(natural, P′)`. Memory holds `rotl(natural, cur[c])`, so rotate by the **difference**:

```
read rotation  = (P′ − cur[c]) mod Z       ← one rotator, read side only
write rotation = none
after writing:  cur[c] = P′
at the end:     rotate each output column by −cur[c] (reuse the same rotator)
```

### Why the Extra Control Is Cheap

* **The mod is one subtract plus a conditional add:** Both values are already `< Z`, so the difference lies between −(Z − 1) and Z − 1, and adding Z when it is negative is enough.
* **The deltas can be precomputed:** The schedule is static, so the deltas can be **precomputed per Z** like the shifts themselves.
* **One subtlety, the first iteration:** The first use of each column in iteration 1 starts from `cur = 0`, while in later iterations it starts from the last P used. Precompute both tables or keep a small `cur[]` register file (68 × 9 bits).

### Golden Model

`model/layered_qc.py` implements `decode_qc` (two rotators) and `decode_delta` (one rotator). On 30 random QC codes it checks that both are **bit-exact** with a textbook dense-matrix layered decoder. Use it as the golden model when you build this in RTL.

## 5. Pipeline Hazards (This Will Feel Familiar)

Layered decoding has a **read-after-write dependency**: if layer ℓ+1 uses column c, it must read the value that layer ℓ wrote for c. With a pipeline of depth D between the read of c in phase 1 and its write in phase 2, layer ℓ+1 can read c too early.

**This is exactly a CPU RAW hazard, and the fixes are the ones you already know:**

| Fix | CPU analogy | Cost |
|---|---|---|
| Stall until the write lands | interlock | lost cycles |
| Reorder blocks inside a layer: write shared columns early in ℓ, read them late in ℓ+1 | instruction scheduling | compile-time work per BG/Z (the schedule is static) |
| Reorder layers | instruction scheduling | changes convergence slightly |
| Forward L_new straight to the read side | bypass network | muxes; tricky with the delta-shift trick (the forwarded word is in a different rotation) |

Chang et al. (2025, in `references/`) treat choosing the layer order as a travelling-salesman problem that minimizes idle cycles.

## 6. Throughput and Latency Estimate

With one block per clock, the cycle count of an iteration is simply the number of blocks processed plus whatever stalls and pipeline overhead each layer adds. Latency and throughput follow directly:

```
cycles_per_iteration = Σ over processed layers ( d_c(layer) + stall/overhead(layer) )
latency  = iterations × cycles_per_iteration / f_clk   (+ load/unload)
throughput = K / latency
```

### Worked Example (BG1, Z = 384, K = 8448)

At the lowest rate all 46 layers are processed:

```
blocks             = 316
overhead           ≈ 4 cycles × 46 layers = 184
cycles/iteration   ≈ 500
iterations         = 8
f_clk              = 500 MHz
latency            = 8 × 500 / 500 MHz = 8 µs
throughput         = 8448 / 8 µs ≈ 1.06 Gb/s
```

### How the Estimate Moves with Rate and Z

* **High code rates:** Only the first few layers are processed, so cycles per iteration drop sharply and throughput goes up.
* **Small Z:** The same cycle count carries far fewer bits, so throughput drops in proportion **unless** the rotator and CNUs run in multi-frame mode (chapter 06 §5).

**That is the system-level reason multi-frame rotators exist.**

## 7. When Lanes < Z (Partially Parallel)

To save area, the datapath can have P lanes with P < Z. A column word then spans ⌈Z/P⌉ memory words, and a rotation by s means three things at once: "read words in a rotated order, **and** rotate within words, **and** stitch two partial words at the seam". Control becomes much harder, which is why the Z-parallel design comes first.

Pourjabar & Choi (2021, in `references/`) is a readable example of a design built for Z ≤ 96 with multi-block parallelism at smaller Z.

## 8. Stopping Early

Iterating to the maximum every time wastes power and latency. Common approaches, cheapest first:

* **Sign-stability check:** Stop when no hard decision changed during a full iteration *and* every check processed in that iteration was satisfied by its own updated values. Cheap; computed per layer as you go.
* **Full syndrome:** After an iteration, compute H·x̂ for all checks. Exact, but needs another pass over the matrix.
* **CRC aided:** Stop when the code block's CRC passes (needs the CRC unit).

Always simulate the chosen rule against the golden model. **Stopping too early costs error-rate performance.**

## 9. Exercises

1. **Throughput at small Z:** Recompute the throughput example for Z = 104 (same BG1, all 46 layers, single frame). Then assume the rotator and CNUs can run 3 frames of 104 lanes in parallel. What is the new throughput?
2. **Watching the deltas:** In `layered_qc.py`, make `decode_delta` print the delta it uses on each read. Confirm that some deltas are 0, and explain why that read needs no rotation.
3. **Forwarding under the delta-shift trick:** Sketch the forwarding path for §5 under the delta-shift trick. Which rotation does the forwarded word need?

### Solutions to Selected Exercises

> **Solution to Exercise 1:**
> K = 22 × 104 = 2288 bits. Latency is unchanged at 8 µs (the cycle count does not depend on Z when one block takes one clock). Throughput ≈ 2288 / 8 µs ≈ 0.29 Gb/s. With 3 frames (3 code blocks in lockstep, 312 of 384 lanes busy), it is ≈ 0.86 Gb/s.

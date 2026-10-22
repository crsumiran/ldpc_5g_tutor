# 07 · Decoder architecture: putting the rotator to work

> Goal: a top-level architecture for a block-serial, Z-parallel, layered 5G
> decoder. Where each memory and unit sits, how wide it is, where the
> pipeline hazards are, and how to estimate throughput.
> Model: `model/layered_qc.py` (dense vs two-rotator vs one-rotator, bit-exact).

---

## 1. The architecture family

Decoders differ mainly in **how many blocks of H they process per clock**:

| Style | Blocks per clock | Rotators | Notes |
|---|---|---|---|
| Fully parallel | all 316 | 316 (hard-wired for one code) | Fixed codes only; impractical for 5G's 51 Z values |
| Row-parallel | one whole layer (up to 19) | up to 19 | Fast, large, wasted at low row weights |
| **Block-serial, Z-parallel** | **1** | **1** | **The usual starting point for a flexible 5G decoder** |
| Partially parallel (P < Z lanes) | a slice of a block | 1 smaller | Small area; rotation spans several words (§7) |

This chapter uses **block-serial, Z-parallel with N = 384 lanes**. It is the
simplest design that handles all of 5G, and every serious design is a
variation on it.

## 2. Top level

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

### Per-layer flow (two phases)

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

Overlapping phase 2 of layer ℓ with phase 1 of layer ℓ+1 brings the cost
down to about **d_c clocks per layer**, at the price of the hazards in §5.

## 3. Memories and word widths

Typical widths: channel LLR 6 bits, APP value W_L = 8 bits, message W_R = 6 bits.
All add and subtract operations **saturate** (Python course LDPC-14/15).

| Memory | Contents | Size for BG1, Z = 384 |
|---|---|---|
| L (APP) | 68 column words × 384 lanes × 8 b | 208,896 b ≈ 25.5 KiB |
| R, uncompressed | 316 blocks × 384 × 7 b (sign + 6) | 849,408 b ≈ 104 KiB |
| R, compressed | per layer & lane: min1, min2 (6 b each), idx (5 b); plus 1 sign bit per edge | 46·384·17 + 316·384 = 421,632 b ≈ 51 KiB |
| Q FIFO | up to 19 words × 384 × 8 b (depends on pipeline) | ≈ 58 kb |
| Shift table | 316 × 9-bit P (+ precomputed Z − P, §5 of ch. 05) | ≈ 6 kb |

**Memories dominate area.** Ren et al. (2023, in `references/`) spend real
effort compressing them. The rotator is the largest *logic* block. At W = 8,
one IBN+bypass rotator is about 58k 2:1 muxes (7,296 × 8). The 384 CNU lanes
are mostly comparators.

Memory port note: the L memory needs one read and one write per clock, each
384 × 8 = 3,072 bits wide. That is usually several SRAM macros side by side,
or a register file. It is a physical-design decision worth making early.

## 4. One rotator instead of two: the delta-shift trick

The naive flow rotates **forward by P on read** and **back by P on write**:
two 384-lane rotators.

**Trick:** never rotate back. Write the word back **in its rotated order** and
record that rotation, `cur[c] = P`. The next time column c is read, with shift
P′, you need `rotl(natural, P′)`. Memory holds `rotl(natural, cur[c])`, so
rotate by the **difference**:

```
read rotation  = (P′ − cur[c]) mod Z       ← one rotator, read side only
write rotation = none
after writing:  cur[c] = P′
at the end:     rotate each output column by −cur[c] (reuse the same rotator)
```

The mod is cheap here: both values are already `< Z`, so it is one subtract
plus a conditional add of Z. The schedule is static, so the deltas can be
**precomputed per Z** like the shifts themselves. There is one subtlety: the
first use of each column in iteration 1 starts from `cur = 0`, while in later
iterations it starts from the last P used. Precompute both tables or keep a
small `cur[]` register file (68 × 9 bits).

`model/layered_qc.py` implements `decode_qc` (two rotators) and `decode_delta`
(one rotator). On 30 random QC codes it checks that both are **bit-exact**
with a textbook dense-matrix layered decoder. Use it as the golden model
when you build this in RTL.

## 5. Pipeline hazards (this will feel familiar)

Layered decoding has a **read-after-write dependency**: if layer ℓ+1 uses
column c, it must read the value that layer ℓ wrote for c. With a pipeline of
depth D between the read of c in phase 1 and its write in phase 2, layer ℓ+1
can read c too early. This is exactly a CPU RAW hazard, and the fixes are the
ones you already know:

| Fix | CPU analogy | Cost |
|---|---|---|
| Stall until the write lands | interlock | lost cycles |
| Reorder blocks inside a layer: write shared columns early in ℓ, read them late in ℓ+1 | instruction scheduling | compile-time work per BG/Z (the schedule is static) |
| Reorder layers | instruction scheduling | changes convergence slightly |
| Forward L_new straight to the read side | bypass network | muxes; tricky with the delta-shift trick (the forwarded word is in a different rotation) |

Chang et al. (2025, in `references/`) treat choosing the layer order as a
travelling-salesman problem that minimizes idle cycles.

## 6. Throughput and latency estimate

```
cycles_per_iteration = Σ over processed layers ( d_c(layer) + stall/overhead(layer) )
latency  = iterations × cycles_per_iteration / f_clk   (+ load/unload)
throughput = K / latency
```

Worked example (BG1, Z = 384, K = 8448, lowest rate, so all 46 layers):

```
blocks             = 316
overhead           ≈ 4 cycles × 46 layers = 184
cycles/iteration   ≈ 500
iterations         = 8
f_clk              = 500 MHz
latency            = 8 × 500 / 500 MHz = 8 µs
throughput         = 8448 / 8 µs ≈ 1.06 Gb/s
```

High code rates process only the first few layers, so cycles per iteration
drop sharply and throughput goes up. At small Z, the same cycle count carries
far fewer bits, so throughput drops in proportion **unless** the rotator and
CNUs run in multi-frame mode (chapter 06 §5). That is the system-level reason
multi-frame rotators exist.

## 7. When lanes < Z (partially parallel)

If the datapath has P lanes with P < Z (to save area), a column word spans
⌈Z/P⌉ memory words. A rotation by s then means "read words in a rotated
order, **and** rotate within words, **and** stitch two partial words at the
seam". Control becomes much harder, which is why the Z-parallel design comes
first. Pourjabar & Choi (2021, in `references/`) is a readable example of a
design built for Z ≤ 96 with multi-block parallelism at smaller Z.

## 8. Stopping early

Iterating to the maximum every time wastes power and latency. Common
approaches, cheapest first:

* **Sign-stability check:** stop when no hard decision changed during a full
  iteration *and* every check processed in that iteration was satisfied by
  its own updated values. Cheap; computed per layer as you go.
* **Full syndrome:** after an iteration, compute H·x̂ for all checks. Exact,
  but needs another pass over the matrix.
* **CRC aided:** stop when the code block's CRC passes (needs the CRC unit).

Always simulate the chosen rule against the golden model. Stopping too early
costs error-rate performance.

---

### Exercises

1. Recompute the throughput example for Z = 104 (same BG1, all 46 layers,
   single frame). Then assume the rotator and CNUs can run 3 frames of 104
   lanes in parallel. What is the new throughput?
2. In `layered_qc.py`, make `decode_delta` print the delta it uses on each read.
   Confirm that some deltas are 0, and explain why that read needs no rotation.
3. Sketch the forwarding path for §5 under the delta-shift trick. Which rotation
   does the forwarded word need?

<details><summary>Answer to 1</summary>

K = 22 × 104 = 2288 bits. Latency is unchanged at 8 µs (the cycle count does
not depend on Z when one block takes one clock). Throughput ≈ 2288 / 8 µs ≈
0.29 Gb/s. With 3 frames (3 code blocks in lockstep, 312 of 384 lanes busy),
it is ≈ 0.86 Gb/s.
</details>

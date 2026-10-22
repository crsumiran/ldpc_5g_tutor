# Building LDPC Decoder Hardware: switching and rotation networks

A hardware companion to the Python LDPC course in this repo. It is written for
an RTL engineer who knows datapaths, pipelines and memories well but has never
studied switching networks, barrel shifters or channel coding.

By the end you should be able to:

1. Say in one page what a 5G LDPC decoder does and which blocks it needs.
2. Explain why the decoder's main interconnect is a **circular shifter**.
3. Design, verify and compare four rotator architectures: **barrel**, **QSN**
   (variable size), **Banyan**, and the **Improved Banyan Network (IBN)** from
   the Song/Cui/Wang paper in the parent folder.
4. Sketch a layered decoder top level and estimate its throughput.
5. Read the switching-network papers without getting lost in their notation.

Everything here comes with code that runs. The Python golden models and the
Verilog are checked against each other. The RTL passes an exhaustive test over
all 51 5G lifting sizes and every shift value.

---

## Reading order

| # | Chapter | What you get | Time |
|---|---------|--------------|------|
| 00 | [The application](00_the_application.md) | What the decoder must do, as a spec | 15 min |
| 01 | [LDPC for RTL engineers](01_ldpc_for_rtl_engineers.md) | The algorithm as a datapath: H, Z, layers, Min-Sum | 40 min |
| 02 | [Why rotation?](02_why_rotation.md) | How the matrix turns into a shifter; direction conventions | 25 min |
| 03 | [Switching basics](03_switching_basics.md) | Mux → 2×2 switch → crossbar → multistage networks | 40 min |
| 04 | [The barrel rotator](04_barrel_rotator.md) | First real rotator; RTL walkthrough | 25 min |
| 05 | [Variable Z: the QSN trick](05_variable_size_qsn.md) | Why one barrel fails for 5G, and the two-shifter fix | 30 min |
| 06 | [Banyan, IBN and the 5G network](06_banyan_ibn_5g.md) | Recursive networks, control generation, the paper's key idea | 60 min |
| 07 | [Decoder architecture](07_decoder_architecture.md) | Where the rotator sits; memories; CNU; one-shifter trick; throughput | 50 min |
| 08 | [Build and verify plan](08_build_plan.md) | Milestones, verification strategy, exercises | 20 min |
| 09 | [Reading guide](09_reading_guide.md) | Which paper to read when, and how to decode its notation | 15 min |
| — | [Glossary](glossary.md) | Every term in one place | — |

If you only have an hour, read 00, 02, 03 and 06.

---

## What is in this folder

```
hw_tutorial/
├── *.md                 the chapters
├── model/
│   ├── rotators.py      golden models of every rotator (mirrors the RTL stage by stage)
│   └── layered_qc.py    layered Min-Sum decoder three ways: dense, two-rotator, one-rotator
├── rtl/
│   ├── switches.v       sw2 (2x2) and sw3 (3x3) switch primitives
│   ├── rot_barrel.v     fixed-size barrel rotator, any N
│   ├── rot_qsn.v        variable-size rotator (QSN style), any Z <= N
│   ├── rot_banyan.v     Banyan rotator, N = 2^n, with shared control generation
│   ├── rot_ibn3.v       Improved Banyan Network, N = 3*2^n (Song et al. 2022)
│   └── rot_5g.v         5G rotator: any of the 51 lifting sizes, Z <= 384
├── tb/tb_rotators.v     self-checking testbench for all of the above
├── site/                builds all chapters into one web page with an interactive rotator lab
└── run_tests.sh         runs everything
```

Read it as a web page (rebuilt from these chapters each time):

```bash
cd hw_tutorial/site
./serve.sh               # then open http://localhost:8080
```

Run all checks (Python 3, plus Verilator; iverilog works too but is slow):

```bash
cd hw_tutorial
./run_tests.sh
```

Expected tail of the output:

```
all rotator models agree with the reference (4479 (Z, shift) pairs at N=384)
dense, two-rotator and one-rotator (delta-shift) decoders agree bit-exactly on 30 random QC codes
   rot_5g: clean
PASS: 9861 checks, 0 errors
```

---

## How this relates to the Python course

The browser course (`/?course=ldpc-5g`) teaches the algorithm in 18 small
Python checkpoints. Its hardware part is short: rotation is one function
(LDPC-11), and lanes and memory banks are counting exercises (LDPC-16, 17).
This tutorial picks up where that leaves off.

| Python checkpoint | Hardware chapter that builds on it |
|---|---|
| LDPC-02 syndrome, LDPC-03 Tanner graph | 01 |
| LDPC-05/18 check node, min1/min2 | 01, 07 (CNU) |
| LDPC-10 layered update | 01, 07 |
| LDPC-11 rotation, LDPC-12 lifting | 02, 04–06 |
| LDPC-13 NR lifting sizes | 05, 06 |
| LDPC-14/15 saturation, quantization | 07 (word widths) |
| LDPC-16 lanes, LDPC-17 banking | 07 |

You don't need to finish the Python course first. Chapter 01 explains
everything the hardware chapters rely on.

**One convention differs from the Python course; it is stated once here.**
The Python course defines rotation as *right* rotation. This tutorial uses
*left* rotation, `out[i] = in[(i + s) mod Z]`, because that is exactly what a
5G circulant needs (chapter 02 shows why). The two are the same operation with
the shift negated: `rotl(x, s) == rotr(x, -s)`.

---

## About the two papers next to this repo

* **Song, Cui, Wang, "A Universal Efficient Circular-Shift Network for
  Reconfigurable QC-LDPC Decoders", IEEE TVLSI 2022.** This is the core paper
  for this tutorial. Chapter 06 rebuilds its main idea (the IBN) from first
  principles, and `rtl/rot_5g.v` follows the structure of its 5G network (Fig. 6a).
* **Huang, Walrand, "A Benes Packet Network", arXiv 1208.0561.** This is about
  routing packets through a data-center switch fabric with queues and
  backpressure scheduling. It is **not an LDPC paper**. Only its description of
  the Benes topology (Section III-A, Fig. 2) is relevant here; chapter 03 covers
  that in a few paragraphs. You can skip the queueing theory.

More open-access papers were downloaded into the `references/` folder next to
this repo (`../../references/` from here; not part of the git repo). Chapter 09
says what each one is good for and lists the paywalled classics.

# Prompt: Build Me an Interactive 5G NR LDPC Tutor for Hardware-Accelerator Thinking

## Purpose

Use this prompt to create a **beginner-to-accelerator interactive tutor** that teaches me Low-Density Parity-Check (LDPC) decoding from scratch, specifically in the context of **real-time 5G NR implementations** and eventually designing a hardware accelerator.

This is **not** a request to dump theory, generate a complete decoder for me, or immediately write RTL.

The learning experience must follow this loop:

> **Explain → show a tiny worked example → visualize → ask me to predict → give me a small coding assignment → test my result → discuss what the result means → connect it to hardware**

I should write the meaningful Python code myself. The tutor may provide scaffolding, fixtures, plotting/visualization helpers, tests, and progressive hints, but should not simply hand me the completed implementation.

## Content authority and required interface

This document is the main **content and teaching specification** for the LDPC
course. Use it to guide the course research and lesson generation. The earlier
`LDPC_TUTOR_RESEARCH_AND_CURRICULUM_PROMPT.md` supplies supplementary engineering
and verification requirements; where the teaching sequence differs, use this
document and explain any research-driven revisions.

The interface must be the existing cache tutor's **notebook-style web page**,
not Jupyter: checkpoint navigation on the left, explanation/code/results in the
center, and the OpenCode-backed tutor chat on the right. I edit ordinary Python
files. Preserve model selection, public tests, saved work, progress, reflections,
and evidence-based tutor answers. Do not introduce `.ipynb`, Colab, notebook
magics, or a Jupyter kernel as a course requirement.

The reference assignment archive is
`/home/ranga/opencode/tutor/notebook_tutor/assignment1.zip`. Borrow its CS231n
learning pattern—small TODOs, clear interfaces, immediate checks, experiments,
and reflection—not its notebook infrastructure or completed solutions.

## Plain-language and visual-first teaching contract

Every lesson must work for someone seeing its terminology for the first time.
Use this order:

```text
What problem are we solving?
          ↓
What does that mean in ordinary language?
          ↓
Show actual numbers and a picture
          ↓
Name the concept and introduce its notation
          ↓
Predict → implement → observe → explain
```

- Define each acronym on first use and keep a small glossary visible.
- Introduce one main new idea at a time. Break a long derivation into steps.
- State what each index selects, each value represents, and each array contains.
- Explain an equation in words before asking me to use it. Define its symbols,
  shapes, units, and sign convention beside the equation.
- Use analogies only as a bridge; explain where the analogy stops being exact.
- Carry one small example through explanation, diagram, calculation, code
  contract, and public result instead of switching examples at every step.
- Give a concise "what to remember" summary and one misconception to avoid.
- Explain a failure with actual values, not only a label such as "LLR error".

Use **ample meaningful visuals**, not decorative illustrations. Each main
concept needs a visual that makes its relationships understandable; each
multi-step update needs a numbered walkthrough or before/after view. A normal
lesson will usually have a concept visual and a worked-example visual, with a
result/trace visual where useful. This is not a quota for redundant diagrams.

For generated Markdown, include readable ASCII diagrams/tables and precise
rendering specifications. For the web tutor, prefer accessible SVG, HTML tables,
and code-generated plots so diagrams remain sharp and match test data. Do not
depend on AI-generated bitmap images to convey exact indices or arithmetic.

For every visual, answer: **"What should I notice here?"** Add a caption that
states the observation, the relevant convention, and whether the example is
toy, standard-derived, or an implementation choice.

---

# 1. Learner profile and final goal

Assume:

- I can write basic Python and NumPy.
- I understand basic digital hardware concepts such as memories, pipelines, parallelism, muxes, LUTs, BRAM/SRAM, clock cycles, and RTL datapaths.
- I may be new to coding theory, information theory, probability, LLRs, Tanner graphs, and iterative decoding.
- I learn best through small numerical examples that I can trace manually.
- I want to understand **why an algorithm maps to hardware the way it does**, not merely call a library.

By the end of the course I should be able to:

1. Explain what an LDPC code is and why 5G NR uses QC-LDPC for data channels.
2. Work with parity-check matrices over GF(2).
3. Construct and interpret a Tanner graph.
4. Understand channel observations and LLRs.
5. Perform check-node and variable-node updates manually.
6. Implement a small flooding Min-Sum decoder.
7. Implement Offset or Normalized Min-Sum.
8. Understand and implement layered decoding.
9. Understand the QC structure used by 5G NR.
10. Explain Base Graph 1 vs Base Graph 2 at a useful engineering level.
11. Understand lifting size `Z`, circulants, shift coefficients, and how the base graph expands.
12. Understand the relationship between information bits, code-block bits, filler bits, mother-code bits, punctured positions, rate-matched transmitted bits, and rate-recovered receiver LLRs.
13. Build a restricted but real NR-compatible decoder path using verified fixtures.
14. Build a bit-accurate fixed-point decoder model.
15. Identify the main decoder bottlenecks: message memory, memory bandwidth, cyclic permutation, min1/min2 computation, sign reduction, hazards between layers, iteration count, and early termination.
16. Model cycles and memory accesses for an accelerator.
17. Explain the tradeoff between high throughput, low single-codeword latency, area, power, programmability across `Z`, and BLER performance.
18. Propose a first FPGA/ASIC decoder architecture and generate golden vectors for it.

The final outcome is **accelerator readiness**, not just a software LDPC demo.

---

# 2. Important 5G NR fact that the course must teach correctly

A colleague told me that "input vector sizes can range from 2 to 384 and rotations can also vary from 2 to 384."

Do **not** simply repeat that sentence.

Teach the precise idea.

In 5G NR QC-LDPC, the central parameter is the **lifting size `Z`**.

The standardized lifting sizes are a finite allowed set from 2 through 384:

```text
{2, 4, 8, 16, 32, 64, 128, 256}
{3, 6, 12, 24, 48, 96, 192, 384}
{5, 10, 20, 40, 80, 160, 320}
{7, 14, 28, 56, 112, 224}
{9, 18, 36, 72, 144, 288}
{11, 22, 44, 88, 176, 352}
{13, 26, 52, 104, 208}
{15, 30, 60, 120, 240}
```

There are 51 allowed `Z` values.

Do not imply that every integer from 2 to 384 is legal.

For a selected `Z`:

- a non-empty QC submatrix is a `Z × Z` circulant permutation matrix;
- hardware commonly operates on a vector of `Z` values when sufficient parallelism is available;
- an NR base-graph shift coefficient is reduced modulo `Z`;
- therefore the effective cyclic shift is in the range `0 ... Z-1`, not "2 ... 384" in general.

The course must teach this with progressively larger examples.

## Required lifting/rotation examples

Use at least:

```text
Z = 2
Z = 8
Z = 32
Z = 96
Z = 192
Z = 384
```

For each one, show:

1. a vector of length `Z`;
2. a cyclic shift;
3. what a `Z × Z` circulant permutation matrix means;
4. how the same operation can be expressed without explicitly constructing the matrix;
5. how hardware might perform the shift.

For small `Z`, show every value.

For large `Z`, such as 96, 192 and 384, show only a representative slice plus the indexing rule.

Example:

```text
Z = 8

input:
[x0 x1 x2 x3 x4 x5 x6 x7]

rotate right by 3:

[x5 x6 x7 x0 x1 x2 x3 x4]
```

Then connect this to hardware:

```text
8 lanes
   ↓
3-stage barrel shifter
   ↓
8 rotated lanes
```

because `8 = 2^3`, so a rotation from 0 to 7 can be composed from conditional shifts of 1, 2 and 4.

Contrast this with `Z=96`, where an accelerator may use a more general permutation network, multiple cycles, banked memories, lane groups, or partial parallelism.

The tutor should ask me to reason about these options instead of claiming one architecture is universally correct.

---

# 3. Standards grounding

Use an authoritative 3GPP TS 38.212 / ETSI publication and **pin the exact version used by the course**.

Explicitly cite the standard for:

- LDPC base graphs;
- base-graph selection;
- lifting-size sets;
- lifting and circulant construction;
- code-block segmentation;
- filler-bit treatment;
- rate matching and rate recovery where taught.

Keep a small claim ledger.

For every claim, distinguish:

```text
STANDARD-DEFINED
ALGORITHM CHOICE
IMPLEMENTATION CHOICE
TEACHING SIMPLIFICATION
```

Example:

```text
"NR supports BG1 and BG2"
→ STANDARD-DEFINED

"Use layered Offset Min-Sum"
→ ALGORITHM / IMPLEMENTATION CHOICE

"Use 6-bit internal messages"
→ IMPLEMENTATION CHOICE

"First demonstrate with a 3×6 toy H matrix"
→ TEACHING SIMPLIFICATION
```

Never make a toy matrix look as if it were an actual 5G code.

---

# 4. Begin with intuition, not the standard tables

Do not begin the first lesson with BG1/BG2 tables.

Start with a tiny code, for example:

```text
H =

1 1 0 1 0 0
0 1 1 0 1 0
1 0 1 0 0 1
```

Explain one row as:

```text
b0 XOR b1 XOR b3 = 0
```

Then show a valid bit vector and calculate the syndrome manually.

Make the visual explanation clear enough that someone unfamiliar with coding theory can answer:

> "What exactly is this matrix checking?"

For this toy matrix, use the same concrete example across the first lessons:

```text
bit index:       0  1  2  3  4  5
candidate c:    [1  0  1  1  1  0]

check 0 selects b0, b1, b3:
                  1 XOR 0 XOR 1 = 0   ✓

check 1 selects b1, b2, b4:
                  0 XOR 1 XOR 1 = 0   ✓

check 2 selects b0, b2, b5:
                  1 XOR 1 XOR 0 = 0   ✓

syndrome:       [0  0  0]
```

Then flip only `b1`, highlight that bit and its two connected checks, and show
the syndrome changing to `[1, 1, 0]`. Say plainly: "Two rules are now broken;
the syndrome tells us which checks fail, not automatically which bit to flip."
Ask me to predict the affected checks before revealing this second result.
This worked example teaches the operation; I still implement the function.

Only after that should the tutor introduce sparse representations and Tanner graphs.

---

# 5. Teaching sequence

Organize the tutor into roughly **16–22 short checkpoints**.

Normal checkpoints should target about 20–45 minutes.

Use the following phases.

---

## Phase A — Binary parity and tiny LDPC codes

### A1 — XOR and GF(2)

Teach:

- binary addition modulo 2;
- XOR;
- dot product over GF(2);
- why ordinary integer matrix multiplication is not the final parity result.

Worked example first.

Assignment:

```python
def gf2_dot(a, b):
    ...
```

Do not provide the completed body.

### A2 — Parity-check matrix and syndrome

Teach:

```text
H @ c mod 2
```

and what zero/nonzero syndrome means.

Include:

- valid codeword;
- one-bit corruption;
- syndrome vector;
- syndrome weight.

Assignment:

```python
def syndrome(bits, h):
    ...
```

Also teach:

```text
zero syndrome != guaranteed original transmitted payload
```

### A3 — Tanner graph

Turn a small `H` into variable nodes, check nodes, and edges.

Show both dense `H` and sparse adjacency forms.

Assignment: write neighbor extraction.

Hardware question:

> Why would we store edges instead of a huge sparse binary matrix?

---

## Phase B — Soft information

### B1 — BPSK and noisy observations

Start with:

```text
bit 0 → +1
bit 1 → -1
```

Use received values such as:

```text
+1.3
+0.15
-0.2
-2.1
```

Ask which decisions are confident and which are uncertain.

### B2 — LLR intuition

Explain first:

```text
LLR > 0 → bit 0 favored
LLR < 0 → bit 1 favored
|LLR| → confidence
```

Then introduce the mathematical definition.

Assignment: hard decisions from LLRs, including a defined zero tie policy.

---

## Phase C — Message-passing decoding

### C1 — One check-node update

Use:

```text
incoming messages:
+7, -3, +5, -9
```

For each outgoing edge, manually exclude that edge.

Teach:

- sign parity;
- minimum magnitude;
- extrinsic information.

Ask me to calculate outputs before coding.

### C2 — Why min1 and min2 exist

Use:

```text
[7, 3, 5, 9]
```

Show:

```text
min1 = 3
min2 = 5
argmin = index 1
```

Then:

```text
if outgoing edge != argmin:
    magnitude = min1
else:
    magnitude = min2
```

Include repeated-minimum and zero edge cases:

```text
[3, 3, 5, 9]
[0, 4, 6]
[-2, +2, +8]
```

Hardware connection:

- comparator tree;
- min1/min2 network;
- critical path;
- storage per check node.

### C3 — Variable-node update

Teach:

```text
posterior = channel LLR + incoming check messages
```

and why an outgoing variable-to-check message excludes the destination check's contribution.

Use a complete numeric example.

### C4 — One flooding iteration

Give a tiny graph and trace:

| Edge | old V→C | new C→V | new V→C |
|---|---:|---:|---:|

Display messages, hard decisions, syndrome, and decision changes.

### C5 — Full toy decoder

Combine the earlier primitives.

Add:

- maximum iteration count;
- syndrome early stop;
- deterministic trace.

Do not jump to 5G yet.

---

## Phase D — Practical decoder algorithms

### D1 — Sum-Product vs Min-Sum

Explain what Sum-Product is computing, then why Min-Sum is attractive to hardware.

Show:

```text
SPA:
tanh / atanh / multiplications

Min-Sum:
abs / compare / xor / add
```

### D2 — Normalized and Offset Min-Sum

Teach:

```text
Normalized:
alpha * min

Offset:
max(min - beta, 0)
```

Example:

```text
min = 5
beta = 1
→ 4
```

Assignment: configurable check-node primitive.

### D3 — Flooding vs layered decoding

Visualize:

```text
Flooding:
all CN updates
      ↓
all VN updates
      ↓
iteration done
```

versus:

```text
Layered:
layer 0 → update posterior immediately
layer 1 → sees the new posterior
layer 2 → sees the new posterior
...
```

Use a tiny graph where a value changed by layer 0 is visibly used by layer 1.

Ask:

- What must be stored?
- What RAW dependency exists?
- Which layers could theoretically overlap?
- Where would bypassing help?

---

# 6. Phase E — Enter real 5G NR QC-LDPC

## E1 — Base graph concept

Teach a toy QC base matrix first:

```text
B =
 0   1  -1
 2  -1   0
```

Define:

```text
-1 → all-zero Z×Z block
k  → identity matrix cyclically shifted by k
```

Use `Z=4`.

Expand the whole toy matrix visually, then show how not to build it explicitly.

Assignment:

```python
def expand_qc(base, z):
    ...
```

for teaching only.

## E2 — Vector rotation as LDPC computation

Directly address the 2..384 mental model.

Use:

```text
Z = 8
shift = 3
```

Show:

```text
[0 1 2 3 4 5 6 7]
→
[5 6 7 0 1 2 3 4]
```

Assignment:

```python
def rotate_qc_vector(x, shift):
    ...
```

Tests:

```text
shift = 0
shift = 1
shift = Z-1
shift = Z
shift > Z
```

Teach modulo reduction.

## E3 — Scaling across NR lifting sizes

Use the real allowed `Z` set.

Include:

| Z | vector width | effective shifts | full-parallel lanes |
|---:|---:|---:|---:|
| 2 | 2 | 0..1 | 2 |
| 8 | 8 | 0..7 | 8 |
| 32 | 32 | 0..31 | 32 |
| 96 | 96 | 0..95 | 96 |
| 192 | 192 | 0..191 | 192 |
| 384 | 384 | 0..383 | 384 |

Ask:

> If the accelerator has only 32 physical lanes, how many groups are needed for `Z=384`?

Then extend to `Z=352` and other nonmultiples.

Discuss:

- masked lanes;
- lane utilization;
- address generation;
- multi-cycle processing.

## E4 — Real BG1/BG2

Introduce actual BG1/BG2 dimensions and verified data.

Do not paste huge standard tables into lesson prose.

Use authored data assets.

Explain:

- base-graph dimensions;
- non-empty circulants;
- systematic region;
- graph-selection motivation;
- expanded size dependence on `Z`.

Use at least one verified BG1 fixture and one BG2 fixture.

## E5 — Shift coefficient versus effective rotation

Teach:

```text
effective_shift = coefficient mod Z
```

Example:

```text
coefficient = 137
Z = 32
137 mod 32 = 9
```

Hardware connection:

> The table entry can become a rotation/address control value rather than a stored permutation matrix.

---

# 7. Phase F — Real receiver plumbing

Do not pretend the decoder receives a perfect mother-code LLR vector directly from the radio.

Teach:

```text
transport block
   ↓
TB CRC
   ↓
segmentation
   ↓
CB CRC
   ↓
LDPC encoding
   ↓
rate matching
   ↓
modulation / channel
   ↓
demodulated LLRs
   ↓
rate recovery
   ↓
LDPC decoder
```

Clearly distinguish:

```text
filler
punctured
not transmitted
repeated
unknown
known
```

Teach that neutral unknown positions are not the same as known filler positions.

Use a tiny authored example before a real NR fixture.

---

# 8. Phase G — Hardware-oriented decoder model

## G1 — Quantization

Take values such as:

```text
+4.83
-1.29
+12.7
-9.1
```

map them into a specified fixed-point/integer format.

Teach:

- clipping;
- saturation;
- rounding;
- accumulator width;
- overflow.

Assignment:

```python
def saturate_signed(x, width):
    ...
```

Compare float and fixed-point traces.

## G2 — Two-minimum CNU

Expose:

```text
min1
min2
argmin
sign parity
```

Ask me to estimate:

- comparators;
- tree depth;
- critical path;
- pipeline placement;
- stored state.

## G3 — QC permutation network

Compare:

### Full-width

```text
Z lanes
→ permutation network
→ Z lanes
```

### Fixed P-lane

```text
P = 32
Z = 384
→ 12 lane groups
```

### Address-based rotation

Rotate addresses where possible instead of physically moving data.

Compare:

- mux cost;
- SRAM banking;
- cycles;
- routing;
- programmability.

## G4 — Memory organization

Model storage for:

- channel/posterior LLRs;
- check-to-variable messages;
- shift/configuration data.

Give a worked exercise such as:

```text
121,344 edge messages
6 bits/message
```

Ask for bits, bytes, KiB, and double-buffer cost.

## G5 — Layer schedule and hazards

Generate a logical schedule:

| Cycle | layer | group | read banks | rotate | CNU | update | write banks |
|---:|---:|---:|---|---|---|---|---|

Have me identify RAW hazards, bank conflicts, idle lanes, bypass opportunities, and pipeline overlap.

## G6 — Early termination

Compare fixed iteration count against syndrome-based early stopping.

Measure:

- average iterations;
- worst-case iterations;
- total operations.

Discuss why throughput and bounded latency are different goals.

---

# 9. Phase H — Real-time and ultra-low-latency viewpoint

Teach three metrics.

### Throughput

```text
decoded information bits / second
```

### Single-codeword latency

```text
time from decoder-input LLR availability to decoded result
```

### Tail / bounded latency

Study:

```text
P50
P90
P99
P99.9
worst case
```

Ask:

> A GPU processes huge batches efficiently while an FPGA may return one short code block sooner. Which is better?

The required answer is: it depends on workload and metric.

---

# 10. Required ultra-low-latency case study

Include at least one recent short-block/URLLC-style implementation.

Investigate the following **candidate case-study figures supplied in this
prompt**. They are not verified by this document and must not be taught as
established measurements until an exact primary source is found:

```text
QC-LDPC (280,176)
Z = 8
layered decoding
Offset Min-Sum
5-bit channel LLR
6-bit internal messages
max 7 iterations
~218.6 MHz
~155.8 Mbps
~1.129 us decode latency
~0.201 W
```

Explain that this is a research configuration, not a universal full-NR decoder.

Find the paper/report, exact table or figure, code configuration, measurement
boundary, and whether each metric is measured, simulated, or estimated. In
particular, verify what the latency includes and how throughput was computed.
If this source cannot be identified or these figures do not match it, report
the discrepancy and substitute a documented case study; do not invent a citation
or use approximate figures as correctness targets.

Ask:

- Why is `Z=8` architecturally convenient?
- Why does short block length help latency?
- What coding-performance tradeoff exists?
- What changes at `Z=384`?
- Which numbers come from algorithm choices versus implementation choices?

---

# 11. Required modern accelerator comparisons

## CPU

Study an optimized FEC implementation such as AFF3CT.

Focus on:

- SIMD;
- message layout;
- threading;
- layered/flooding schedules;
- fixed-point options.

Point to individual modules/functions, not the whole repository.

## GPU

Study an open CUDA LDPC implementation and a modern 5G GPU implementation such as NVIDIA Aerial/cuPHY where useful.

Teach why GPU decoding likes:

```text
many code blocks
×
many graph edges
×
many threads
```

Then discuss kernel-launch, synchronization, memory, batching, and single-packet-latency tradeoffs.

## FPGA / ASIC

Study modern 5G QC-LDPC architectures covering:

- layered decoding;
- partial parallelism;
- min1/min2;
- configurable `Z`;
- cyclic-shift networks;
- memory reduction;
- pipeline hazards;
- quantization.

For every paper extract:

```text
technology
algorithm
supported Z/configurations
frequency
throughput
latency if reported
precision
iterations
resources/area
power if reported
```

Never compare numbers blindly across different code configurations or technologies.

---

# 12. Nice explanations are mandatory

Each lesson page should use this structure.

## Page template

### 1. The question we are answering

Example:

> How can thousands of parity-check connections be represented without storing a gigantic matrix?

### 2. Intuition

Plain language.

Define new terms and explain why this operation is needed. Include one sentence
that I could use to explain the idea to another beginner.

### 3. Tiny example

Actual values.

### 4. Draw it

ASCII diagram, heatmap, Tanner graph, rotation, pipeline, or table.

Add indices, labels, a legend, and a caption saying what to notice. Make the
connection to the previous picture explicit; do not introduce an unrelated
diagram just to fill this section.

### 5. Walk every important intermediate value

Do not skip to the result.

Use numbered steps and highlight the active row, edge, lane, or layer. If the
same value is represented differently in a matrix, graph, array, and hardware
diagram, show that mapping explicitly.

### 6. Connect to 5G

Label the example toy or standard-derived.

### 7. Connect to hardware

Discuss arithmetic, storage, addressing, routing, parallelism, cycles, and precision.

### 8. Prediction

Ask me for an output before running code.

### 9. My assignment

A bounded TODO.

### 10. Public checks

Deterministic examples.

### 11. Experiment

A small observable experiment.

### 12. Reflection

Ask what I learned.

### 13. Progressive hints

```text
Hint 1 — conceptual
Hint 2 — algorithm structure
Hint 3 — near-pseudocode
```

Do not give the completed implementation unless I explicitly ask after trying.

---

# 13. Assignment style

Use CS231n-like assignment design:

- clear docstrings;
- shapes and dtypes;
- precise contracts;
- small TODO region;
- provided scaffolding;
- immediate tests;
- visual output;
- experiment;
- reflection.

Example:

```python
def qc_rotate(values: np.ndarray, shift: int) -> np.ndarray:
    """
    Cyclically rotate one QC vector.

    Parameters
    ----------
    values:
        Shape (Z,). One message per lifted position.

    shift:
        Integer rotation coefficient. Apply modulo Z.

    Returns
    -------
    rotated:
        Shape (Z,), same dtype as values.

    Requirements
    ------------
    - do not mutate values
    - support shift = 0
    - support shift >= Z with modulo reduction
    - reject an empty vector

    TODO
    ----
    Implement the rotation without constructing a Z×Z matrix.
    """
    raise NotImplementedError
```

The course must explicitly fix left-vs-right rotation convention before grading.

---

# 14. Visualizations

Use visuals whenever they answer a learning question.

## 14.1 Visual progression: from the smallest example to hardware

The course must repeatedly link these views, rather than presenting them as
separate facts:

```text
Parity equation   ↔   one matrix row   ↔   one check node
                                              ↓
                                      incident graph edges
                                              ↓
                                      Python edge indices
                                              ↓
                                   arithmetic + memory access
```

Use consistent labels such as `b0`, `c0`, and `e0`. Different objects must not
share an ambiguous label. Keep the same edge numbering in a graph, array table,
message trace, and test result.

## 14.2 Required visual storyboard

| Topic | Show | What the learner should notice |
|---|---|---|
| XOR / parity | Two-bit truth table, then one highlighted parity equation | A check asks whether the selected bits contain an even number of ones |
| Syndrome | Matrix and candidate bits beside row-by-row calculations | One syndrome entry belongs to one check; it is not a decoded bit |
| Corruption | Before/after vector with one flipped bit and affected checks | One bit can break several checks; several errors may mask each other |
| Tanner graph | Matrix and bipartite graph side by side with linked highlights | Every `1` corresponds to one edge, and every edge has two endpoints |
| Sparse storage | Edge table linked to node-neighbor lists | Indices identify connections; storage need not include every matrix zero |
| LLRs | Signed number line with hard decision and magnitude annotations | Sign is the favored bit; magnitude is confidence, not the bit value |
| Extrinsic update | Active outgoing edge marked "exclude"; other inputs highlighted | A message must not immediately echo its recipient's own evidence |
| Min1/min2 | Sorted magnitudes and per-edge exclusion table | Repeated minima need explicit handling; the second minimum is not always a distinct value |
| Flooding iteration | Numbered graph updates plus old/new edge table | Which values belong to the old iteration and which have just been computed |
| Layered decoding | Posterior value timeline with read/write arrows | A later layer may consume an earlier layer's updated information |
| QC lifting | Small base matrix with a highlighted block and its expansion | One base entry describes a whole structured block, not one expanded edge |
| Rotation | Indexed input/output lanes plus source-to-destination arrows | The shift direction and modulo rule determine exactly where each value goes |
| Large lifting size | Representative lane slices and an index rule | A schematic is not a literal display of all 384 lanes or all matrix entries |
| Rate recovery | Separate transmitted, recovered, and full-graph index strips | Missing, repeated, and known positions require different treatment |
| Fixed point | Value → scaling → rounding → clipping → stored value | Precision and range are separate; overflow cannot be left implicit |
| Memory banking | Address table and bank/time grid | Concurrent requests can collide even when there are enough compute lanes |
| Pipeline schedule | Cycle timeline showing reads, processing, and writes | Pipeline latency, dependencies, and initiation interval are different |
| Decoder convergence | Syndrome weight and decision changes with iteration labels | Zero syndrome and recovery of the original payload are different outcomes |

Do not put every visual in every lesson. Introduce each when its concept becomes
relevant, then reuse the established visual language in later diagnostics.

## 14.3 A required message-update walkthrough

For the first Min-Sum check-node example, show **which inputs are excluded**:

```text
incoming:      e0:+7     e1:-3     e2:+5     e3:-9

outgoing e0:   exclude +7
              use [-3, +5, -9]
              two negative signs → positive
              minimum magnitude = 3
              outgoing message = +3
```

Ask me to calculate the other outgoing edges before showing the completed
table. Then link the table to the graph arrows and the function's output order.
State that this is the uncorrected Min-Sum teaching example, before OMS/NMS.

## 14.4 Visual interactions in the cache-style web tutor

Provide simple interactions where they help learning:

- Select a matrix row to highlight its graph node and connected bits.
- Select an edge to show its index, endpoints, incoming/outgoing messages, and
  the exact update used in the displayed public trace.
- Step through an iteration or layer with Previous/Next controls; show a static
  readable trace as a fallback, not animation alone.
- Choose `Z` and a shift to inspect indexed rotation; distinguish a teaching
  control from a standards-valid configuration.
- Compare expected/observed or float/fixed states and highlight the first
  divergence rather than dumping two enormous arrays.
- Select a cycle to highlight active lanes, memory reads/writes, and conflicts.

These interactions use provided visualization helpers; implementing a plot or
UI widget is not the learner's LDPC assignment unless explicitly intended.
Changing a visualization must not send an automatic model request.

## 14.5 Rendering and accuracy rules

- Use both text/shape labels and color; never make red/green the only signal.
- Label row/column axes, bit/edge/lane indices, units, and timing boundaries.
- Give large graphs a selected neighborhood view, not an unreadable hairball.
- Use exact small examples and matching fixtures for diagrams and tests. A
  picture with different values from the assertion teaches the wrong lesson.
- Label cropped arrays and schematic blocks; show the complete indexing rule.
- Specify left/right shifts consistently for matrix and vector conventions.
- Do not confuse a count of lifted positions with a check-node degree. Before
  drawing a reduction network, define what each lane processes and which axis
  is reduced; validate the architecture against the researched dataflow.
- For mathematical/code-generated figures, keep the source data and renderer
  reproducible. Provide a text description for screen readers and Markdown.
- Keep optional visual detail collapsible so the central idea remains visible.

Each generated lesson must include a small **visual specification**: input
fixture, labels, view type, highlighted steps, expected observation, caption,
and static fallback. This lets an implementation agent build the picture
without guessing the mathematics.

Required visual types:

- parity-matrix heatmap;
- Tanner graph;
- edge-index table;
- one-iteration message trace;
- QC expansion;
- vector lanes;
- permutation network;
- layer schedule;
- memory banking;
- syndrome weight per iteration;
- changed decisions per iteration;
- float vs fixed comparison;
- first fixed-point divergence;
- cycle schedule.

---

# 15. Conventions sheet

Before iterative decoding, define:

- matrix orientation;
- row/column meaning;
- bit indexing;
- edge order;
- cyclic-shift direction;
- LLR sign convention;
- BPSK mapping;
- zero-LLR tie;
- variable/check message definitions;
- extrinsic update;
- flooding iteration definition;
- layered iteration definition;
- syndrome-check timing;
- punctured representation;
- filler representation;
- fixed-point signed format;
- rounding;
- saturation;
- accumulator width;
- sign-of-zero behavior.

Use this sheet while debugging.

---

# 16. Public tests

Tests must catch self-consistent mistakes such as:

- rotating in the wrong direction;
- reversed bit order;
- ordinary addition instead of GF(2);
- including the destination message in an extrinsic update;
- mishandling repeated minima;
- using min2 incorrectly;
- accidental integer overflow;
- treating punctured positions as known zeros;
- confusing filler with unknown;
- layered updates in the wrong order.

Use independent fixtures.

Do not accept "my encoder and decoder agree" as sufficient validation.

---

# 17. First accelerator design exercise

Assume:

```text
P = 32 physical lanes
```

Compare:

```text
Z = 32
Z = 96
Z = 192
Z = 384
```

Have me calculate:

```text
ceil(Z / P)
```

Then ask me to propose:

```text
input message SRAM
        ↓
32-lane reader
        ↓
QC rotator / address mapper
        ↓
32 CNU lanes
        ↓
min1/min2 reduction
        ↓
posterior update
        ↓
message SRAM
```

Challenge the architecture with:

- How is a minimum formed across multiple 32-lane groups?
- Where do partial min1/min2 values live?
- How is sign parity combined across groups?
- When can outputs begin?
- Is a second pass required?
- What SRAM bandwidth is needed?
- Can reads/writes overlap?
- What if edges collide on one bank?
- How is `Z` programmed?
- What if `Z` is not divisible by 32?
- What is lane utilization?
- What is the estimated cycle count per layer?

Do not answer everything upfront. Let me propose and defend a design.

---

# 18. Final capstone

I should produce:

1. supported NR slice;
2. base graph support;
3. supported `Z` values;
4. decoder algorithm;
5. schedule;
6. fixed-point widths;
7. max iterations;
8. early-stop rule;
9. processing-lane count;
10. message-memory layout;
11. QC rotation architecture;
12. CNU architecture;
13. VNU/posterior architecture;
14. hazard rules;
15. cycle-estimation model;
16. golden Python model;
17. intermediate golden vectors;
18. latency/throughput estimates;
19. limitations;
20. first RTL block.

Do not claim frequency, area, or power until synthesis.

---

# 19. Recommended first RTL block

Unless research indicates otherwise, recommend starting with either:

```text
A. configurable QC rotation unit
```

or:

```text
B. fixed-point CNU:
   sign parity + min1 + min2 + argmin + OMS correction
```

Generate bit-accurate Python vectors before RTL.

---

# 20. Tutor behavior

The tutor should:

1. Answer the direct question first.
2. Use the current lesson and my code.
3. Refer to actual failing values when debugging.
4. Ask me to inspect one useful intermediate quantity.
5. Give progressive hints.
6. Avoid premature full solutions.
7. Explain the hardware consequence of each important software choice.
8. Label things as standard-defined, algorithm-specific, implementation-specific, or teaching convention.
9. Correct mistaken assumptions clearly.
10. Never call a toy example 5G-compliant.

---

# 21. Research reading track

At each relevant phase assign only 1–2 sources.

Cover:

### Standard
- pinned 3GPP TS 38.212 / ETSI version.

### Algorithm
- belief propagation / Sum-Product;
- Min-Sum;
- Offset or Normalized Min-Sum;
- layered scheduling.

### CPU
- optimized LDPC/FEC software such as AFF3CT.

### GPU
- CUDA QC-LDPC;
- modern 5G GPU LDPC such as NVIDIA Aerial/cuPHY.

### FPGA/ASIC
- configurable 5G NR QC-LDPC decoder;
- memory-efficient implementation;
- low-latency implementation;
- URLLC-oriented implementation.

For each reading say:

```text
Read:
exact section/page

Look for:
specific idea

Ignore for now:
details not yet useful

After reading:
2–3 questions
```

---

# 22. Course artifacts

Use ordinary `.py` files, not Jupyter notebooks.

Suggested structure:

```text
curriculum/ldpc_5g/
  overview.md
  conventions.md
  reading.md
  accelerator_notes.md

  lessons/
    A01_GF2.md
    A02_SYNDROME.md
    A03_TANNER.md
    B01_BPSK.md
    B02_LLR.md
    C01_CHECK_NODE.md
    ...

  starter/
    ldpc/
      gf2.py
      graph.py
      channel.py
      minsum.py
      qc.py
      nr.py
      fixed.py
      cycle_model.py

  provided/
    verified_nr_tables/
    fixtures/
    plotting/

  tests/
    public/

  experiments/
```

---

# 23. Deliverables before implementing the tutor application

## A. `LDPC_COURSE_OVERVIEW.md`

Include:

- objective;
- phases;
- supported NR slice;
- prerequisites;
- non-goals;
- learning flow.

## B. `LDPC_CONVENTIONS_AND_STANDARD_NOTES.md`

Include:

- pinned 3GPP version;
- claim ledger;
- conventions;
- lifting-size set;
- base-graph scope;
- shift interpretation;
- rate-recovery terminology.

## C. `LDPC_CURRICULUM.md`

For every checkpoint include:

1. ID
2. title
3. prerequisites
4. expected time
5. goal
6. theory
7. worked example
8. visual
9. hardware connection
10. assignment
11. public tests
12. experiment
13. prediction
14. reflection
15. three hints
16. completion criteria
17. reusable artifacts

Also include a beginner glossary, notation/shape legend, common misconception,
and the visual specifications from Section 14. The course plan must explain how
the listed subtopics fit into 16–22 checkpoints: some are reading/experiment
sections rather than separate assignments. Split difficult tasks if necessary
and justify any change in the total; do not force several new ideas into one
checkpoint merely to meet the numerical target.

## D. `LDPC_FIRST_3_ASSIGNMENTS.md`

Fully author the first three checkpoints with starter interfaces and public-test specifications.

Do not provide completed target implementations.

Include ready-to-render diagrams, captions, prediction reveal points, and exact
worked-example values. The first three assignments must demonstrate the full
teaching style, not just promise that explanatory text will be added later.

## E. `LDPC_5G_QC_EXAMPLES.md`

Mandatory examples for:

```text
Z=2
Z=8
Z=32
Z=96
Z=192
Z=384
```

Include:

- vector shape;
- sample rotations;
- modulo behavior;
- circulant interpretation;
- indexing;
- full vs partial parallelism;
- 32-lane cycle-count exercises.

## F. `LDPC_DECODER_ACCELERATOR_BRIDGE.md`

Map:

```text
CNU
VNU/posterior update
min1/min2
sign parity
QC rotator
message SRAM
LLR SRAM
banking
layer scheduler
syndrome checker
early-stop controller
```

to hardware interfaces, memory, cycles, and golden-vector exercises.

## G. `LDPC_READING_GUIDE.md`

Phase-specific reading assignments and reasons.

---

# 24. Source anchors

Verify exact details before relying on them.

Use:

1. **3GPP TS 38.212 / ETSI equivalent**
   - lifting sets;
   - QC construction;
   - BG1/BG2;
   - rate matching.

2. **5G QC-LDPC hardware literature**
   - configurable lifting;
   - layered decoding;
   - OMS/NMS;
   - message-memory optimization;
   - permutation networks.

3. **URLLC-oriented FPGA case study**
   - short `(280,176)` QC-LDPC;
   - `Z=8`;
   - layered OMS;
   - reported decoder latency around 1.129 us.

4. **GPU/production implementations**
   - high-throughput CUDA LDPC;
   - real-time 5G GPU PHY implementations.

Whenever quoting performance, preserve the tested code size, rate, iteration count, precision, and platform.

---

# 25. Start the tutor-generation task this way

Do not begin by writing code.

First produce:

### Part 1 — What I will learn

One-page beginner-readable map.

### Part 2 — Correcting the `2..384` mental model

Explain lifting size, vector width, and rotations with `Z=8` and `Z=384`.

### Part 3 — Course map

Show the checkpoint DAG/table.

### Part 4 — Lesson A1 in full

Use:

```text
explanation
worked example
visual
prediction
assignment
tests
experiment
reflection
hints
hardware connection
```

Then stop and let me do the assignment.

---

# 26. Non-negotiable quality bar

A lesson is not acceptable if it only says:

> "LDPC uses a sparse parity-check matrix. Implement syndrome()."

A good lesson should make me able to explain:

- what data exists;
- how large it is;
- what every index means;
- which values move;
- what arithmetic occurs;
- what output should appear;
- why the operation exists;
- how it becomes hardware.

Before accepting a lesson, check:

1. Could I understand its intuition without already knowing the jargon?
2. Can I point at the diagram and explain every important label/index?
3. Can I reproduce the tiny worked example by hand?
4. Do the visual, equation, function contract, and public test describe the same
   operation with the same conventions?
5. Is there a prediction I can make before the result is revealed?
6. Does the assignment leave the meaningful implementation for me?
7. Is the toy-to-NR-to-hardware transition explained, with unsupported claims
   and unverified research numbers clearly marked?

If not, revise the lesson before adding more theory or moving to the next one.

The course should repeatedly move through:

```text
tiny mathematical example
        ↓
Python representation
        ↓
5G NR representation
        ↓
hardware representation
        ↓
cycles / storage / parallelism
```

That transition is the central purpose of this tutor.

# LDPC Tutor: Detailed Review and Revision Brief

Date: 9 October 2026

## 1. Purpose and authority

Use this document to revise the existing tutor into a clearer, more complete learning experience. It is a change specification for the implementing Codex agent, not a replacement decoder implementation or a request to give learners completed solutions.

Reviewed inputs:

- `LDPC_THEORY_AND_BIG_PICTURE_REVIEW.md`: the exported six introductory chapters, 17 assignment lessons, overview, architecture notes and visual fixture catalog.
- `LDPC_5G_HARDWARE_ACCELERATOR_TUTOR_PROMPT(1).md`: the original teaching and scope specification.

The review evaluates the exported text. The running interface, learner scaffolding, tests, hidden implementation details and actual tutor behavior were not inspected. Where a feature is absent from the export, inspect the repository before concluding that it is absent from the application. Do not claim implementation correctness from this review.

**Latest user clarification takes precedence:** parity and elementary concepts should remain. The tutor should be useful to engineers without LDPC knowledge, including those without chip-design experience. Do not shorten the basics merely because the requesting user is a chip designer.

The main revision goal is consistent teaching depth: preserve the accessible beginning and bring message passing, QC structure, fixed point and hardware up to the same standard.

## 2. Overall assessment

| Dimension | Assessment | Meaning |
|---|---:|---|
| Introductory learning experience | 7/10 | Useful foundations; important reasoning bridges are missing. |
| Delivery against the complete requested scope | 4/10 | A foundation course exists, but the real-NR and accelerator outcomes are deferred. |
| Worked arithmetic reviewed | Mostly sound | No arithmetic error identified in the displayed syndrome, Min-Sum, flooding, layered, quantization or lane examples. This does not validate code. |
| Honesty about limitations | Strong | Toy examples and unsynthesized hardware estimates are generally labeled accurately. Preserve this. |

These are editorial judgments, not measured learning outcomes or a numerical compliance audit.

### Preserve

- The progression from a communication problem to repetition, parity and graphs.
- Explicit distinctions between payload, codeword, syndrome and original-message recovery.
- The warning that zero syndrome does not prove correct recovery.
- Consistent LLR sign and zero-tie conventions.
- The principle of excluding the recipient when computing outgoing messages.
- Small hand-traceable examples and meaningful learner-written code.
- Explicit toy/standard/implementation labels.
- Ordinary Python files and the existing notebook-style web interface.

### Change

- Add missing explanations between operations instead of merely adding terminology.
- Teach complete state transitions before asking learners to assemble them.
- Replace generic or mismatched visual fixtures with operation-specific traces.
- Restore the missing min1/min2 lesson and real-NR milestones.
- Make experiments, progressive hints and completion criteria concrete.
- Connect hardware questions to actual arithmetic, addresses, stored values and timing assumptions.

## 3. Audience and teaching contract

Assume basic engineering numeracy and some programming familiarity. Provide a short Python/NumPy refresher for indexing, shapes, loops, Boolean operations and copying arrays. Do not require prior knowledge of probability, coding theory, radio systems, Tanner graphs or RTL.

Use three levels within lessons:

1. **Core explanation:** plain language, actual numbers, all prerequisites needed for the assignment.
2. **Optional mathematical detail:** derivations and probability interpretation.
3. **Optional hardware detail:** datapaths, memory organization, pipelines and implementation tradeoffs.

Optional detail must not contain information necessary to solve the core assignment. For example, the derivation of an LLR formula may be optional; the sign convention and meaning of each input cannot be optional.

Define hardware vocabulary when it first becomes necessary. A lane is one processing unit handling one item at a time under the stated schedule. A bank is an independently accessible memory partition. Explain a cycle, read port, pipeline latency and initiation interval before using them in calculations.

Each lesson must answer:

- What problem does this operation solve?
- What information is available, and what remains unknown?
- What does every input value and index mean?
- Why does the operation produce useful evidence?
- What changes, what stays fixed, and what is stored?
- What can the result establish, and what can it not establish?

## 4. Chapter-by-chapter changes

### Chapter 1 — Why error correction?

Current clarity: 9/10. Retain the explanation and communication chain.

Add a tiny terminology strip: payload, encoder, codeword, channel, observation, decoder, estimated payload. Introduce terms gradually rather than displaying an unexplained block diagram.

Distinguish a simulated transmitter truth from receiver knowledge. When the UI shows the original payload, label it as available to the experimenter for evaluation, not an input to the decoder.

Acceptance: the learner can explain why an unprotected received bit pattern cannot identify its own errors and can identify the decoder's actual inputs.

### Chapter 2 — Repetition, legal words and code rate

Current clarity: 9/10. Keep the complete repetition example and two-error failure.

Show why 000 and 111 are the only legal words, and compare received 101 with both: one differing position from 111 versus two from 000. Name Hamming distance only after this counting exercise.

Explain that rate is a fraction of information bits, not a clock rate. Avoid implying that redundancy alone determines correction strength.

Acceptance: the learner predicts both successful and incorrect majority decisions, explains the one-error assumption, and calculates the rate.

### Chapter 3 — Encode the running toy example before checking it

Current clarity: 8.5/10. The missing bridge is how the displayed valid word was created.

Use the existing matrix and designate the first three positions as payload for this toy construction:

```text
H = [[1,1,0,1,0,0],
     [0,1,1,0,1,0],
     [1,0,1,0,0,1]]
```

| Step | Calculation | Result |
|---|---|---|
| Choose payload | [b0,b1,b2] | [1,0,1] |
| Add parity b3 | b0 XOR b1 | 1 |
| Add parity b4 | b1 XOR b2 | 1 |
| Add parity b5 | b0 XOR b2 | 0 |
| Assemble codeword | [b0,b1,b2,b3,b4,b5] | [1,0,1,1,1,0] |

Explain that the encoder chooses the parity bits so every check passes. The decoder estimates all six bits; payload extraction returns the first three positions for this chosen toy layout. Do not imply arbitrary parity matrices have this same direct encoding structure.

Then calculate all three checks, flip b1, and obtain syndrome [1,1,0]. Define syndrome weight as the number of failed checks; here it is 2.

Add a failure example on the same matrix. Codewords [1,0,1,1,1,0] and [0,0,1,0,1,1] both pass all checks but contain different payloads. This makes the validity-versus-recovery distinction concrete.

Acceptance: the learner constructs parity bits, computes the syndrome, identifies its shape, and explains why its entries are not decoded payload bits.

### Chapter 4 — Graph connections become stored messages

Current clarity: 8/10. Keep the Tanner graph explanation, but add stable global edge IDs:

| Edge | Check | Bit |
|---|---|---|
| e0 | c0 | b0 |
| e1 | c0 | b1 |
| e2 | c0 | b3 |
| e3 | c1 | b1 |
| e4 | c1 | b2 |
| e5 | c1 | b4 |
| e6 | c2 | b0 |
| e7 | c2 | b2 |
| e8 | c2 | b5 |

Explain that a bit may participate in several checks and therefore have several distinct outgoing messages. An edge is a relationship, not an extra transmitted bit.

Link matrix cell, graph edge, edge-table entry and message-array address by selecting one edge. Keep row-major edge order stable throughout this example. When moving to a different graph, explicitly announce the new fixture and its edge numbering.

Do not describe this tiny matrix as representative of practical sparsity or error performance. Use a separate labeled schematic to illustrate a much sparser large matrix.

Acceptance: the learner locates both endpoints of a message and distinguishes node indices from edge indices.

### Chapter 5 — Split the conceptual load into short lessons

Current clarity: 7/10. Preserve the existing five-stage story but add the following sequence:

1. Observations and hard decisions.
2. Confidence and LLR meaning.
3. One check advises all its neighbors.
4. One variable combines evidence and excludes a destination.
5. The four kinds of decoder state.
6. One complete flooding iteration.
7. A second iteration that is genuinely necessary.
8. Successful recovery, valid-but-wrong recovery and failure to converge.

The main chapter may remain an overview, but the assignment pages must contain the full explanations below.

### Chapter 6 — Replace the compressed ending with a staged bridge

Current clarity: 6/10. Retain the overview but do not present it as completion of accelerator readiness.

Teach three separate stages:

- **Structure:** toy base matrix → lifted parity checks → cyclic indexing → verified NR configuration.
- **Numerics:** floating messages → quantized codes → complete fixed-point decoder behavior.
- **Execution:** logical operations → memory requests → lanes → scheduled cycles → latency and throughput.

Keep beginner hardware explanations. Experienced engineers can collapse them. Distinguish lane-group count from cycle count and cycle count from measured physical timing.

## 5. Required replacement examples for soft decoding

### 5.1 Where an LLR comes from

Start with a teaching channel: bit 0 maps to +1, bit 1 maps to -1. A noisy observation y can differ from either ideal value. The receiver knows the assumed channel model, not the transmitted bit.

For real additive Gaussian noise of variance sigma_squared and equal bit priors:

```text
channel_LLR = ln(p(y | bit=0) / p(y | bit=1))
            = 2*y / sigma_squared
```

Explain that p here is a probability density for a continuous observation. Do not demand density calculations in the first assignment. Positive means the observation supports 0, negative supports 1, and zero is a tie.

Use y=-0.1 and sigma_squared=1 to produce LLR=-0.2. At the same y, a larger noise variance produces a smaller magnitude. This explains why amplitude alone is insufficient to specify confidence.

When writing posterior odds, condition on the evidence explicitly. Do not use an unexplained unconditional P(bit=0)/P(bit=1) formula for every type of decoder message.

### 5.2 Why add scores?

Explain in ordinary language: independent evidence contributes multiplicative likelihood ratios; logarithms convert multiplication to addition. Include a tiny optional example: ratios 4 and 2 combine to 8, so ln(4)+ln(2)=ln(8).

Qualify the independence assumption. In a graph with cycles, messages can become correlated. Excluding a destination avoids immediately echoing its own message, but does not make all evidence globally independent.

### 5.3 Complete the existing check example

For one even-parity check with channel scores [+4,-0.2,+3], show all outputs:

| Destination | Excluded input | Inputs used | Min-Sum advice | Combined score |
|---|---:|---|---:|---:|
| b0 | +4 | [-0.2,+3] | -0.2 | +3.8 |
| b1 | -0.2 | [+4,+3] | +3 | +2.8 |
| b2 | +3 | [+4,-0.2] | -0.2 | +2.8 |

Explain the sign by parity: the XOR of the other proposed bits determines the target bit required for even parity. The minimum magnitude is a Min-Sum approximation to confidence, not the definition of a parity constraint or an exact probability rule.

Ask the learner to predict two rows before revealing them. Keep supplied values and computed learner output visibly separate.

### 5.4 Decoder state table

| Quantity | Meaning | Educational representation | Initialization |
|---|---|---|---|
| Channel LLR L | Original received evidence | n values | Supplied by channel/demapper model |
| V→C message q | Bit evidence excluding destination check | One per edge | Channel LLR of that edge's bit |
| C→V message r | Check advice based on its other neighbors | One per edge | Zero before the first update |
| Posterior A | Channel plus all current incoming check messages | n values | Channel LLR |

Channel LLRs remain fixed within this decoding invocation. Hard decisions are derived from posterior signs; the decision at exactly zero is 0 in this course.

For the dense educational representation, explain H shape (m,n), q/r shape (m,n), and why nonedges are stored as zero. Dense storage is a teaching choice; do not silently alternate between dense and edge-only representations.

### 5.5 Two-iteration flooding example

Use a deliberately simple equality chain, explicitly identified as a new teaching fixture:

```text
H = [[1,1,0],
     [0,1,1]]
L = [3,-1,-1]
e0=(c0,b0), e1=(c0,b1), e2=(c1,b1), e3=(c1,b2)
```

For a degree-two equality check, the outgoing advice to one bit is the other bit's incoming message under uncorrected Min-Sum.

| Stage | Posterior/decision scores | Hard decisions | Syndrome |
|---|---|---|---|
| Initial | [3,-1,-1] | [0,1,1] | [1,0] |
| Iteration 1 | [2,1,-2] | [0,0,1] | [0,1] |
| Iteration 2 | [1,1,1] | [0,0,0] | [0,0] |

| Edge | Initial q | Iteration 1 r | Iteration 1 new q | Iteration 2 r |
|---|---:|---:|---:|---:|
| e0 | 3 | -1 | 3 | -2 |
| e1 | -1 | 3 | -2 | 3 |
| e2 | -1 | -1 | 2 | -1 |
| e3 | -1 | -1 | -1 | 2 |

Walk every row. For example, after iteration 1, the message b1→c1 is posterior(b1) minus c1's advice: 1-(-1)=2. That message helps b2 in iteration 2.

Learning point: information travels through successive exchanges. A failed check can change identity while the syndrome weight stays unchanged. Neither monotonically falling syndrome weight nor monotonically improving individual bits is guaranteed.

All checks send messages during a scheduled update, including checks whose current hard decisions satisfy parity. An initial syndrome test is an early-stop policy, not a trigger that enables only failed checks.

### 5.6 A concrete layered comparison

Use the same equality chain and L=[3,-1,-1], with old check messages initially zero. Process c0 then c1:

| Step | Extrinsic inputs | New check messages | Updated posterior |
|---|---|---|---|
| Initial | — | All zero | [3,-1,-1] |
| c0, bits [0,1] | [3,-1] | [-1,3] | [2,2,-1] |
| c1, bits [1,2] | [2,-1] | [-1,2] | [2,1,1] |

The second layer uses b1's updated posterior 2. Compare this with the flooding trace. This example demonstrates faster propagation for this fixture; it does not prove a universal latency advantage.

Then retain the existing nonzero-old-message example to teach replacement:

```text
posterior=[5,1,4], indices=[0,1], old_messages=[2,-1]
q=[3,2], new_messages=[2,3]
new_posterior=[5,5,4]
```

Explain why adding new messages without subtracting old ones double-counts contributions. Define a full layered iteration as one sweep through the declared layers and specify syndrome-check timing.

## 6. Restore min1/min2 and algorithm understanding

Add a dedicated lesson after the direct check-node implementation.

Start with q=[+7,-3,+5,-9]. Absolute magnitudes are [7,3,5,9]; min1=3, min2=5, argmin=1. Total negative-sign parity is even. Exclude each target sign and choose min2 only when excluding the selected minimum position.

Expected output: [+3,-5,+3,-3].

Then demonstrate these cases:

| Input | Required lesson |
|---|---|
| [3,3,5,9] | min1=3 and min2=3: second-smallest counts multiplicity. |
| [0,4,6] | Output [4,0,0]; excluding the only zero can produce a nonzero message. |
| [-2,+2,+8] | Output [+2,-2,-2]; repeated minima and sign exclusion both matter. |

State the tie policy for argmin. Define sign-of-zero as positive while retaining zero magnitude. Never divide by an input value to remove its sign; zeros make that approach unsafe.

Connect to hardware only after the operation is understood: sign XOR, magnitude extraction, comparison network, minimum index, output selector and optional offset/scaling. Explain whether minima are found serially over edges or in parallel.

Give a short Sum-Product comparison with an authoritative algorithm reference selected by the implementing agent. Explain what Min-Sum approximates; do not require a full probability derivation before learners can proceed. Preserve the distinction between NMS, OMS and the combined experimental correction supported by the current primitive.

## 7. QC lifting and the 5G bridge

### 7.1 Make the toy expansion complete

Retain B=[[0,1,-1],[2,-1,0]] with Z=4. Render the complete 8×12 expanded H with block boundaries, not just one 4×4 block. Highlight how one base entry generates four edges and how -1 generates none.

For base entry at row r, column c, with shift k, display:

```text
expanded check = r*Z + i
expanded bit   = c*Z + ((i+k) mod Z)
for i = 0,...,Z-1
```

### 7.2 Resolve rotation direction with actual data

Under the existing convention, columns of identity shift right. For Z=4 and k=1:

```text
P = [[0,1,0,0],
     [0,0,1,0],
     [0,0,0,1],
     [1,0,0,0]]
P @ [a,b,c,d] = [b,c,d,a]
right_rotate([a,b,c,d],1) = [d,a,b,c]
```

Explain that matrix construction and vector rotation name different operations. Establish one exact indexing rule for check-side gather and its inverse for scatter. A standalone right-rotation helper is fine, but its connection to the lifted graph must be explicit.

### 7.3 Keep the lifting-size correction

Preserve the finite allowed NR lifting sets, effective shifts 0 through Z-1, and the distinction between one Z-wide group and a whole codeword. Verify supplied tables against the pinned standard. A legal lifting size alone does not establish a valid NR configuration.

Provide the requested Z=2,8,32,96,192,384 examples with full small arrays, labeled large slices, modulo normalization and exact indexing. Include at least one nonmultiple of 32, such as 104, for lane masking.

### 7.4 Add a restricted real-NR milestone

Use the pinned [ETSI TS 138 212 V17.9.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf), especially segmentation, LDPC construction and rate-matching sections. This version was identified in the reviewed material and verified to exist; implementation assets still require independent validation.

Do not begin by supporting all configurations. Choose one documented base graph, legal lifting size and supported rate-matching configuration. Declare the input boundary: already recovered LLRs or transmitted-order LLRs. Then extend deliberately.

Teach and label the positions of payload, CRC where included, filler, full graph bits, structurally punctured bits, rate-matched bits and receiver LLRs. Known filler positions and unknown punctured positions must not receive the same representation. Explain repetitions and LLR accumulation if supported.

Use an independent standard-derived fixture or trusted reference implementation; local encoder/decoder agreement is insufficient evidence. Record source version, configuration, ordering, expected outputs and limitations. Keep receiver implementation policies separate from standard-defined encoding and rate-matching rules.

## 8. Fixed point and accelerator changes

### 8.1 Connect numeric primitives to the decoder

Keep saturation and quantization lessons, including ties-to-even as an explicit teaching policy. Add the actual numeric range after scaling. With width=4 and fraction_bits=1, the representable reconstructed range is -4 through 3.5 with step 0.5.

Specify widths and clipping points separately for channel LLRs, edge messages, posterior storage and intermediate accumulators. Show that clipping can destroy information needed by a later subtract-old operation; do not assume algebraically equivalent floating expressions remain bit-equivalent under saturation.

Address the most-negative two's-complement value: its positive magnitude may not fit in the same signed width. Choose widened magnitude arithmetic or another explicit policy and verify it.

Run float and fixed decoders on the same fixture and show the first divergent intermediate value, not only final bits. Include a case where quantization changes a decision and a case where it does not.

### 8.2 Keep the two hardware axes separate

The original prompt's proposed pipeline and questions about reducing minima across 32-lane groups are ambiguous. Correct them rather than copying them mechanically.

If lanes process different lifted positions i, each lane maintains minima over the neighboring edges of its own check position. Do not reduce unrelated positions into one minimum. If an alternative architecture assigns lanes to edges of one check, describe that mapping explicitly; its reduction structure is different.

Use a table indexed by lifted position and neighboring base-column edge. Label which axis is parallelized, which is reduced and which is traversed over time.

### 8.3 Turn grouping into a declared schedule

For P=32, the group counts for Z=32,96,192,384 are 1,3,6,12. For Z=104, counts are [32,32,32,8] and utilization is 81.25%. These are work groups, not decoder-cycle measurements.

As a teaching schedule, assume one vector of up to P edge messages can be processed per cycle and a check layer has degree d. A first pass over edges can accumulate sign parity and two minima; a second pass can form outgoing messages. A simple nonoverlapped model may therefore have 2*d*ceil(Z/P) issue cycles, before overhead. Label this as conditional on available bandwidth, buffering and the declared two-pass schedule, not a universal formula.

Require a cycle table with reads, computations, writes, valid lanes and dependencies. Explain buffering needed to retain messages or the bandwidth required to reread them. Include a shared-posterior RAW hazard between layers.

### 8.4 Teach memory banks before conflict counting

Explain that a single-read-port bank can serve one read per cycle. Then retain addresses [0,4,1] with bank=address mod 4. Show requested banks [0,0,1], one conflicting bank, and a possible two-cycle service schedule.

Next derive addresses from a QC edge fixture instead of arbitrary integers. Distinguish logical address, bank ID and within-bank address. State read/write-port assumptions and whether broadcast of identical addresses is supported.

## 9. Assignment-by-assignment revision checklist

| Existing assignment | Required improvement | Evidence of completion |
|---|---|---|
| 01 GF(2) | Preserve basics; connect mask AND and XOR reduction. | Hand parity prediction, empty-input convention and a real XOR hardware explanation. |
| 02 Syndrome | Add toy encoding, syndrome weight and another valid word. | Learner explains validity versus recovery on actual values. |
| 03 Graph | Add global edge table and bit-to-check view. | Matrix, graph and edge arrays use identical IDs. |
| 04 LLR decisions | Add observation-to-LLR bridge and noise experiment. | Learner distinguishes amplitude, score and hard bit. |
| 05 Check update | Show all excluded-input calculations; add min1/min2 checkpoint. | Signed, zero and repeated-minimum fixtures agree with independent expected outputs. |
| 06 Variable update | Add evidence-flow diagram and state legend. | Posterior versus per-destination output is explained and computed. |
| 07 Flooding | Show old/new arrays and complete edge trace. | No accidental partial in-place schedule; nonedges defined. |
| 08 Decoder | Add two-round example, wrong-valid result and capped failure. | Explicit status/iteration/history semantics; distinguish parity-valid from truth-correct. |
| 09 Corrections | Explain approximation and isolate OMS/NMS experiments. | Report observed changes without calling a parameter universally optimal. |
| 10 Layering | Show two overlapping layers and nonzero stored messages. | Learner identifies the changed input consumed by layer 2. |
| 11 Rotation | Link exact gather/scatter convention to block multiplication. | Basis/index fixtures catch opposite-direction mistakes. |
| 12 QC expansion | Show complete toy H and index mapping. | Dense and implicit connections match on independent expected indices. |
| 13 Lifting | Retain legal-set lookup; add a real configured slice later. | Scope does not confuse table lookup with NR decoding. |
| 14 Saturation | Explain overflow and most-negative magnitude handling. | Explicit boundary values and intermediate widths. |
| 15 Quantization | Visualize scale, round, clip and reconstruct. | Same values flow through the lesson, visual and public test. |
| 16 Lanes | Explain lane meaning; separate degree and position axes. | Correct grouping plus clearly scoped cycle assumptions. |
| 17 Banking | Teach banks; derive later examples from decoder addresses. | Conflict detection and a concrete service schedule. |

Do not force all additions into exactly 17 assignments. Preserve existing IDs where practical and add subcheckpoints or milestones. Explain any expansion beyond the original 16–22 target: short conceptual pages need not each become a coding assignment.

## 10. Required page structure and visual behavior

Every substantive assignment page must include:

1. A practical question and prerequisite recap.
2. Intuition before notation.
3. Input/output meanings, shapes, indices and conventions.
4. A tiny worked example with important intermediate values.
5. A visual tied to that exact example and a caption saying what to notice.
6. A prediction before revealing the full result.
7. A bounded learner TODO, with scaffolding and plotting provided.
8. Deterministic public checks, including a misconception-catching case.
9. A small experiment varying one parameter.
10. A reflection that asks for reasoning, not just restating a definition.
11. Three hints: conceptual, algorithm structure, near-pseudocode.
12. A hardware connection appropriate to the concept.
13. Clear completion criteria and a concise takeaway.

For each visual, author a specification containing fixture ID, labels, view type, selected element, step sequence, expected observation, caption, text fallback and whether data is supplied or learner-generated.

Replace mismatched fixtures: variable updates need a contribution diagram; layered updates need a posterior timeline; quantization needs scale/round/clip values. A generic LLR slider or flooding panel cannot substitute for these explanations.

Use shared fixture data for prose tables, UI and public examples where possible. Independently validate the fixture itself so shared data does not merely reproduce the same error everywhere. Use text and shape labels as well as color. Provide readable static traces alongside stepping controls.

Keep advanced panels collapsible, not prerequisite explanations. Changing a visualization must not automatically trigger a model request.

## 11. Tutor-chat context and behavior

Provide the tutor model with the active lesson, conventions, fixture, assignment contract, learner code and latest public results. Include expected intermediate values and the relevant conceptual explanation so a weaker model does not need to reconstruct the course or read the standard from scratch.

When debugging, the tutor should:

- Answer the direct question first.
- Identify one concrete mismatch using actual values.
- Ask the learner to inspect one useful intermediate quantity.
- Offer progressive hints before complete code.
- Distinguish a learner misunderstanding from an implementation bug.
- Avoid claiming that passing public checks proves general correctness or NR compliance.

Add misconception prompts such as: “Does H[0,3]=1 mean b3 must be one?”, “Why does a passing check still send advice?”, and “Which axis produces min1/min2 in this lane mapping?”

Do not grade open explanations solely by matching keywords. A learner should identify the quantities and explain the causal relationship in their own words.

## 12. Delivery milestones and priorities

### Priority 0 — Repair conceptual continuity

Complete toy encoding, terminology, edge IDs, channel-to-LLR explanation, state table, full check calculations, two-round flooding and two-layer traces. Correct independence wording and rotation ambiguity. Keep the current beginner material.

Deliverable: a beginner can manually trace the toy decoder before coding it.

### Priority 1 — Complete the foundation assignments

Add min1/min2, experiments, hints, meaningful hardware connections, operation-specific visuals and misconception tests. Verify every displayed fixture against its stated conventions.

Deliverable: an integrated toy decoder and clear explanations of corrections, schedules and QC indexing.

### Priority 2 — Fulfill the restricted NR scope

Provide verified graph assets and fixtures, documented codeword/index domains, supported rate recovery and one declared NR path. Add a phase-specific reading guide with exact sections, purpose and questions. Verify sources before quoting algorithm or implementation performance.

Deliverable: a restricted NR-compatible path with explicit boundaries and independent evidence.

### Priority 3 — Reach accelerator readiness

Build a complete fixed-point model, meaningful error-rate experiments, memory-access trace and cycle schedule. Compare lane counts and lifting sizes. Produce golden vectors and an architecture proposal with limitations.

Deliverable: a bit-accurate model and justified first RTL block, such as a QC routing unit or fixed-point check-node unit. Do not claim frequency, area or power without the corresponding implementation evidence.

## 13. Acceptance rubric

Score each lesson from 0–2 on each criterion: 0 absent, 1 partial, 2 clear and demonstrated.

| Criterion | Full-credit evidence |
|---|---|
| Motivation | Learner can explain why the operation exists. |
| Prerequisites | No essential unexplained term or notation. |
| Data meaning | Every relevant array, index and state has a definition. |
| Worked reasoning | Learner can reproduce intermediate values by hand. |
| Visual consistency | Diagram and example use the same values and conventions. |
| Assignment readiness | Learner knows the contract without being given the implementation. |
| Experiment | One controlled change leads to an observable result. |
| Misconception handling | A common wrong interpretation is explicitly tested. |
| Hardware connection | Actual arithmetic, storage or timing consequence is explained. |
| Scope honesty | Toy, algorithm, standard and implementation claims are distinguished. |

Target at least 17/20, with no zero in prerequisites, data meaning or worked reasoning. This is a proposed editorial gate, not a validated educational measurement.

Final learner demonstration: without looking at completed code, explain one bit's channel evidence, one outgoing variable message, one check message, one posterior update, one QC address mapping and one memory scheduling constraint. Passing unit tests alone is not sufficient.

## 14. Instructions to the implementing Codex agent

Revise the existing tutor using this brief and the original prompt. Treat the user's clarification about keeping basics as authoritative. Inspect the repository before editing and map every identified gap to its actual source file. The export lists likely sources such as `theory.json`, `manifest.json`, overview/architecture notes and the primer, walkthrough and lesson components; verify their current paths rather than assuming the export is synchronized.

Preserve working navigation, saved learner code, model selection, public checks, progress and reflections. Do not reset progress just to accommodate new pages; define prerequisite changes and migrations explicitly if needed.

Implement Priority 0 and Priority 1 as a coherent teaching revision before expanding the NR scope. Produce a change log distinguishing implemented content from planned milestones. Do not replace requested learning outcomes with “future work” while labeling the course complete.

Keep meaningful target implementations for the learner. Provide exact worked examples and test expectations, but do not fill every TODO as part of the teaching revision.

The finished version should make an engineer able to explain the algorithm's data and reasoning before asking them to optimize its software or hardware execution.

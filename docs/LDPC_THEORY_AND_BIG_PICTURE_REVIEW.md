# LDPC tutor: theory and big-picture explanations for review

Historical snapshot: 2026-10-09, **before** the detailed revision brief was implemented.
For the revised tutorial, read [LDPC_TUTOR_REVISED_REVIEW.md](LDPC_TUTOR_REVISED_REVIEW.md).
This file is retained unchanged below so the original external review remains traceable.

## Review brief

The learner starts without LDPC or communications theory knowledge and wants to learn Python concepts that eventually support hardware-accelerator design. Review the actual material below for correctness, beginner clarity, sequencing, unexplained notation, and whether the visuals explain the reasoning rather than merely display numbers.

Please give each chapter a clarity rating with reasons, identify specific confusing sentences or steps, check the arithmetic and assumptions, and suggest concrete replacements. Especially review chapter 5: does the learner understand where rule messages come from, why a destination is excluded, and why a valid candidate need not be the original message? Do not assume that passing public programming checks establishes full NR compliance.

## What this file contains

- All six introductory chapters: goals, big-picture content, complete theory prose, understanding questions/answers, and links to assignment purposes.
- All five states of the revised chapter 5 walkthrough and its optional maths.
- The authored overview and architecture notes.
- The lesson text, goals, prediction prompts and reflections for all 17 coding assignments.
- A static catalog of the provided assignment visual fixtures.

Theory and assignment lesson prose are copied from the authored data without rewriting. Interactive visuals are represented as text diagrams, tables and descriptions of their behavior; this file cannot reproduce clicks, layout, animation, or the chat itself. It contains no learner code, progress, chat history, API keys, private tests, or reference implementations.

Source files:

- curriculum/ldpc_5g/theory.json
- curriculum/ldpc_5g/manifest.json
- curriculum/ldpc_5g/overview.md
- curriculum/ldpc_5g/architecture.md
- web/src/components/ldpc/LdpcPrimer.tsx
- web/src/components/ldpc/DecodingWalk.tsx
- web/src/components/ldpc/LdpcLesson.tsx

This is a dated snapshot, not an automatically synchronized source. The running tutor continues to use the files above.

## Contents

1. Why do we need error correction?
2. Extra bits make mistakes recoverable
3. Parity rules, then the syndrome
4. What does LDPC actually mean?
5. How a decoder uses uncertain clues
6. From these ideas to 5G hardware

Then: course notes, assignment lessons, visual fixture catalog.


---

## Chapter 1: Why do we need error correction?

Goal: Understand the problem LDPC solves before learning its mathematics.

### The big picture

```text
Payload: the data you want to deliver
  ↓
Encoder: add relationships that protect the bits
  ↓
Channel: physical signal + noise; errors can occur
  ↓
Decoder: use observations + known rules to estimate the data
```

### Theory

#### Start with a message

A photo, a web page, and a voice recording can all be represented as bits: zeros and ones. Suppose your phone wants to send the three bits 101. The receiver needs those same three bits, not something that merely looks similar.

A radio does not send Python integers through the air. It turns bits into a physical signal. The receiver observes that signal and estimates the bits. Noise, interference, and weak reception can make an estimate wrong: a transmitted 1 might be read as 0. We call this a bit error. The channel is the path between transmitter and receiver, including these disturbances.

#### The difficulty: the receiver does not know what you sent

If the receiver sees 001, how could it know that the first bit was originally 1? Without extra information, 001 is also a perfectly possible message. Simply checking whether the values are zeros or ones tells us nothing.

Error-correcting coding adds carefully chosen extra bits before transmission. These extra bits create relationships that the receiver can check. The encoder adds this protection; the decoder uses the received observations and the relationships to estimate the original data. This costs transmission resources, but can avoid asking for the same data again. Recovery is not guaranteed under every noise pattern.

#### Where LDPC comes in

LDPC is one family of error-correcting codes. It specifies many simple relationships among transmitted bits, arranged so that a decoder can repeatedly exchange clues about which bits are likely wrong. Later pages explain each word in its name.

This is not encryption: we are not hiding the message. It is not compression: we add protection rather than simply make the message smaller. Nor is it modulation: modulation creates the physical signal; coding adds the bit relationships. Real communication systems combine these different jobs.

### Check your understanding

Question: If an unprotected 101 arrives as 001, can the receiver know which bit changed just by looking at 001?

Revealable answer: No. It could have been sent as 001. The receiver needs extra constraints or other evidence to distinguish possible original messages.

### Why you will write this code

- LDPC-01 — GF(2): bits are not ordinary numbers: Your first function will evaluate one tiny protection rule. It is a building block, not yet a decoder.


---

## Chapter 2: Extra bits make mistakes recoverable

Goal: Meet payloads, codewords, and code rate through a tiny example.

### The big picture

One payload bit becomes three copies. Click a received bit to introduce or remove an error.

```text
Payload = 1
Encoder sends 111
Initial received bits = 101 (middle bit flipped)
Majority vote estimates payload 1: it matches what we sent.

Also flip the first bit:
Received bits = 001
Majority vote estimates payload 0: it is wrong.
More than one flip defeated this code.
```

We show the transmitted value so YOU can compare. The receiver does not have this answer. This is a repetition-code toy, not the 5G LDPC algorithm.

Static export note: the app lets the learner change the payload and toggle any of the three errors. These are two representative states.

### Theory

#### A deliberately simple code

Suppose we send one data bit three times: 0 becomes 000, and 1 becomes 111. The original data bit is the payload. The protected three-bit sequence is the codeword. Only 000 and 111 are allowed codewords in this toy code.

If we send 111 and receive 101, the middle bit differs from the other two. A majority vote estimates that we sent 111, then recovers the payload 1. We can justify this when at most one of the three bits was flipped: each possible one-bit error is closer to its original codeword than to the other one.

#### Protection has a cost and a limit

We used three transmitted bits to carry one information bit. The code rate is information bits divided by codeword bits: here R = 1/3. This fraction is not a speed in bits per second. A lower code rate generally uses more redundancy, but the code structure and decoding method matter too.

Two flips can defeat this example: send 111, receive 001, and majority vote chooses 000. There is no unconditional promise of recovery. More redundancy does not mean every imaginable error becomes fixable.

#### From copying to shared rules

Repeating every bit is easy to understand but uses many extra bits. More useful codes share protection across groups of bits instead of making independent copies of each one. LDPC uses overlapping parity rules to do this.

The repetition example is a teaching model, not the 5G LDPC encoder. Keep its lesson: restrict which bit patterns are legal, then use that restriction to reason about noisy observations.

### Check your understanding

Question: For the toy code, we transmit 000 and receive 010. What does majority vote estimate, and what assumption makes that reliable?

Revealable answer: It estimates codeword 000 and payload 0. This is reliable if at most one bit was flipped. With more flips, the same received pattern might have come from the other codeword.

### Why you will write this code

- LDPC-08 — Assemble a toy decoder: The toy decoder later estimates legal bit patterns by iteration rather than by a hard-coded majority vote.


---

## Chapter 3: Parity rules, then the syndrome

Goal: Translate a protection rule into the operation you wrote in assignment 1.

### The big picture

Circles are bit values; squares are rules. A line means the rule includes that bit. Start with this valid candidate, then flip b1 to see two overlapping rules fail.

Flip a bit; select a check row. The same connections appear in the graph.

```text
         b0 b1 b2 b3 b4 b5
bits:     1  0  1  1  1  0
H c0:     1  1  0  1  0  0  → 0 (even)
H c1:     0  1  1  0  1  0  → 0 (even)
H c2:     1  0  1  0  0  1  → 0 (even)

Graph connections:
c0 ── b0, b1, b3
c1 ── b1, b2, b4
c2 ── b0, b2, b5

Flip b1 from 0 to 1:
bits     = [1, 1, 1, 1, 1, 0]
syndrome = [1, 1, 0]
```

Toy matrix. Syndrome [0, 0, 0] initially; weight 0. Matrix 1 = one edge. Zero syndrome proves parity validity, not original payload recovery.

Static export note: the app lets the learner select a rule and toggle any bit. The graph and syndrome update together. The diagram above preserves the connections, not the on-screen geometry.

### Theory

#### One rule, explained without a matrix

Parity means whether a group contains an even or odd number of ones. An even-parity rule asks for an even number: 00 has zero ones, 11 has two, and both satisfy the rule. 01 and 10 each have one and break it.

XOR is the bit operation that computes parity. For two bits: 0 XOR 0 = 0, 0 XOR 1 = 1, 1 XOR 0 = 1, and 1 XOR 1 = 0. Across a group, the result is 0 for an even number of ones and 1 for an odd number. Thus 0 means this even-parity rule passes; 1 means it fails.

#### Who decides the rule—and how does the receiver know it?

GF(2) is arithmetic: a calculation can return either 0 or 1. It does not require every result to be zero. The linear LDPC code we are studying defines valid codewords as those giving zero for every parity check. That zero requirement comes from the code. Odd-parity conventions can be used in other settings.

The transmitter and receiver already know the agreed code, including its check rules. The encoder adds parity bits so the codeword meets those rules before transmission. We do not normally send the matrix H or the expected zero syndrome along with every codeword.

Tiny teaching example: payload [a,b] = [1,0]. Add p = a XOR b = 1. Transmit [a,b,p] = [1,0,1]. Both ends know the rule a XOR b XOR p = 0. The receiver checks the received bits using that rule: [1,0,1] gives 0, but [1,0,0] gives 1. The parity bit travels as part of the encoded message; the syndrome is calculated locally by the receiver. This single check detects inconsistency but cannot uniquely locate or correct the wrong bit. It is not a full 5G encoder.

#### Why assignment 1 uses a dot product

A rule needs to select which bits to check. In the assignment fixture, rule c0 selects b0, b1, and b3. Write its selection mask as [1, 1, 0, 1, 0, 0]. Multiply each mask entry by the matching bit, add the selected values, and take the remainder after division by 2. This is your gf2_dot.

For bits [1, 0, 1, 1, 1, 0], c0 gives (1 + 0 + 1) mod 2 = 0. Ordinary addition would give 2; parity gives 0. GF(2) is the name for arithmetic on the two values 0 and 1 with addition modulo 2. Your function tells us whether ONE selected rule is satisfied.

#### Several rules form a matrix; their results form a syndrome

Stack the selection masks as rows of a table named H, the parity-check matrix. Each column refers to one bit; each row refers to one rule. A 1 means the rule includes that bit, not that the bit's value must be 1.

Evaluate every row on the candidate bits. The resulting list is the syndrome. Three rules produce three syndrome entries, even if there are six bits. In notation s = H b mod 2, H is the table, b is the bit list, and s is the rule-result list. The next assignment applies your gf2_dot once per row.

#### A failed rule is a clue, not an instruction to flip a particular bit

If c0 fails, at least one selected bit is inconsistent, but c0 alone does not tell us which one. Other overlapping rules and the receiver's confidence help a decoder choose an estimate.

An all-zero syndrome says the candidate satisfies all these parity rules. It does NOT prove it is the codeword originally sent. In the repetition example, both 000 and 111 satisfy the rules that neighboring bits agree. Noise could turn one into the other. Checking validity and recovering the original message are different tasks.

### Check your understanding

Question: There are six bits and three rules. How many entries does the syndrome have? Does [0, 0, 0] guarantee the original payload?

Revealable answer: Three entries, one per rule. An all-zero syndrome means the candidate is a valid codeword under these rules; it does not guarantee it is the transmitted one.

### Why you will write this code

- LDPC-01 — GF(2): bits are not ordinary numbers: gf2_dot computes one row's parity.
- LDPC-02 — Syndrome: which rules are broken?: syndrome collects all the row results. It detects violated rules, not the original payload by itself.


---

## Chapter 4: What does LDPC actually mean?

Goal: See how sparse, overlapping rules become a graph and a memory layout.

### The big picture

Circles are bit values; squares are rules. A line means the rule includes that bit. Start with this valid candidate, then flip b1 to see two overlapping rules fail.

Flip a bit; select a check row. The same connections appear in the graph.

```text
         b0 b1 b2 b3 b4 b5
bits:     1  0  1  1  1  0
H c0:     1  1  0  1  0  0  → 0 (even)
H c1:     0  1  1  0  1  0  → 0 (even)
H c2:     1  0  1  0  0  1  → 0 (even)

Graph connections:
c0 ── b0, b1, b3
c1 ── b1, b2, b4
c2 ── b0, b2, b5

Flip b1 from 0 to 1:
bits     = [1, 1, 1, 1, 1, 0]
syndrome = [1, 1, 0]
```

Toy matrix. Syndrome [0, 0, 0] initially; weight 0. Matrix 1 = one edge. Zero syndrome proves parity validity, not original payload recovery.

Static export note: the app lets the learner select a rule and toggle any bit. The graph and syndrome update together. The diagram above preserves the connections, not the on-screen geometry.

### Theory

#### Low Density Parity Check, one word at a time

Parity check: each rule tests the even parity of selected bits. Low density: the parity-check matrix has relatively few ones compared with its total number of entries. Each rule connects to a small fraction of the bits. This describes the CONNECTION TABLE, not how many ones occur in the payload.

Real LDPC matrices can be large. The small six-bit fixture here illustrates notation and connections, not the sparsity or performance of a practical 5G code. A sparse table lets a decoder work on the actual connections instead of repeatedly processing every possible bit-rule pair.

#### The same table drawn as a Tanner graph

Draw one circle for each bit (a variable node) and one square for each parity rule (a check node). Draw a line only where H has a 1. This drawing is called a Tanner graph. Its edges are the connections; its neighbors are the nodes directly connected to a particular node.

In our fixture, c0 has neighbors b0, b1, and b3. Bit b1 connects to c0 and c1. That overlap matters: evidence about b1 can link two rules. A graph edge is not a separate transmitted bit; it is a relationship on which decoder messages will travel.

#### Why you will write a neighbor-list function

A dense matrix is useful on paper. A decoder can instead store the indices of connected bits: c0 -> [0, 1, 3]. Assignment 3 builds those lists. The check calculation later visits only these neighbors.

For hardware, the same list raises practical questions: where are the bit values stored, which addresses must we read together, and how many memory ports do we need? First learn the relationship; later we will make its implementation efficient.

### Check your understanding

Question: If H[0, 3] = 1, does it force bit b3 to equal 1?

Revealable answer: No. It means rule c0 includes b3 in its parity calculation. The bit value is stored separately and may be 0 or 1.

### Why you will write this code

- LDPC-03 — Tanner graph: store connections: Neighbor lists turn the graph's edges into the indices your Python code will process.


---

## Chapter 5: How a decoder uses uncertain clues

Goal: Understand confidence and message passing before implementing the update equations.

### The big picture

#### How can a rule help a weak guess?

Follow one small example. Three received bits share one even-parity rule. The receiver does not know the original bits.

A **guess** says 0 or 1. **Confidence** says how strongly the observation supports that guess. The numbers are explained below; you do not need their formula yet.

The interface walks through five stages. All stage explanations are reproduced below; the diagrams and tables are static equivalents of the changing cards.

#### Step 1: The middle bit is only a weak guess

The receiver has three noisy observations. The first and last strongly suggest 0. The middle only slightly suggests 1. If we keep just the guesses, we get [0, 1, 0]. We have not checked the coding rule yet.

#### Step 2: The guesses disagree with a known rule

Both transmitter and receiver know this rule: these three bits must contain an even number of ones. Our guesses [0, 1, 0] contain one 1, so the rule fails. This tells us something is inconsistent—not which bit is wrong.

#### Step 3: Ask what the OTHER two bits suggest

To advise the middle bit, this rule looks only at the first and last bits. Both strongly suggest 0. If those two are 0, the middle must also be 0 to make the rule pass. So the rule sends evidence favoring 0 to the middle bit. It does not use the middle bit's own guess as fresh evidence.

#### Step 4: The new evidence outweighs the weak guess

The middle bit's radio clue weakly favors 1. The rule's evidence more strongly favors 0. The decoder combines them, and the middle bit's guess changes to 0. This is an evidence-based update, not a command to flip any bit in a failing rule.

#### Step 5: The revised guesses now satisfy the rule

After each bit combines its radio clue with its rule message, the guesses are [0, 0, 0]. There are zero ones—an even number—so the rule passes. We found a valid candidate. We still do not know for certain that it is what was sent.

#### Initial visual state (steps 1–3)

| Bit | Guess | Support |
| --- | --- | --- |
| First bit · b0 | 0 | Strong support for 0 |
| Middle bit · b1 | 1 | Weak support for 1 |
| Last bit · b2 | 0 | Strong support for 0 |

Known rule: an even number of ones. b0 XOR b1 XOR b2 must equal 0.

At step 1: not checked yet.
At step 2: 0 XOR 1 XOR 0 = 1 → rule fails.

#### Evidence-flow visual (step 3)

```text
b0: likely 0             b2: likely 0
           ↓ other bits' evidence ↓
             EVEN-PARITY RULE
                 ↓ advice for b1 ↓
       “These clues favor you being 0.”
```

The rule’s message is advice computed by the decoder. It is not a new bit arriving over the radio.

#### Numerical combine visual (step 4)

Now put numbers to the evidence: **positive favors 0; negative favors 1.** A larger distance from zero means stronger support. Read the labels if you prefer; the calculation method is optional below.

```text
Original radio clue  +  Rule's new evidence  =  Combined confidence
       −0.2          +          +3          =         +2.8
 weakly favors 1             favors 0             now favors 0
```

| Bit | Original radio clue (unchanged) | Combined confidence | Revised guess |
| --- | --- | --- | --- |
| b0 | +4 | +3.8 | 0 |
| b1 | −0.2 | +2.8 | 0 |
| b2 | +3 | +2.8 | 0 |

At step 4: new candidate ready; next, test it again.
At step 5: 0 XOR 0 XOR 0 = 0 → rule passes.

#### Optional maths: what do +4, −0.2 and +3 mean?

These signed confidence scores are called LLRs. In this course, positive favors bit 0, negative favors bit 1, and a larger distance from zero means stronger support. Zero is undecided; our code chooses 0 for that tie. These are not probabilities or raw radio amplitudes.

The radio scores stay fixed: [+4, −0.2, +3]. A separate combined score is updated. For the middle bit, a Min-Sum check uses ONLY the other scores, +4 and +3. Both favor 0, and the weaker magnitude is 3, so its advice is +3. This approximation limits the message by its weakest input.

```text
b1 radio clue        = -0.2
rule → b1 message    = +3.0
b1 combined score    = +2.8
positive score       → guess 0
```

The rule also advises the other bits. Their combined scores are +3.8 and +2.8, so their guesses remain 0. This is why the final candidate is [0, 0, 0], not just a guessed change to the middle bit. The later assignments derive the signs, minima, and exclusion of each destination.

Big picture: radio clues → test the known rule → exchange evidence → revise guesses → test again. A real LDPC graph has many overlapping rules and repeats this process up to a stopping condition or limit. This single-rule example illustrates one update, not guaranteed error correction.

Static export note: the interface shows one stage at a time with Back/Next buttons. Optional maths is initially collapsed. For these illustrative scores, the card renderer labels magnitude below 1 as “Weak” and otherwise “Strong”; that display threshold is not an NR rule or a universal decoder threshold.

### Theory

#### 1. Keep how sure you are, not just your guess

A noisy radio observation can suggest a bit is 1 without being very convincing. Another observation can strongly suggest 0. If we save only the guessed bits, we lose this difference.

A hard decision is just the guess: 0 or 1. Soft information also keeps how strongly the observation supports it. In the walkthrough, the first and last bits strongly favor 0. The middle bit only weakly favors 1. Their initial guesses are [0, 1, 0]. The receiver does not know the original bits; these are estimates.

#### 2. A failed rule raises a question

Both ends know that these three bits must contain an even number of ones. The guesses [0, 1, 0] contain one 1, so they fail this rule.

Does that mean the middle bit must be wrong? No. The first bit or last bit could also be wrong. A parity failure tells us the guesses are inconsistent. It does not name the guilty bit. We need to use confidence as well as the rule.

#### 3. The rule advises a bit using its other neighbors

Focus on the middle bit. Ask: if the first and last bits are both 0, what must the middle bit be for even parity? It must be 0 too. Since the other two observations strongly favor 0, the rule can provide evidence that the middle bit should be 0.

This advice is called a check-to-bit message. It is calculated inside the decoder; it is not another signal sent by the transmitter. To advise the middle bit, the check uses only the OTHER two bits. Reusing the middle bit's own weak guess as new support would count the same clue twice. If either of the other bits were uncertain, the advice should be weaker.

#### 4. Combine the old clue with the new evidence

The middle bit now has two sources of evidence: its original radio observation weakly favors 1, while the rule's message favors 0 more strongly. Combining them changes its guess to 0.

Our numeric scores use positive for support for 0 and negative for support for 1. The original middle-bit score is -0.2, and this rule's message is +3. Adding them gives +2.8, so the revised guess is 0. The original radio clue stays -0.2; we store the combined score separately. The walkthrough's optional maths explains where +3 comes from. It is not an arbitrary reward for passing a rule.

#### 5. Check again—and repeat when necessary

In this example, all three bits receive their own rule messages. Their combined scores are [+3.8, +2.8, +2.8], so the revised guesses are [0, 0, 0]. The rule now passes. The one-entry syndrome is [0]. This establishes a valid candidate, not proof of the original message.

A real LDPC graph has many overlapping rules. Each rule sends advice to its connected bits. Each bit combines advice from its connected rules with its original radio clue. One round of these updates is an iteration. If some rules still fail, the decoder can do another iteration, up to a fixed limit. It does not blindly flip every bit belonging to a broken rule, and it does not always recover the original message.

#### Names you will meet in the assignments

LLR (log-likelihood ratio): the signed confidence score. Its sign picks the favored bit; its distance from zero indicates strength. It compares how likely the observation would be if 0 versus 1 were sent. It is not itself a probability or raw radio amplitude. At zero, this course chooses bit 0 as a tie-break.

Min-Sum: the approximate method used here to compute a check's message from the other neighbors' signs and weakest confidence. It is one algorithm choice, not the definition of LDPC.

Assignments 4–8 build these parts separately: make guesses from scores, compute rule advice, combine evidence at bits, perform one round, then repeat rounds in a toy decoder. Later assignments compare confidence corrections and update orders. You do not need those later details to understand the five-step picture above.

### Check your understanding

Question: Why should a message from a parity rule to b1 exclude b1's own incoming message?

Revealable answer: It should provide evidence from the other connected bits. Otherwise b1's original guess is echoed back as new support, double-counting the same evidence.

### Why you will write this code

- LDPC-04 — Soft bits: hard decisions from LLRs: Turn signed confidence into candidate bits.
- LDPC-05 — Check-node messages: exclude the recipient: Compute a rule's outgoing evidence.
- LDPC-06 — Variable-node messages: remove the destination: Combine evidence at a bit without echoing the destination.
- LDPC-07 — One flooding iteration: freeze old messages: Connect the updates into one iteration.
- LDPC-08 — Assemble a toy decoder: Repeat iterations with a stopping condition.
- LDPC-09 — Correct Min-Sum confidence: Study corrections to the Min-Sum approximation.
- LDPC-10 — Layered update: remove old, add new: Study the remove-old/add-new invariant used by a layered schedule.


---

## Chapter 6: From these ideas to 5G hardware

Goal: Know what every assignment contributes—and what this course does not yet implement.

### The big picture

```text
Mathematical model
  Parity, neighbors, soft messages, iteration
  ↓
Structured data movement
  QC shifts and lifted groups
  ↓
Finite arithmetic
  Scale, round, clip
  ↓
Parallel implementation
  Lane groups, memory access, scheduling
```

### Theory

#### The 5G connection

5G NR uses LDPC coding for uplink and downlink shared-channel data. This does not mean every 5G channel uses LDPC. Our pinned reference is ETSI TS 138 212 V17.9.0, section 5.3.2 and the shared-channel processing sections.

Practical NR LDPC uses structured base graphs and lifting: small graph entries describe larger blocks of cyclic connections. The course first uses tiny teaching examples so that the arithmetic is visible. Toy parity matrices and toy decoder results are not claims of NR compliance.

#### Why structure is good for an accelerator

A quasi-cyclic (QC) block can describe a connection as a cyclic shift instead of storing every matrix entry. A lifting size Z tells you how many positions belong to a lifted group. This structure can support regular address generation and parallel processing. Assignments 11–13 introduce rotations, toy QC expansion, and the standard lifting-size sets. They do not supply the full BG1/BG2 tables or a complete 5G encoder.

A Python float can represent confidence conveniently. Hardware often uses a limited-width signed integer code with a scale. Assignments 14–15 explore saturation (clipping to the representable range) and quantization (scaling and rounding before clipping). These affect numerical behavior, not just storage size.

#### Arithmetic alone is not an accelerator

Imagine processing 104 positions with 32 parallel lanes. Three full groups cover 96 positions, so a fourth group processes the remaining 8. Assignment 16 computes this grouping and its utilization—not total decoder latency.

If several lanes request the same single-port memory bank at once, they cannot all be served in one cycle. Assignment 17 detects collisions for a simple assumed bank mapping. Real performance also needs a schedule, memory-port model, dependencies, iteration count, and clock timing. Those are future steps; a collision count is not a finished hardware design.

#### Your course roadmap

1–3: represent parity rules and their connections.
4–8: turn soft observations and those rules into a toy iterative decoder.
9–10: investigate algorithm corrections and update scheduling.
11–13: learn cyclic structure and lifting conventions relevant to NR.
14–17: begin thinking like a hardware designer about precision, lanes, and memory.

You can now return to the assignment you were working on. Passing tests checks these small public contracts, not full decoder performance. A later full-NR project still needs the actual base graphs, surrounding rate-recovery/segmentation processing, realistic channel experiments, and a complete scheduled decoder implementation.

### Check your understanding

Question: Why is a correct Python syndrome function useful but insufficient to claim a working 5G hardware decoder?

Revealable answer: It implements only a rule-validity check. A full system also needs soft-input decoding, the actual NR code structure and surrounding processing, numerical and scheduling choices, and hardware verification.

### Why you will write this code

- LDPC-11 — QC rotation: follow the indices: Represent cyclic data movement.
- LDPC-12 — Lift a toy QC base matrix: Expand a toy base graph into parity connections.
- LDPC-13 — NR lifting sizes: legal is not every integer: Recognize supported NR lifting sets.
- LDPC-14 — Saturation: overflow must be deliberate: Model finite signed range.
- LDPC-15 — Quantization: scale, round, clip: Model the conversion to fixed-point codes.
- LDPC-16 — 32 lanes: model work, not clock frequency: Plan parallel lane groups.
- LDPC-17 — Memory banking: compute lanes can still stall: Identify simple memory-bank conflicts.

Standards reference: [ETSI TS 138 212 V17.9.0 (5G NR coding)](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf). You do not need to read the standard before these exercises.


---

## Course overview (authored source)

#### LDPC: understand before accelerating
Implement one small Python idea, predict its result, run public checks, then ask the guide about actual evidence.
##### What works in this first course
- Parity, syndrome, sparse graph, LLR decisions, Min-Sum, flooding toy decoder and one layered update.
- QC rotations/expansion, verified NR lifting-size sets, saturation, quantization, lane groups and memory-bank conflicts.
- Interactive visual walkthroughs, saved Python work, public reports, prerequisite progression and OpenCode chat.
##### Not yet a full 5G decoder
- BG1/BG2 coefficient assets, selection, encoding, CRC/segmentation and rate recovery need independently verified fixtures.
- Full fixed-point decoder, BER/BLER Monte Carlo, memory-bank/cycle model and hardware synthesis remain future milestones.
- The first decoder uses an authored toy graph, not an NR base graph. Zero syndrome does not prove the original payload.
##### Conventions
- H rows are checks; columns are bits. Edge order is increasing variable index in each row.
- Positive LLR favors 0; zero decides 0. Channel mapping is 0→+1 and 1→-1.
- Vector rotation is right. QC blocks are identity matrices with columns shifted right; matrix-vector multiplication uses the inverse vector mapping.
- Floating primitives use finite arrays. Fixed codes use explicit saturation and ties-to-even rounding.
- Completion reruns PUBLIC checks only. There are no secret tests or adversarial grading claims.


## Architecture notes (authored source)

#### The learning path
bits → parity checks → graph edges → confidence messages → toy decoder
→ structured QC groups → bounded numeric codes → parallel lane groups
##### Standard anchor
Pinned source: ETSI TS 138 212 V17.9.0 (2024-08), Section 5.3.2 and Table 5.3.2-1.
https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf
Only the lifting-size sets are supplied as NR data in this release. All teaching matrices are toy examples. Algorithms and quantization policies are implementation choices.
##### Accelerator boundary
CNU minima reduce incident edges per check position. Physical lanes may process independent lifted positions. Never confuse those axes. Group count alone is not full layer latency. Model memory access and dependencies before claiming throughput.



---

## Assignment lesson appendix

These are authored lessons, not the learner’s completed assignments. The lesson blocks below retain the existing text, including any awkward wording, so they can be reviewed honestly. Visual fixtures are described separately in the final appendix.

### LDPC-01: GF(2): bits are not ordinary numbers

Goal: Return the parity of the pairwise AND of equal-length binary vectors. Ordinary addition counts; modulo two asks whether the count is odd.

Provided visual fixture: parity

#### The question
GF(2): bits are not ordinary numbers

#### Intuition
Think of a check as a rule: the selected bits must contain an even number of ones. GF(2) is arithmetic with only 0 and 1. Addition wraps after one; it becomes XOR. Multiplication becomes AND. We start here because every later parity check uses exactly this operation.

#### Walk the example
```text
[1,1,1] AND [1,0,1] = [1,0,1]
count = 2 → parity = 0
1 XOR 1 = 0, not 2.
```

#### Representation and contract
a,b: binary 1-D arrays of equal length; return Python int 0 or 1. Do not mutate inputs. Empty equal vectors return 0.

#### Your task
Complete only gf2.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why is counting ones alone not the final parity result?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

How does parity change when one selected bit is flipped?

#### Reflection after passing visible checks

Why is counting ones alone not the final parity result?

### LDPC-02: Syndrome: which rules are broken?

Goal: Compute one parity result per row of H. A zero syndrome means the candidate is a valid codeword, not necessarily the original transmitted word.

Provided visual fixture: parity

#### The question
Syndrome: which rules are broken?

#### Intuition
Each row selects the bits connected to one rule. A one means select this bit; a zero means ignore it. The syndrome is the list of rule results. It has one entry per row, not per bit. Two different codewords can both satisfy all the rules; parity alone cannot tell which was sent.

#### Walk the example
```text
H = [[1,1,0,1,0,0],
     [0,1,1,0,1,0],
     [1,0,1,0,0,1]]
bits = [1,0,1,1,1,0]
row 0: 1 XOR 0 XOR 1 = 0
row 1: 0 XOR 1 XOR 1 = 0
row 2: 1 XOR 1 XOR 0 = 0
flip b1 → syndrome [1,1,0]
```

#### Representation and contract
bits: length n binary array; h: binary shape (m,n); return binary shape (m,), preserve inputs.

#### Your task
Complete only syndrome.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why can the syndrome be zero even when the decoded payload is wrong?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

Before flipping b1, predict which rows select it.

#### Reflection after passing visible checks

Why can the syndrome be zero even when the decoded payload is wrong?

### LDPC-03: Tanner graph: store connections

Goal: Turn each row of the binary parity matrix into a list of variable indices. Ordering is ascending variable index.

Provided visual fixture: graph

#### The question
Tanner graph: store connections

#### Intuition
A Tanner graph has two kinds of nodes: bits and parity checks. An edge says this check uses that bit. Sparse storage records only the connections. If the matrix is mostly zero, storing all zeros wastes memory. Graph edge order later determines where messages live, so freeze it now.

#### Walk the example
```text
row c0: [1,1,0,1,0,0] → [0,1,3]
c0 connects to b0, b1, b3.
A matrix 1 = one graph edge.
```

#### Representation and contract
h: shape (m,n); return list of m lists of integer indices. Empty rows produce an empty list.

#### Your task
Complete only graph.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why does an edge list save storage but require careful indexing?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

How many edges leave check c0?

#### Reflection after passing visible checks

Why does an edge list save storage but require careful indexing?

### LDPC-04: Soft bits: hard decisions from LLRs

Goal: Use LLR = log(P(bit 0)/P(bit 1)). Positive favors zero, negative favors one. Exactly zero chooses zero in this course.

Provided visual fixture: llr

#### The question
Soft bits: hard decisions from LLRs

#### Intuition
A radio observation is uncertain. A hard bit discards confidence; an LLR keeps both the favored bit and how strongly it is favored. Here bit 0 maps to BPSK +1 and bit 1 to -1. Received amplitude is not itself an LLR unless noise scaling is accounted for. This checkpoint starts with supplied LLRs, not an unmodeled radio.

#### Walk the example
```text
LLRs:  [+1.3, +0.15, -0.2, -2.1, 0]
bits:  [   0,     0,    1,    1, 0]
Small magnitude = uncertain, not a third bit.
```

#### Representation and contract
llrs: finite 1-D real array; return binary integer array of same length. No mutation.

#### Your task
Complete only channel.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why must the zero tie policy be fixed before comparing decoders?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

Which is more confident: +0.15 or -2.1?

#### Reflection after passing visible checks

Why must the zero tie policy be fixed before comparing decoders?

### LDPC-05: Check-node messages: exclude the recipient

Goal: For each edge, exclude that edge; multiply signs of the others and use their minimum absolute value. Zero has positive sign but zero magnitude. Degree must be at least two.

Provided visual fixture: cnu

#### The question
Check-node messages: exclude the recipient

#### Intuition
The check tells each bit what the other bits suggest. It must not send a bit its own evidence back. This is extrinsic information: information from elsewhere. Min-Sum approximates the confidence calculation with a minimum. It is an algorithm choice, not a 5G standard requirement.

#### Walk the example
```text
incoming: [+7,-3,+5,-9]
to e0: exclude +7; use [-3,+5,-9]
two negatives → positive; min magnitude 3 → +3
all outgoing: [+3,-5,+3,-3]
```

#### Representation and contract
q: finite 1-D float array length d >= 2; return float array (d,). Preserve input.

#### Your task
Complete only minsum.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why would including the recipient's own message create misleading confidence?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

What changes when two incoming magnitudes share the minimum?

#### Reflection after passing visible checks

Why would including the recipient's own message create misleading confidence?

### LDPC-06: Variable-node messages: remove the destination

Goal: Compute posterior = channel LLR + sum incoming. Outgoing edge j equals posterior minus incoming[j].

Provided visual fixture: llr

#### The question
Variable-node messages: remove the destination

#### Intuition
The variable node combines independent evidence from its channel and neighboring checks. For a decision, use all contributions. For a message back to a check, remove that check's own contribution. This subtraction is also central to layered hardware: old stored messages are removed before new ones are added.

#### Walk the example
```text
channel = 2; incoming = [3,-1]
posterior = 2+3-1 = 4
to edge 0: 4-3 = 1
to edge 1: 4-(-1) = 5
```

#### Representation and contract
channel_llr: scalar; incoming: finite 1-D floats; return tuple (posterior scalar, outgoing array).

#### Your task
Complete only variable.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
How does subtracting the destination prevent feedback from reinforcing itself?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

Which value is used for the bit decision: posterior or outgoing e0?

#### Reflection after passing visible checks

How does subtracting the destination prevent feedback from reinforcing itself?

### LDPC-07: One flooding iteration: freeze old messages

Goal: Compute all check messages from old v2c, then all posteriors and new v2c. Store zero at nonedges.

Provided visual fixture: iteration

#### The question
One flooding iteration: freeze old messages

#### Intuition
An iteration is a controlled exchange of evidence. Flooding separates two phases: every check reads the same old message state, then variables combine the new check results. Updating v2c halfway through the check phase accidentally changes the schedule. The dense representation is deliberately small and educational; a hardware decoder will store edges or QC groups instead.

#### Walk the example
```text
H = [[1,1,0],[0,1,1]]
channel = [3,-1,2]
old V→C = [[3,-1,0],[0,-1,2]]
new C→V = [[-1,3,0],[0,2,-1]]
posterior = [2,4,1]
new V→C = [[3,1,0],[0,2,2]]
```

#### Representation and contract
h: binary (m,n) with every check degree >=2; channel: (n,); v2c: (m,n). Return (c2v, new_v2c, posterior).

#### Your task
Complete only iteration.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Which arrays are old and which are new during each phase?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

What would happen if check 1 saw an already updated message from check 0?

#### Reflection after passing visible checks

Which arrays are old and which are new during each phase?

### LDPC-08: Assemble a toy decoder

Goal: Initialize v2c from channel at edges. Check initial syndrome. Run flooding steps until zero syndrome or the iteration cap. Return bits, iterations used, and syndrome weight history including initial state.

Provided visual fixture: iteration

#### The question
Assemble a toy decoder

#### Intuition
Reuse your primitives, not a library decoder. The iteration cap makes execution bounded. An initial valid candidate can stop with zero iterations. Stop means the candidate satisfies parity; it does not prove it matches the transmitted payload. This is a toy code, not a 5G NR codeword or realistic performance benchmark.

#### Walk the example
```text
H = [[1,1,0],[0,1,1]] checks equality
channel = [-0.2,3,3]
initial bits [1,0,0] → syndrome weight 1
first posterior [2.8,5.8,6] → bits [0,0,0]
weight history [1,0], iterations used 1
```

#### Representation and contract
Return dict: bits array (n,), iterations int, syndrome_weights list. max_iterations >=0. Toy code only.

#### Your task
Complete only decoder.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why should syndrome history include the initial hard decision?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

With an iteration cap of zero, can the decoder repair a bit?

#### Reflection after passing visible checks

Why should syndrome history include the initial hard decision?

### LDPC-09: Correct Min-Sum confidence

Goal: Start from uncorrected check_messages. Preserve sign; output magnitude alpha * max(abs(r)-beta,0). alpha in (0,1], beta >=0. beta=0 is NMS; alpha=1 is OMS.

Provided visual fixture: cnu

#### The question
Correct Min-Sum confidence

#### Intuition
Min-Sum often overstates check confidence compared with the more exact sum-product calculation. Scaling or subtracting an offset can soften it. These correction parameters are implementation choices. This checkpoint allows a combined rule for experimentation, but the comparison experiments should isolate OMS and NMS rather than pretend this choice is standard-defined.

#### Walk the example
```text
uncorrected [+3,-5,+3,-3]
OMS beta=1 → [+2,-4,+2,-2]
NMS alpha=0.5 → [+1.5,-2.5,+1.5,-1.5]
```

#### Representation and contract
Finite q length >=2; return array same shape. No mutation.

#### Your task
Complete only corrected.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why does a correction parameter need an experiment rather than being called a universal constant?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

What happens to magnitude 0.5 with offset 1?

#### Reflection after passing visible checks

Why does a correction parameter need an experiment rather than being called a universal constant?

### LDPC-10: Layered update: remove old, add new

Goal: For this one check layer, q = posterior[indices] - old_messages; compute new check messages; replace those contributions in a copy of posterior.

Provided visual fixture: iteration

#### The question
Layered update: remove old, add new

#### Intuition
Flooding waits for the full check phase. Layered decoding updates posterior information immediately after each layer. The next layer reads the new posterior. Stored old check messages must be subtracted first or evidence gets counted twice. A hardware pipeline must respect the read-after-write dependency between overlapping layers.

#### Walk the example
```text
posterior [5,1,4]; selected indices [0,1]
old check contributions [2,-1]
extrinsic q = [3,2]
new check contributions [2,3]
new posterior [5,5,4]
```

#### Representation and contract
indices: unique ascending indices, degree >=2; old_messages: same length. Return (new_posterior, new_messages).

#### Your task
Complete only layered.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
When could two layers run at once without sharing a posterior entry?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

Which posterior entry changes in this example, and which stays untouched?

#### Reflection after passing visible checks

When could two layers run at once without sharing a posterior entry?

### LDPC-11: QC rotation: follow the indices

Goal: Rotate right by shift modulo vector length: output[i] = input[(i-shift) mod Z]. Reject empty vectors with ValueError.

Provided visual fixture: rotation

#### The question
QC rotation: follow the indices

#### Intuition
QC means quasi-cyclic: connections repeat with circular shifts. Rotating a vector changes addresses, not message arithmetic. This lesson fixes a right-rotation convention explicitly. Matrix-times-column-vector may require the inverse rotation; do not infer direction from a picture alone. An 8-lane rotation can use conditional shifts of 1, 2 and 4; this is one architecture, not a universal solution.

#### Walk the example
```text
Z=8, right shift 3:
[0,1,2,3,4,5,6,7] → [5,6,7,0,1,2,3,4]
right shift 11 is the same because 11 mod 8 = 3.
```

#### Representation and contract
Nonempty 1-D array, integer shift (negative supported); return same shape and dtype, no mutation.

#### Your task
Complete only rotation.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Could memory address mapping replace physical movement for this operation?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

Where does input index 0 appear after right shift 3?

#### Reflection after passing visible checks

Could memory address mapping replace physical movement for this operation?

### LDPC-12: Lift a toy QC base matrix

Goal: Replace -1 by zero block; nonnegative k by identity with columns rotated right k mod Z. Set block[i,(i+k) mod Z]=1.

Provided visual fixture: qc

#### The question
Lift a toy QC base matrix

#### Intuition
A base matrix compresses a large structured parity matrix. A nonempty entry describes Z connections; -1 describes none. Dense expansion is for understanding and tiny fixtures, not the production storage format. This example is not BG1 or BG2. Matrix right-shift convention follows the pinned standard construction, but B itself is authored toy data. Multiplying this block by a column vector produces the inverse of our right vector rotation.

#### Walk the example
```text
B=[[0,1,-1],[2,-1,0]], Z=4
expanded H has 8 rows and 12 columns.
Each k describes a 4×4 block, not one edge.
I shifted right 1 has row0 [0,1,0,0].
```

#### Representation and contract
base: integer (r,c), entries >=-1; z positive int. Return binary array (r*z,c*z). Toy base only.

#### Your task
Complete only qc.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why can we store a shift coefficient instead of Z squared binary entries?

#### Scope
Toy mathematical / algorithm example; not a full NR code.

#### Predict before you code

How many ones does one nonempty Z×Z permutation block contain?

#### Reflection after passing visible checks

Why can we store a shift coefficient instead of Z squared binary entries?

### LDPC-13: NR lifting sizes: legal is not every integer

Goal: Return the set index 0..7 for a legal NR lifting size from provided LIFTING_SETS. Unsupported Z raises ValueError.

Provided visual fixture: rotation

#### The question
NR lifting sizes: legal is not every integer

#### Intuition
The lifting size determines the width of each QC block. NR defines a finite list of choices. A table set index also selects the correct base-graph shift coefficients; it is not a random grouping. This lesson uses verified lifting-set data only: it does not implement BG selection, encoding, rate matching or a complete NR decoder.

#### Walk the example
```text
Z=8 belongs to set 0; Z=96 belongs to set 1.
Z=384: effective rotations 0..383.
Z=97 is not a legal lifting size.
A full codeword contains many Z-wide groups, not just Z bits.
```

#### Representation and contract
z integer. Return Python int. Standards data: TS38.212 V17.9.0 Table 5.3.2-1.

#### Your task
Complete only lifting.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
How is lifting size different from total codeword length?

#### Scope
Standard-derived lifting-size data only. Other NR behavior is not yet implemented.

#### Predict before you code

Is 97 legal just because it lies between 2 and 384?

#### Reflection after passing visible checks

How is lifting size different from total codeword length?

### LDPC-14: Saturation: overflow must be deliberate

Goal: Clip integer values to two's-complement signed range [-2^(w-1),2^(w-1)-1]. Width >=2. Return int64 array.

Provided visual fixture: fixed

#### The question
Saturation: overflow must be deliberate

#### Intuition
Finite hardware storage cannot hold arbitrarily large values. Saturation clamps to the nearest limit; wraparound changes the sign and can turn strong confidence into the opposite bit. Signed width alone defines range, not fractional precision. We use explicit integer codes here before introducing a scale.

#### Walk the example
```text
width 4 → range -8..7
[-12,-8,-1,0,7,11] → [-8,-8,-1,0,7,7]
clip, do not wrap 11 into a negative number.
```

#### Representation and contract
values: integer array representable in int64; width 2..32. Use wider intermediates, preserve input.

#### Your task
Complete only fixed.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
Why is saturating a posterior safer than relying on accidental NumPy overflow?

#### Scope
Implementation-choice model; not a measured accelerator.

#### Predict before you code

What is the largest positive value in six signed bits?

#### Reflection after passing visible checks

Why is saturating a posterior safer than relying on accidental NumPy overflow?

### LDPC-15: Quantization: scale, round, clip

Goal: Return stored integer codes: values * 2^fraction_bits, round ties to even, then signed saturation. fraction_bits >=0; inputs finite.

Provided visual fixture: fixed

#### The question
Quantization: scale, round, clip

#### Intuition
Quantization trades precision and range for bounded storage. Fractional bits set the step size; total signed bits set the integer-code range. Rounding ties to even is an explicit teaching convention, not a mandatory accelerator choice. The eventual full decoder must specify each quantization point and accumulator width; this primitive alone is not a bit-accurate complete decoder.

#### Walk the example
```text
width=4, fractional bits=1:
[1.25,1.75,-1.25,10]
scaled [2.5,3.5,-2.5,20]
rounded [2,4,-2,20]
clipped codes [2,4,-2,7]
reconstructed [1,2,-1,3.5]
```

#### Representation and contract
Return int64 array. Real reconstructed value = code / 2^fraction_bits. Use saturate_signed helper.

#### Your task
Complete only quantize.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
What changes if the fractional-bit count increases but total width stays fixed?

#### Scope
Implementation-choice model; not a measured accelerator.

#### Predict before you code

Why does 1.25 round differently from 1.75 at this scale?

#### Reflection after passing visible checks

What changes if the fractional-bit count increases but total width stays fixed?

### LDPC-16: 32 lanes: model work, not clock frequency

Goal: Partition z independent lifted positions into groups of at most lanes. Return groups count, valid count per group, utilization = z/(groups*lanes). Positive integers only.

Provided visual fixture: lanes

#### The question
32 lanes: model work, not clock frequency

#### Intuition
Parallel lanes process multiple lifted check positions at once. The number of neighbors of a check is a different axis: minima are reduced over incident-edge messages for each check position, not across unrelated Z positions. This model counts lane groups only. Actual layer latency also needs edge reads, memory ports, pipeline delays and hazards. No frequency, throughput or area has been synthesized.

#### Walk the example
```text
Z=384, P=32 → 12 full groups
Z=104, P=32 → [32,32,32,8]
utilization 104/128 = 0.8125
Z=352 is exactly divisible by 32: 11 groups.
```

#### Representation and contract
Return dict with groups:int, valid:list[int], utilization:float. This is a lane-issue model, not total decoder cycles.

#### Your task
Complete only lanes.py. Use the worked values to predict your result before running the public checks. Provided plotting and sandbox plumbing are not your assignment.

#### Hardware connection
What extra assumptions are required to turn a group count into a decoder cycle estimate?

#### Scope
Implementation-choice model; not a measured accelerator.

#### Predict before you code

Which group needs masking for Z=104 and P=32?

#### Reflection after passing visible checks

What extra assumptions are required to turn a group count into a decoder cycle estimate?

### LDPC-17: Memory banking: compute lanes can still stall

Goal: Detect conflicts in a simple single-read-port modulo-banked memory.

Provided visual fixture: banks

#### The problem
32 compute lanes may need data at once. Each SRAM bank has a limited number of ports. If two reads need one single-ported bank, one must wait even while other banks are idle.

#### Walk the example
```text
4 banks, addresses [0,4,1]
bank IDs [0,0,1]
counts [2,1,0,0]
bank 0 has two requests for one port → conflict
```

#### Your task
Model this one issue group. Return bank IDs and per-bank counts before declaring a conflict. Preserve the original address array.

#### Hardware connection
Changing memory layout, adding ports, buffering, or scheduling reads in different cycles can help, but each costs something. This toy modulo mapping is an implementation choice, not a standard rule.

#### Next NR milestone
You now have the primitives. A full NR course still needs verified BG1/BG2 tables and fixtures, rate recovery, the complete bit-accurate decoder, cycle scheduling and performance experiments. Do not label this toy path a complete 5G accelerator.

#### Predict before you code

With four banks, can addresses 0 and 4 be read in the same cycle?

#### Reflection after passing visible checks

Could a different layout, a second port, or staggering reads avoid the conflict?


---

## Assignment visual fixture catalog (static equivalents)

These visuals use supplied teaching values, not the learner’s run output. A fixture may be reused across multiple assignments; the assignment appendix names its fixture key.

### parity / graph

Same matrix, bit toggles, selected check and Tanner connections as the big-picture panel in chapters 3 and 4. Initially syndrome [0,0,0]; flipping b1 gives [1,1,0].

### llr

Slider from −5 to +5; initial value +0.15. Negative selects bit 1; nonnegative selects bit 0, including the zero tie. A bar has width proportional to absolute score over this slider range. Caption: “Magnitude measures confidence. At zero choose bit 0. This is an LLR, not raw channel amplitude.” The bar is not a probability calibration.

### cnu

Select which edge receives the outgoing message. Its own input is excluded.

```text
Signed fixture q = [7, -3, 5, -9]
To e0: other inputs [-3, 5, -9]
       sign product = +1; minimum magnitude = 3; outgoing = +3

Repeated-minimum alternative q = [3, 3, 5, 9]
To e0: other inputs [3, 5, 9]
       sign product = +1; minimum magnitude = 3; outgoing = +3
```

Caption: “Uncorrected toy Min-Sum. Click the destination edge. Repeated minima must still work after exclusion. OMS/NMS adjust magnitude afterward.”

### iteration

The four selectable states of the provided flooding fixture:

```text
H = [[1,1,0], [0,1,1]]

1. Channel [3,-1,2]
   old V→C [[3,-1,0],[0,-1,2]]

2. All checks read OLD messages
   C→V [[-1,3,0],[0,2,-1]]

3. posterior = channel + incoming
   [2,4,1] → bits [0,0,0]

4. new V→C excludes destination
   [[3,1,0],[0,2,2]]
   syndrome [0,0]
```

Caption: “Worked flooding fixture: H=[[1,1,0],[0,1,1]]. Not your run output. Layered decoding uses a different order; see its remove-old/add-new example.”

### rotation

Z options: 2,8,32,96,192,384. Initial Z=8, right shift=3. Normalize the shift modulo Z. Each displayed output shows the source index: out[i] = input[(i−shift) mod Z]. At large Z, only indices 0–11 are displayed, explicitly labeled as a slice.

Caption: “Right VECTOR rotation. Identity columns shifted right give the inverse mapping when multiplying a column vector. Width Z is not codeword length.”

### qc

Z=4 toy block; shift options 0–3, initially 1. Right-shifting identity columns by one produces:

```text
0 1 0 0
0 0 1 0
0 0 0 1
1 0 0 0
```

Caption: “Z=4 toy block. Each row selects one column; one base entry encodes four edges. Not a BG1/BG2 fixture.”

### fixed

Signed-width options 4,5,6,8; initially 4, range −8..7. The table distinguishes clipped values from preserved ones:

| Integer code | Stored at width 4 | Action |
| --- | --- | --- |
| −40 | −8 | clip |
| −12 | −8 | clip |
| −1 | −1 | preserve |
| 0 | 0 | preserve |
| 7 | 7 | preserve |
| 40 | 7 | clip |

Quantization scales and rounds before clipping; this visual is integer-code saturation only.

### lanes

Z options: 2,32,96,104,192,352,384. P=32; initially Z=104. Four groups have valid lane counts [32,32,32,8]. Utilization is 104/(4×32) = 81.25%.

Caption: “One pass of lane groups, not total decoder cycles. Lanes process lifted positions; minima reduce check neighbors on a separate axis. Memory ports, edge counts and hazards are not modeled yet.”

### banks

Four single-read-port banks with bank = address mod 4. Toggle between these issue groups:

```text
Colliding addresses [0,4,1] → bank IDs [0,0,1]
Bank 0 gets 2 reads: one-port conflict.
Banks 1,2,3 get 1,0,0 reads: capacity OK.

Conflict-free addresses [0,1,2,3] → bank IDs [0,1,2,3]
Each bank gets 1 read: capacity OK.
```

Caption: “Modulo mapping, four single-read-port banks. Bank capacity is independent of how many arithmetic lanes are available. Toy issue-group model, not a full decoder schedule.”

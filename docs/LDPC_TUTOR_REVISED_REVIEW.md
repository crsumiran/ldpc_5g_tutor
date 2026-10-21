# Revised LDPC teaching review

Snapshot: 10 October 2026. Current beginner theory, self-contained assignment prose and supplied visual traces. This is not execution evidence or a complete NR accelerator. See docs/LDPC_REVISION_STATUS.md for implemented versus pending scope.

## Overview
# LDPC: understand before accelerating
Implement one small Python idea, predict its result, run public checks, then ask the guide about actual evidence.
## What works in this first course
- Six beginner chapters and 18 checkpoints; the original path remains intact, with an optional min1/min2 branch (LDPC-18) after LDPC-05.
- Toy encoding, linked global edges, AWGN-to-LLR explanation, complete two-round flooding and two-layer worked traces.
- Parity, syndrome, sparse graph, LLR decisions, Min-Sum, flooding toy decoder and one layered update.
- QC rotations/expansion, verified NR lifting-size sets, saturation, quantization, lane groups and memory-bank conflicts.
- Interactive visual walkthroughs, saved Python work, public reports, prerequisite progression and OpenCode chat.
- Worked fixtures are supplied examples, not learner run output. Reveal intermediate values, compare a controlled variant, and follow operation-specific tables without making a model request.
## Not yet a full 5G decoder
- BG1/BG2 coefficient assets, selection, encoding, CRC/segmentation and rate recovery need independently verified fixtures.
- Full fixed-point decoder, BER/BLER Monte Carlo, memory-bank/cycle model and hardware synthesis remain future milestones.
- The first decoder uses an authored toy graph, not an NR base graph. Zero syndrome does not prove the original payload.
## Conventions
- H rows are checks; columns are bits. Edge order is increasing variable index in each row.
- Positive LLR favors 0; zero decides 0. Channel mapping is 0→+1 and 1→-1.
- Vector rotation is right. QC blocks are identity matrices with columns shifted right; matrix-vector multiplication uses the inverse vector mapping.
- Floating primitives use finite arrays. Fixed codes use explicit saturation and ties-to-even rounding.
- Completion reruns PUBLIC checks only. There are no secret tests or adversarial grading claims.

## Architecture
# The learning path
bits → parity checks → graph edges → confidence messages → toy decoder
→ structured QC groups → bounded numeric codes → parallel lane groups
## Standard anchor
Pinned source: ETSI TS 138 212 V17.9.0 (2024-08), Section 5.3.2 and Table 5.3.2-1.
https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf
Only the lifting-size sets are supplied as NR data in this release. All teaching matrices are toy examples. Algorithms and quantization policies are implementation choices.
## Accelerator boundary
CNU minima reduce incident edges per check position. Physical lanes may process independent lifted positions. Never confuse those axes. Group count alone is not full layer latency. Model memory access and dependencies before claiming throughput.

## Current teaching architecture
Theory prose lives in theory.json; checkpoint revisions live in lesson_revisions.json.
fixtures.json supplies the same worked values and visual specifications to the UI
and tutor context. Public cases use independently checked expectations.
LDPC-18 is appended for stable IDs but depends only on LDPC-05. Workspace upgrades
create missing Python assets exclusively, never overwrite learner files or reset grades.
The two-pass issue table is a declared teaching model, not a complete scheduled decoder.


## Theory: Why do we need error correction?
Understand the problem LDPC solves before learning its mathematics.

### A message arrives with a mistake
Imagine sending a friend the three bits 101. Perhaps those bits are part of a photograph or a voice recording. Whatever they represent, you want your friend to receive exactly the same values.

But a radio does not carry neat little zeros and ones through the air. It carries a physical signal. The receiver measures that signal and decides which bits it most likely represents. Noise can make that decision wrong, so your 101 might arrive as 001. The first bit has changed.

Here is the difficulty: your friend does not have your original 101 to compare against. Looking at 001, they cannot tell whether you sent 001 correctly or sent something else that was damaged. Both explanations are possible. The received bits alone contain no note saying which ones are wrong.

### Give the receiver something it can check
To help, we can add extra bits before sending the message. We choose those extra bits so that the complete sequence follows rules that both sides already know. If the receiver's guesses break a rule, it has a reason to suspect an error. With enough useful rules and information about the received signal, it may also be able to work out a better guess.

The original information is called the payload. The process of adding protection is encoding, and the protected sequence is called a codeword. At the receiving end, decoding means using the noisy observations and the known rules to estimate the original information.

Notice what the receiver is given: the observations and the rules, not the answer. When a teaching example shows you what was actually sent, that is for you to judge the result. A real decoder cannot look up the transmitted message.

### This is the problem LDPC is designed to solve
LDPC is a way to build these protection rules and use them to recover information after transmission errors. It is not a way to hide the message or shrink it. We deliberately send some extra information because we want the receiver to have a better chance of recovering the data.

You do not need to understand its name or its equations yet. First, we will try the simplest possible protection: sending a bit more than once. That example will show why adding information can help, and why it still cannot promise to fix every error.

<details>
<summary>Optional reference material — not part of the main story</summary>

### Optional Python and NumPy refresher
Before assignment 1, try these tiny expressions in your editor. An array stores values; its shape tells you what the indices mean.
```python
import numpy as np
bits = np.array([1, 0, 1])
mask = np.array([1, 0, 1])
print(bits.shape)           # (3,) -- one index
print(bits[mask == 1])      # [1 1] -- select positions
h = np.array([[1, 1, 0], [0, 1, 1]])
print(h.shape)              # (2, 3) -- rows, columns
print(h[1, 2])              # 1 -- rule 1 includes bit 2
print(np.flatnonzero(h[0])) # [0 1] -- nonzero indices
copy = bits.copy()         # independent storage
copy[0] = 0                # bits is unchanged
```

Python a ^ b is XOR for integer bits; a & b selects with a binary mask. Do not confuse XOR with ordinary addition. A comparison such as scores < 0 returns a Boolean array; astype(int) converts False/True to 0/1. np.zeros((m,n)) initializes a matrix; a scalar, vector, and matrix are different shapes. The NumPy docs are at https://numpy.org/doc/stable/user/absolute_beginners.html. These snippets are preparation, not solutions to your target functions.

</details>

### Understanding check
If an unprotected 101 arrives as 001, can the receiver know which bit changed just by looking at 001?
No. It could have been sent as 001. The receiver needs extra constraints or other evidence to distinguish possible original messages.

### Assignment connections
LDPC-01: Your first function will evaluate one tiny protection rule. It is a building block, not yet a decoder.

## Theory: Extra bits make mistakes recoverable
Meet payloads, codewords, and code rate through a tiny example.

### Send one bit three times
In the previous chapter, the receiver had no way to check an unprotected message. Let's give it a very simple rule: every bit is sent three times.

If the payload is 0, we send 000. If the payload is 1, we send 111. Those are the only two codewords this little system is allowed to send. Patterns such as 101 and 001 are not legal transmitted words, because their three copies disagree.

Now suppose we send 111 and the receiver guesses 101. Two positions suggest 1 and one suggests 0. Taking a majority vote gives 1, so the receiver estimates that the codeword was 111 and recovers the original payload bit.

### Why that choice makes sense
Compare 101 with the two allowed codewords. It differs from 111 in just one position. It differs from 000 in two positions. If we assume that at most one bit was flipped, 111 is the only possible original word.

Counting the positions that differ is called Hamming distance. The name is less important than the reasoning: we made the possible transmitted words different enough that a small mistake still leaves us closer to the original one.

But the assumption matters. If we send 111 and two bits flip, we might receive 001. Majority vote now chooses 000 and returns payload 0. The same decoder that fixed one error makes a wrong decision after two. It does not know how many flips actually happened.

### Protection costs extra bits
We transmitted three bits to carry one information bit. The fraction of transmitted bits that represent original information is called the code rate. Here it is 1/3. This is a fraction, not a clock frequency or a transmission speed.

Repeating everything works as a first illustration, but it is expensive. We would like several information bits to share their protection instead of giving every bit its own copies. The next chapter introduces parity rules, which let us protect groups of bits together.

Keep the central idea: a code restricts which patterns can be sent. The receiver uses those restrictions to make sense of a noisy pattern. Whether it succeeds depends on the code, the errors and the way we decode—not simply on how many extra bits we added.

### Understanding check
For the toy code, we transmit 000 and receive 010. What does majority vote estimate, and what assumption makes that reliable?
It estimates codeword 000 and payload 0. This is reliable if at most one bit was flipped. With more flips, the same received pattern might have come from the other codeword.

### Assignment connections
LDPC-08: The toy decoder later estimates legal bit patterns by iteration rather than by a hard-coded majority vote.

## Theory: Parity rules, then the syndrome
Translate a protection rule into the operation you wrote in assignment 1.

### Protect a group instead of copying every bit
We have seen how three copies can protect one bit. Now let's protect two bits with just one extra bit.

Suppose the payload is 10. We add a third bit so that the complete group contains an even number of ones. There is currently one 1, so we add another 1 and send 101. If the payload were 11, we would add 0 and send 110, because two ones is already an even number.

This is an even-parity rule. Parity simply describes whether the number of ones is even or odd. Zero ones also counts as even, so 000 passes the rule too. The encoder chooses the extra parity bit to make the rule pass before transmission.

### The receiver checks the same rule
Both ends already know that the group should have even parity. The receiver does not need us to send that rule again with every message. The extra parity bit does travel with the message; the rule itself is agreed in advance.

If our transmitted 101 is guessed as 100, the receiver counts one 1 instead of two. The rule fails, so the receiver knows this candidate is inconsistent. However, the rule does not tell it which position changed. Changing any one of the three bits could restore even parity.

XOR is the operation we use to do this check. XOR across a group returns 0 when the number of ones is even and 1 when it is odd. Thus 1 XOR 0 XOR 1 gives 0, while 1 XOR 0 XOR 0 gives 1.

You will also see the name GF(2). It means arithmetic on the two values 0 and 1, where addition behaves like XOR. That arithmetic can produce either value. It is our chosen code that requires a valid word's parity checks to produce 0; GF(2) does not independently force every calculation to be zero.

### Give the bits several overlapping rules
One rule can detect a problem, but it offers little help locating it. Let's use several rules that overlap. This is the six-bit toy example used in the assignments.

Call the three payload bits b0, b1 and b2. Add three parity bits: b3 makes the group b0,b1,b3 even; b4 makes b1,b2,b4 even; and b5 makes b0,b2,b5 even.

For payload 101, the first group needs b3=1, the second needs b4=1, and the third needs b5=0. Our complete codeword is therefore [1,0,1,1,1,0]. You can check each group: each contains two ones, so all three rules pass. The first three positions carry the payload in this particular toy code.

Now flip b1 from 0 to 1. The candidate becomes [1,1,1,1,1,0]. The first and second rules break, while the third still passes. That is more useful than a single failed rule: the two broken groups share b1. It is a clue about what might have happened, although a full decoder must also consider other possible errors.

### A matrix records the rules; a syndrome records their results
Instead of writing the groups in words, we can record them in a table called H, the parity-check matrix. Each row is one rule and each column is one bit. A 1 means include that bit; a 0 means leave it out. It does not mean that the bit itself must be 1.

Evaluating all the rows produces a list called the syndrome. For our damaged candidate, the results are [1,1,0]: broken, broken, passing. There are three entries because there are three rules, even though there are six bits. The syndrome weight is just the number of broken rules—two here.

An all-zero syndrome means the candidate follows every rule. It does not prove it is the message we sent. For example, [0,0,1,0,1,1] also passes all three rules, but carries a different payload. The receiver's job is not merely to find any word that passes: it is to use the observations and rules to estimate the word that was actually transmitted.

This gives the first two assignments their purpose. Your parity function evaluates one rule. Your syndrome function collects the results of all the rules. Next, we will draw those same connections so we can see how information moves between them.

<details>
<summary>Optional reference material — not part of the main story</summary>

### Why assignment 1 uses a dot product
A rule needs to select which bits to check. In the assignment fixture, rule c0 selects b0, b1, and b3. Write its selection mask as [1, 1, 0, 1, 0, 0]. Multiply each mask entry by the matching bit, add the selected values, and take the remainder after division by 2. This is your gf2_dot.

For bits [1, 0, 1, 1, 1, 0], c0 gives (1 + 0 + 1) mod 2 = 0. Ordinary addition would give 2; parity gives 0. GF(2) is the name for arithmetic on the two values 0 and 1 with addition modulo 2. Your function tells us whether ONE selected rule is satisfied.

</details>

### Understanding check
There are six bits and three rules. How many entries does the syndrome have? Does [0, 0, 0] guarantee the original payload?
Three entries, one per rule. An all-zero syndrome means the candidate is a valid codeword under these rules; it does not guarantee it is the transmitted one.

### Worked visual: Toy systematic layout: payload positions 0–2
Fixture: toy-encode. supplied teaching fixture; not learner output
Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.

#### Encode payload [1,0,1]

| Step | Calculation | Result |
| --- | --- | --- |
| Payload | b0,b1,b2 | [1,0,1] |
| b3 | b0 XOR b1 | 1 |
| b4 | b1 XOR b2 | 1 |
| b5 | b0 XOR b2 | 0 |
| Codeword | payload followed by parity | [1,0,1,1,1,0] |
Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.

#### All checks on the transmitted codeword

| Check | Selected bit values | XOR | Syndrome entry |
| --- | --- | --- | --- |
| c0 | 1,0,1 | 1 XOR 0 XOR 1 | 0 |
| c1 | 0,1,1 | 0 XOR 1 XOR 1 | 0 |
| c2 | 1,1,0 | 1 XOR 1 XOR 0 | 0 |
Syndrome shape (3,), not payload shape by coincidence.

#### Flip b1

| Candidate | Syndrome | Weight |
| --- | --- | --- |
| [1,1,1,1,1,0] | [1,1,0] | 2 |
Weight counts broken checks, not necessarily bit errors.

#### A different valid word

| Codeword | Payload | Syndrome |
| --- | --- | --- |
| [1,0,1,1,1,0] | [1,0,1] | [0,0,0] |
| [0,0,1,0,1,1] | [0,0,1] | [0,0,0] |
Valid codewords can carry different data.

Visual specification:
```json
{
  "labels": [
    "Step",
    "Calculation",
    "Result"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Encode payload [1,0,1]",
    "All checks on the transmitted codeword",
    "Flip b1",
    "A different valid word"
  ],
  "expected_observation": "Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.",
  "caption": "Toy systematic layout: payload positions 0–2",
  "text_fallback": "Encode payload [1,0,1]\nStep | Calculation | Result\nPayload | b0,b1,b2 | [1,0,1]\nb3 | b0 XOR b1 | 1\nb4 | b1 XOR b2 | 1\nb5 | b0 XOR b2 | 0\nCodeword | payload followed by parity | [1,0,1,1,1,0]\n\nAll checks on the transmitted codeword\nCheck | Selected bit values | XOR | Syndrome entry\nc0 | 1,0,1 | 1 XOR 0 XOR 1 | 0\nc1 | 0,1,1 | 0 XOR 1 XOR 1 | 0\nc2 | 1,1,0 | 1 XOR 1 XOR 0 | 0\n\nFlip b1\nCandidate | Syndrome | Weight\n[1,1,1,1,1,0] | [1,1,0] | 2\n\nA different valid word\nCodeword | Payload | Syndrome\n[1,0,1,1,1,0] | [1,0,1] | [0,0,0]\n[0,0,1,0,1,1] | [0,0,1] | [0,0,0]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Assignment connections
LDPC-01: gf2_dot computes one row's parity.
LDPC-02: syndrome collects all the row results. It detects violated rules, not the original payload by itself.

## Theory: What does LDPC actually mean?
See how sparse, overlapping rules become a graph and a memory layout.

### Draw the connections we already know
In the last chapter, bit b1 belonged to two rules. That overlap gave us a useful clue when b1 was flipped. A drawing makes these relationships easier to follow.

Draw a circle for each bit and a square for each parity rule. Connect a bit to a rule when that rule includes it. For example, the first rule connects to b0, b1 and b3. Bit b1 connects to the first and second rules.

This drawing is called a Tanner graph. It contains exactly the same information as H, just in a different form. A line is called an edge, and the nodes at the ends of that line are neighbors. The edge is a relationship—not an extra bit transmitted over the radio.

### Why the name says low density
LDPC stands for Low Density Parity Check. We already know what a parity check does. Low density describes the connection table: most entries of H are zero, so each rule includes only a small fraction of all the bits.

It does not describe how many ones happen to be in your message. A payload full of ones can still use an LDPC code. The sparsity is in the rules, not in the data.

Our six-bit table is deliberately tiny so you can check it by hand. It is not a realistic demonstration of how sparse a large LDPC matrix is. In a practical code, there may be many bits and many rules, but each rule still connects to only a few of those bits.

### A small set of neighbors is enough to work with
If a rule includes only b0, b1 and b3, its calculation needs those three values. It does not need to inspect every bit in the codeword. We can store its neighbors as the list [0,1,3] instead of repeatedly reading a whole row of zeros and ones.

That is why assignment 3 asks you to build neighbor lists. It is preparing the connections that the decoder will use, not solving a separate graph puzzle.

The drawing will become more useful in the next chapter. Each rule will use its neighbors to advise a bit, and each bit will combine advice from its connected rules. No new information arrives from the transmitter during that conversation: it all happens inside the receiver, using the original observations and the known connections.

<details>
<summary>Optional reference material — not part of the main story</summary>

### Stable edges connect equations to memory
Use row-major global edge IDs in the supplied nine-edge fixture: e0=(c0,b0), e1=(c0,b1), e2=(c0,b3), e3=(c1,b1), e4=(c1,b2), e5=(c1,b4), e6=(c2,b0), e7=(c2,b2), e8=(c2,b5). No edge exists at an H entry of zero.

The bit-to-check message on e3 is q[3]; the check-to-bit message is r[3]. Bit b1 receives r[1] and r[3]. Dense teaching arrays instead store these at [check,bit], so e3 maps to [1,1]. Dense non-edge entries must stay zero. Select e3 below and follow its line and addresses. These IDs apply only to this fixture; another H gets another edge map.

</details>

### Understanding check
If H[0, 3] = 1, does it force bit b3 to equal 1?
No. It means rule c0 includes b3 in its parity calculation. The bit value is stored separately and may be 0 or 1.

### Worked visual: Toy 3×6 matrix; row-major GLOBAL edge IDs
Fixture: toy-edges. supplied teaching fixture; not learner output
An edge has two endpoints and two directed messages, not a transmitted bit.

#### Global edge table

| Edge | Check | Bit | Message addresses |
| --- | --- | --- | --- |
| e0 | c0 | b0 | q[e0], r[e0] |
| e1 | c0 | b1 | q[e1], r[e1] |
| e2 | c0 | b3 | q[e2], r[e2] |
| e3 | c1 | b1 | q[e3], r[e3] |
| e4 | c1 | b2 | q[e4], r[e4] |
| e5 | c1 | b4 | q[e5], r[e5] |
| e6 | c2 | b0 | q[e6], r[e6] |
| e7 | c2 | b2 | q[e7], r[e7] |
| e8 | c2 | b5 | q[e8], r[e8] |
An edge has two endpoints and two directed messages, not a transmitted bit.

#### Bit-to-check view

| Bit | Connected checks | Global edges |
| --- | --- | --- |
| b0 | c0, c2 | e0, e6 |
| b1 | c0, c1 | e1, e3 |
| b2 | c1, c2 | e4, e7 |
| b3 | c0 | e2 |
| b4 | c1 | e5 |
| b5 | c2 | e8 |
b1 has distinct outgoing messages on e1 and e3.

Visual specification:
```json
{
  "labels": [
    "Edge",
    "Check",
    "Bit",
    "Message addresses"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Global edge table",
    "Bit-to-check view"
  ],
  "expected_observation": "An edge has two endpoints and two directed messages, not a transmitted bit.",
  "caption": "Toy 3×6 matrix; row-major GLOBAL edge IDs",
  "text_fallback": "Global edge table\nEdge | Check | Bit | Message addresses\ne0 | c0 | b0 | q[e0], r[e0]\ne1 | c0 | b1 | q[e1], r[e1]\ne2 | c0 | b3 | q[e2], r[e2]\ne3 | c1 | b1 | q[e3], r[e3]\ne4 | c1 | b2 | q[e4], r[e4]\ne5 | c1 | b4 | q[e5], r[e5]\ne6 | c2 | b0 | q[e6], r[e6]\ne7 | c2 | b2 | q[e7], r[e7]\ne8 | c2 | b5 | q[e8], r[e8]\n\nBit-to-check view\nBit | Connected checks | Global edges\nb0 | c0, c2 | e0, e6\nb1 | c0, c1 | e1, e3\nb2 | c1, c2 | e4, e7\nb3 | c0 | e2\nb4 | c1 | e5\nb5 | c2 | e8",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Assignment connections
LDPC-03: Neighbor lists turn the graph's edges into the indices your Python code will process.

## Theory: How a decoder uses uncertain clues
Understand confidence and message passing before implementing the update equations.

### A guess does not tell the whole story
So far, we have checked rules using bits that are already 0 or 1. But a receiver is not equally sure about every bit. One noisy observation may strongly suggest 0, while another only slightly suggests 1. If we keep just the guesses, we throw away that difference.

To see why it matters, let's follow one small example from beginning to end. We are looking at three bits connected to one even-parity rule, not at the whole six-bit code from the earlier chapters. The receiver strongly favors 0 for the first bit, weakly favors 1 for the middle bit, and strongly favors 0 for the last bit.

Its first guesses are therefore [0,1,0]. It does not know the original bits. The question is whether the rule can help it improve these guesses.

### Keep a score alongside each guess
We can represent the receiver's confidence with a signed score. In this tutorial, a positive score supports 0 and a negative score supports 1. The farther the score is from zero, the stronger the support. A score near zero means the receiver is unsure.

Our three scores are +4, -0.2 and +3. The first and last strongly support 0. The middle score only weakly supports 1. Taking the sign of each score gives the same initial guesses [0,1,0], but now we have kept the information that the middle guess is much less convincing.

These scores are called log-likelihood ratios, or LLRs. They compare how well the observation supports 0 versus 1. You do not need their probability formula to follow this example. For now, remember what the sign and size mean. Zero is a tie; our assignments choose bit 0 in that case.

### Ask what the rule can tell the middle bit
The known rule says these three bits must contain an even number of ones. Our guesses [0,1,0] contain one 1, so they fail. This tells us something is inconsistent, but it does not name the guilty bit. The first or last bit could also be wrong.

Now focus on the middle bit and consider the other two. Both strongly suggest 0. If those two really are 0, the middle bit must be 0 as well for the group to have even parity. The rule therefore has a reason to send the middle bit evidence favoring 0.

That evidence is called a message. It is computed inside the decoder, not another signal sent by the transmitter. To advise the middle bit, the rule deliberately leaves out the middle bit's own score. Otherwise it would feed the same original clue back to that bit as though it were new evidence.

How strong should the advice be? It depends on both of the other clues. If one were weak, we should not pretend their conclusion was strong. The simple method used here takes the weaker magnitude. Between +4 and +3, that is 3. Both clues favor 0, so this rule sends the middle bit a score of +3. This approximate check calculation is called Min-Sum.

### Combine the advice with the original observation
The middle bit now has its original score of -0.2 and the rule's message of +3. We add them: -0.2 + 3 = +2.8. The result favors 0, so its new guess is 0.

We have not erased the radio observation. It is still -0.2. We have formed a separate combined score using that observation and the extra evidence from the rule. The decoder changes its estimate because the new evidence outweighs the weak original clue, not because a broken rule ordered it to flip a particular bit.

The same rule advises the first and last bits too. To advise the first bit, it sees the middle bit suggesting 1 and the last bit suggesting 0. If those guesses were right, even parity would require the first bit to be 1. But the middle clue is weak, so this advice is only -0.2. The last bit receives the same weak advice. Adding it to their strong original scores gives +3.8 and +2.8, so both still favor 0.

All three combined scores are now [+3.8, +2.8, +2.8]. Our revised guesses are [0,0,0]. There are zero ones, which is even, so the rule passes. This is the whole update: start with uncertain observations, use the other bits to form advice, combine that advice with the original clue, and check the new guesses.

### Repeat the same idea across the graph
A larger LDPC code has many overlapping rules rather than just this one. Each rule advises its connected bits. Each bit combines its original observation with the advice it receives. When sending evidence back to a particular rule, it leaves out that rule's own contribution, for the same reason we left out the destination bit earlier: do not immediately echo someone's evidence back to them.

A round of these updates is an iteration. One round may not be enough, because useful evidence can need several rounds to move through the graph. The decoder checks the syndrome after an update and continues if rules are still broken, until it reaches a chosen iteration limit.

If every rule passes, it has found a valid candidate. As we saw earlier, that is not proof that it recovered the transmitted word. Strongly misleading observations can lead to a different valid word, and some noisy cases never settle on a valid one before the limit.

For now, the important idea is the conversation: observations provide the starting clues, rules connect those clues, and messages help the bits revise their estimates. The assignments will let you build that conversation one operation at a time. The additional formulas and multi-round traces are available below when you want to look more closely; they are not another story you have to follow before this one makes sense.

<details>
<summary>Optional reference material — not part of the main story</summary>

### Bridge a noisy sample to confidence
For an intentionally simple BPSK channel, bit 0 maps to +1 and bit 1 to -1. Observation y is that symbol plus zero-mean Gaussian noise of variance sigma squared. With equal bit priors the channel score is L = 2y / sigma squared. Positive favors 0; negative favors 1; zero is a tie, chosen as 0 here.

At variance 1, y=[1.3,0.15,-0.1,-2.1,0] becomes L=[2.6,0.3,-0.2,-4.2,0], then bits [0,0,1,1,0]. Increasing variance to 4 divides the scores by four, reducing confidence without changing these signs. This is a pedagogical channel, not the full NR demapper. Assignment 4 receives scores; it does not implement the channel.

### Four arrays with different jobs
L[b] is original channel evidence and stays fixed during decoding. q[c,b] is bit-to-check evidence, excluding that check. r[c,b] is check-to-bit advice, excluding that bit. A[b] is the posterior score: L[b] plus incoming r messages. A changes as advice changes. In sparse storage q[e] and r[e] use the graph edge ID.

One check with incoming [7,-3,5,-9] must produce all outputs [3,-5,3,-3]. For each destination, omit its own input, multiply the other signs, and select their smallest magnitude. Never echo a bit its own evidence. At a bit with L=2 and incoming r=[3,-1], A=4 and outgoing q=[1,5]. The message back to the first check is 4-3=1, not 4.

### A second round can matter
Switch to a NEW three-bit chain with H=[[1,1,0],[0,1,1]] and L=[3,-1,-1]. Its four edge IDs are local to this chain, not the earlier six-bit graph. The supplied full trace below starts at hard bits 011, syndrome [1,0].

Flooding round 1 gives A=[2,1,-2], bits 001, syndrome [0,1]. One rule improved while the other broke. Round 2 gives A=[1,1,1], bits 000, syndrome [0,0]. Checks in one round all read OLD q; only after computing all r do bits form new q.

Stop when the syndrome is zero or the iteration limit is reached. Zero means code-valid, not proven correct. If 000 was sent but L=[-3,-3,-3], the initial candidate 111 is already legal for this chain and the decoder stops wrongly at iteration zero. In simulation you know the sent bits for comparison; the decoder does not.

### Why addition—and where that intuition has limits
Independent likelihood ratios multiply when combining separate observations; taking logs turns multiplication into addition. That motivates combining channel and incoming evidence. The messages in a graph with cycles are not always independent: evidence may return along a loop. Excluding the destination avoids the immediate echo, but does not magically remove every long-loop correlation. Min-Sum is an approximation, not a guarantee of truth.

For a layered schedule, update one check immediately. Remove its old r contribution from A, compute replacement r, then add the replacement back. The next layer sees this updated A. The layered assignment visual follows both layers and a nonzero-old-message case.

</details>

### Understanding check
Why should a message from a parity rule to b1 exclude b1's own incoming message?
It should provide evidence from the other connected bits. Otherwise b1's original guess is echoed back as new support, double-counting the same evidence.

### Worked visual: NEW fixture H=[[1,1,0],[0,1,1]], L=[3,-1,-1]
Fixture: flooding-chain. supplied teaching fixture; not learner output
Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.

#### Four kinds of state

| Quantity | Meaning | Shape | Initialization / lifetime |
| --- | --- | --- | --- |
| L | Original received evidence | (n,) | supplied; fixed during decoding |
| q (V→C) | Bit evidence excluding destination | (m,n), edges only nonzero | H*L; old/new buffers |
| r (C→V) | Check advice from other neighbors | (m,n), nonedges 0 | zero before update |
| A | Channel plus all current incoming advice | (n,) | L initially; changes each round |
Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.

#### New equality-chain fixture: stable local edge IDs

| Edge | Endpoints | Initial q | Round 1 r | Round 1 new q | Round 2 r |
| --- | --- | --- | --- | --- | --- |
| e0 | c0,b0 | 3 | -1 | 3 | -2 |
| e1 | c0,b1 | -1 | 3 | -2 | 3 |
| e2 | c1,b1 | -1 | -1 | 2 | -1 |
| e3 | c1,b2 | -1 | -1 | -1 | 2 |
Round 2 checks consume round 1 NEW q; no partially updated q is read in the check phase.

#### Two iterations are genuinely needed

| Stage | Posterior A | Hard bits | Syndrome | Weight |
| --- | --- | --- | --- | --- |
| Initial | [3,-1,-1] | [0,1,1] | [1,0] | 1 |
| Round 1 | [2,1,-2] | [0,0,1] | [0,1] | 1 |
| Round 2 | [1,1,1] | [0,0,0] | [0,0] | 0 |
A failed check changes identity while syndrome weight stays 1. Progress need not be monotonic.

#### Dense arrays corresponding to the edge table

| Quantity | Round 1 | Round 2 |
| --- | --- | --- |
| Old q | [[3,-1,0],[0,-1,-1]] | [[3,-2,0],[0,2,-1]] |
| New r | [[-1,3,0],[0,-1,-1]] | [[-2,3,0],[0,-1,2]] |
| New q | [[3,-2,0],[0,2,-1]] | [[3,-2,0],[0,2,-1]] |
(m,n)=(2,3). Matrix zeros remain zero in q/r. All checks update, including passing checks.

Visual specification:
```json
{
  "labels": [
    "Quantity",
    "Meaning",
    "Shape",
    "Initialization / lifetime"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Four kinds of state",
    "New equality-chain fixture: stable local edge IDs",
    "Two iterations are genuinely needed",
    "Dense arrays corresponding to the edge table"
  ],
  "expected_observation": "Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.",
  "caption": "NEW fixture H=[[1,1,0],[0,1,1]], L=[3,-1,-1]",
  "text_fallback": "Four kinds of state\nQuantity | Meaning | Shape | Initialization / lifetime\nL | Original received evidence | (n,) | supplied; fixed during decoding\nq (V→C) | Bit evidence excluding destination | (m,n), edges only nonzero | H*L; old/new buffers\nr (C→V) | Check advice from other neighbors | (m,n), nonedges 0 | zero before update\nA | Channel plus all current incoming advice | (n,) | L initially; changes each round\n\nNew equality-chain fixture: stable local edge IDs\nEdge | Endpoints | Initial q | Round 1 r | Round 1 new q | Round 2 r\ne0 | c0,b0 | 3 | -1 | 3 | -2\ne1 | c0,b1 | -1 | 3 | -2 | 3\ne2 | c1,b1 | -1 | -1 | 2 | -1\ne3 | c1,b2 | -1 | -1 | -1 | 2\n\nTwo iterations are genuinely needed\nStage | Posterior A | Hard bits | Syndrome | Weight\nInitial | [3,-1,-1] | [0,1,1] | [1,0] | 1\nRound 1 | [2,1,-2] | [0,0,1] | [0,1] | 1\nRound 2 | [1,1,1] | [0,0,0] | [0,0] | 0\n\nDense arrays corresponding to the edge table\nQuantity | Round 1 | Round 2\nOld q | [[3,-1,0],[0,-1,-1]] | [[3,-2,0],[0,2,-1]]\nNew r | [[-1,3,0],[0,-1,-1]] | [[-2,3,0],[0,-1,2]]\nNew q | [[3,-2,0],[0,2,-1]] | [[3,-2,0],[0,2,-1]]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Assignment connections
LDPC-04: Turn signed confidence into candidate bits.
LDPC-05: Compute a rule's outgoing evidence.
LDPC-06: Combine evidence at a bit without echoing the destination.
LDPC-07: Connect the updates into one iteration.
LDPC-08: Repeat iterations with a stopping condition.
LDPC-09: Study corrections to the Min-Sum approximation.
LDPC-10: Study the remove-old/add-new invariant used by a layered schedule.
LDPC-18: Optional branch after assignment 5: compute two minima once, then reconstruct all outgoing messages.

## Theory: From these ideas to 5G hardware
Know what every assignment contributes—and what this course does not yet implement.

### Turn the decoder we understand into something we can run
We now have a picture of decoding: keep confidence scores, exchange evidence through parity rules, revise the guesses and check again. Building hardware for this process does not change its purpose. It changes how we store the values and carry out the work.

The first useful step is a small Python decoder. With a tiny graph, we can inspect every message and check whether the implementation follows the reasoning. This is why the course begins with toy examples rather than a large 5G configuration. We want a model we understand before we try to make it fast.

### Organize the connections so they are easier to handle
A real decoder has far more connections than our hand-worked example. Storing and visiting every connection individually can be expensive. The LDPC codes used for 5G shared-channel data have a repeated structure that helps organize this work.

You can think of a small connection pattern being expanded into groups of similar connections. Within a group, a cyclic shift tells us which position connects to which. Instead of writing down every address separately, we can describe the group and its shift.

The later assignments introduce this idea with small rotations and expanded toy matrices. You will see the names quasi-cyclic and lifting there. Their exact indexing rules matter when you implement them, but you do not need to memorize them in this overview. The purpose is to make a large graph easier to describe and process.

### Store the scores with a limited amount of precision
Python lets us work conveniently with floating-point scores. Hardware often stores each score in a small, fixed number of bits. That saves storage and can simplify arithmetic, but some values will need to be rounded and values outside the allowed range will need a stated handling rule.

Those changes can matter to decoding. A small negative score might round to zero and change a bit's decision. A large score might be clipped, making it less strong than it was in the floating-point model. We therefore need to check the effect on the decoder, not just confirm that the values fit in memory.

The saturation and quantization assignments are the first steps in understanding this tradeoff. A complete fixed-point decoder will need consistent rules for every stored message and intermediate result.

### Parallel work still needs its data
Once the arithmetic is clear, we can ask how much of it to do at once. A lane is one processing unit working on one item. For example, 32 lanes can process a group of up to 32 positions together. If there are 104 positions, we need three full groups and one group of eight.

But arithmetic units cannot work without their inputs. A memory bank is an independently accessible part of storage. If two lanes need different values from the same bank and that bank can serve only one read at a time, one lane must wait. Counting lanes alone therefore does not tell us how fast the decoder runs.

This is the path ahead: first get the decoding arithmetic right, then organize its connections, choose its numeric precision and plan how values reach the processing units. The current assignments teach these pieces. They are not yet a complete 5G decoder or a finished accelerator. We will need verified 5G graph data, the surrounding receiver processing and a full implementation model before making that claim.

<details>
<summary>Optional reference material — not part of the main story</summary>

### Name hardware terms before using them
Gather means reading scattered addresses into the order the computation needs. Scatter means writing contributions back to their original addresses. With a Z=4 block shift k=1, a check gathers x[(i+1) mod 4]; bit accumulation scatters its outgoing message to the same bit index. This differs from the standalone right-vector-rotation helper.

A lane is one parallel arithmetic slot. A bank is a separately accessible memory partition. A port is the number of accesses that a bank can serve per cycle. A mask disables unused lanes in a partial group. A pipeline overlaps stages from different work items; a dependency can prevent overlap. A read-after-write hazard occurs when a later operation needs a value that an earlier one has not yet stored. Group counts alone are not clock-cycle latency.

</details>

### Understanding check
Why is a correct Python syndrome function useful but insufficient to claim a working 5G hardware decoder?
It implements only a rule-validity check. A full system also needs soft-input decoding, the actual NR code structure and surrounding processing, numerical and scheduling choices, and hardware verification.

### Assignment connections
LDPC-11: Represent cyclic data movement.
LDPC-12: Expand a toy base graph into parity connections.
LDPC-13: Recognize supported NR lifting sets.
LDPC-14: Model finite signed range.
LDPC-15: Model the conversion to fixed-point codes.
LDPC-16: Plan parallel lane groups.
LDPC-17: Identify simple memory-bank conflicts.

## LDPC-01: GF(2): bits are not ordinary numbers
Return the parity of the pairwise AND of equal-length binary vectors. Ordinary addition counts; modulo two asks whether the count is odd.
A bit is a value that is either 0 or 1. A message can be represented as a sequence of bits, but noise during transmission can make the receiver guess some of them incorrectly. LDPC stands for Low Density Parity Check. An LDPC code protects a message using known relationships between its bits, which give the receiver something to check.

A parity rule checks whether a selected group of bits contains an even number of ones. Zero ones counts as even too. In an LDPC code, these rules help a receiver spot guesses that do not fit the protected message. This assignment implements just one rule, not the whole decoder.

Suppose the available bits are [1,1,1], but this rule uses only the first and last positions. We describe that selection with the mask [1,0,1]. A mask entry of 1 means include the bit; 0 means ignore it. The selected values are therefore [1,1]. There are two ones, so this even-parity rule passes.

We want our function to return 0 when the count is even and 1 when it is odd. XOR is the operation that computes this. For two bits, equal values XOR to 0 and different values XOR to 1. Applying XOR across a group gives the parity of the whole group. You can also think of parity as the remainder after dividing the sum by two.

AND handles the selection: a bit AND 1 keeps the bit, while a bit AND 0 gives 0. Pairwise AND of [1,1,1] and [1,0,1] gives [1,0,1]. The ignored position contributes zero, and XOR across those contributions gives 0. If either selected bit changes to 0, only one selected 1 remains and the result becomes 1. Changing the ignored middle bit has no effect.

The name GF(2) refers to arithmetic on 0 and 1, where addition is XOR and multiplication is AND. That is why this operation is called a GF(2) dot product. The two arrays must have equal lengths so matching indices refer to the same position. If both arrays are empty, there are no ones to count, so the result is 0.

## Your task
Write gf2_dot(a, b) in python/gf2.py. Return one integer parity result, 0 or 1, from two equally sized binary arrays. Return 0 for empty arrays. Inputs must have equal lengths. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- a,b: binary 1-D arrays of equal length; return Python int 0 or 1. Do not mutate inputs. Empty equal vectors return 0.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
How does parity change when one selected bit is flipped?

### Worked visual: Toy: one selected parity rule
Fixture: gf2-mask. supplied teaching fixture; not learner output
Two selected ones → even parity 0. Mask 0 ignores a bit.

#### Pairwise AND, then XOR

| Bit | Value | Mask | Selected contribution |
| --- | --- | --- | --- |
| 0 | 1 | 1 | 1 |
| 1 | 1 | 0 | 0 |
| 2 | 1 | 1 | 1 |
Two selected ones → even parity 0. Mask 0 ignores a bit.

#### XOR truth table

| a | b | a XOR b |
| --- | --- | --- |
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |
XOR asks odd/even, not the ordinary count.

#### Controlled variant: Flip selected b0

#### One selected flip

| Selected contributions | Count | Parity |
| --- | --- | --- |
| [0,0,1] | 1 | 1 |
One selected bit flip toggles parity.

#### Controlled variant: Flip ignored b1

#### Ignored flip

| Bits | Mask | Selected contributions | Parity |
| --- | --- | --- | --- |
| [1,0,1] | [1,0,1] | [1,0,1] | 0 |
An ignored bit has no effect on this rule.

Visual specification:
```json
{
  "labels": [
    "Bit",
    "Value",
    "Mask",
    "Selected contribution"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Pairwise AND, then XOR",
    "XOR truth table"
  ],
  "expected_observation": "Two selected ones → even parity 0. Mask 0 ignores a bit.",
  "caption": "Toy: one selected parity rule",
  "text_fallback": "Pairwise AND, then XOR\nBit | Value | Mask | Selected contribution\n0 | 1 | 1 | 1\n1 | 1 | 0 | 0\n2 | 1 | 1 | 1\n\nXOR truth table\na | b | a XOR b\n0 | 0 | 0\n0 | 1 | 1\n1 | 0 | 1\n1 | 1 | 0",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Flip each input bit in turn while keeping mask [1,0,1]. Predict which flips change parity, then select the matching visual experiment. Compare the same vectors with ordinary integer addition.
### Progressive hints
1. Compute pairwise products first.
2. Reduce the sum modulo two.
3. Validate the equal lengths; reduce the dot product to one binary value.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
A tree of XOR gates combines selected bits. Mask ANDs select contributions; XOR stages determine the parity output. A lane is one processing unit, not one encoded bit. Tree depth and pipeline stages are design choices; no timing is measured here.
### Misconception
XOR is not an ordinary integer sum. H[0,3]=1 selects b3; it does not require b3=1.
### Reflection
Why is counting ones alone not the final parity result?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
One selected-bit flip toggles one rule; an ignored flip cannot affect it.
Public cases: 3; prerequisite IDs: none.

## LDPC-02: Syndrome: which rules are broken?
Compute one parity result per row of H. A zero syndrome means the candidate is a valid codeword, not necessarily the original transmitted word.
A protected message is a sequence of bits chosen to satisfy some known rules. The original information is the payload; extra parity bits make the rules pass. At the receiver, noise may change our guesses, so we need to check which rules those guesses still satisfy.

A parity-check matrix, called H, records the rules. Each row is a rule and each column is a bit position. A 1 includes that position in the rule; a 0 ignores it. The rule passes when its selected bits contain an even number of ones. XOR computes this: an even count returns 0, an odd count returns 1.

We will use H=[[1,1,0,1,0,0], [0,1,1,0,1,0], [1,0,1,0,0,1]]. Name the six bit positions b0 through b5, counting from zero. The first row selects b0, b1 and b3.

Let's first construct a word that satisfies these rules. In this toy example, positions b0,b1,b2 are payload. The equations choose b3=b0 XOR b1, b4=b1 XOR b2, b5=b0 XOR b2. Payload [1,0,1] becomes [1,0,1,1,1,0]. Each parity bit makes its row even. This direct structure is not available for every arbitrary H.

The receiver knows H but not the sent payload. It estimates all six codeword bits; extracting positions 0..2 returns a payload estimate under this declared layout. Check c0: 1 XOR 0 XOR 1=0. Check c1: 0 XOR 1 XOR 1=0. Check c2: 1 XOR 1 XOR 0=0.

H has m=3 rows (rules) and n=6 columns (bits); syndrome has shape (m,), with one entry per row. Flip b1 to 1: syndrome [1,1,0], weight 2. Weight counts failed rules, not bit errors. [0,0,1,0,1,1] is another valid codeword with payload [0,0,1]; it also gives [0,0,0]. Passing parity cannot decide which was sent.

## Your task
Write syndrome(bits, h) in python/syndrome.py. Return one parity result for each row of H, in row order. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- bits: length n binary array; h: binary shape (m,n); return binary shape (m,), preserve inputs.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Before flipping b1, predict which rows select it.

### Worked visual: Toy systematic layout: payload positions 0–2
Fixture: toy-encode. supplied teaching fixture; not learner output
Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.

#### Encode payload [1,0,1]

| Step | Calculation | Result |
| --- | --- | --- |
| Payload | b0,b1,b2 | [1,0,1] |
| b3 | b0 XOR b1 | 1 |
| b4 | b1 XOR b2 | 1 |
| b5 | b0 XOR b2 | 0 |
| Codeword | payload followed by parity | [1,0,1,1,1,0] |
Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.

#### All checks on the transmitted codeword

| Check | Selected bit values | XOR | Syndrome entry |
| --- | --- | --- | --- |
| c0 | 1,0,1 | 1 XOR 0 XOR 1 | 0 |
| c1 | 0,1,1 | 0 XOR 1 XOR 1 | 0 |
| c2 | 1,1,0 | 1 XOR 1 XOR 0 | 0 |
Syndrome shape (3,), not payload shape by coincidence.

#### Flip b1

| Candidate | Syndrome | Weight |
| --- | --- | --- |
| [1,1,1,1,1,0] | [1,1,0] | 2 |
Weight counts broken checks, not necessarily bit errors.

#### A different valid word

| Codeword | Payload | Syndrome |
| --- | --- | --- |
| [1,0,1,1,1,0] | [1,0,1] | [0,0,0] |
| [0,0,1,0,1,1] | [0,0,1] | [0,0,0] |
Valid codewords can carry different data.

Visual specification:
```json
{
  "labels": [
    "Step",
    "Calculation",
    "Result"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Encode payload [1,0,1]",
    "All checks on the transmitted codeword",
    "Flip b1",
    "A different valid word"
  ],
  "expected_observation": "Parity bits were chosen to satisfy THIS matrix, not guessed by a decoder.",
  "caption": "Toy systematic layout: payload positions 0–2",
  "text_fallback": "Encode payload [1,0,1]\nStep | Calculation | Result\nPayload | b0,b1,b2 | [1,0,1]\nb3 | b0 XOR b1 | 1\nb4 | b1 XOR b2 | 1\nb5 | b0 XOR b2 | 0\nCodeword | payload followed by parity | [1,0,1,1,1,0]\n\nAll checks on the transmitted codeword\nCheck | Selected bit values | XOR | Syndrome entry\nc0 | 1,0,1 | 1 XOR 0 XOR 1 | 0\nc1 | 0,1,1 | 0 XOR 1 XOR 1 | 0\nc2 | 1,1,0 | 1 XOR 1 XOR 0 | 0\n\nFlip b1\nCandidate | Syndrome | Weight\n[1,1,1,1,1,0] | [1,1,0] | 2\n\nA different valid word\nCodeword | Payload | Syndrome\n[1,0,1,1,1,0] | [1,0,1] | [0,0,0]\n[0,0,1,0,1,1] | [0,0,1] | [0,0,0]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Before selecting the flipped view, predict c0,c1,c2 for a b1 flip. Then compare the two valid words' first three bits. Give a counterexample to “weight 2 means two wrong bits.”
### Progressive hints
1. Reuse your GF(2) dot function for a row.
2. One output belongs to each row of H.
3. Return a vector of row parities, not a real-valued sum.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
A syndrome circuit reduces each row with XOR, then OR-reduces failed results for early termination. One bit feeds several row reductions; syndrome storage is m bits, not n bits.
### Misconception
Syndrome entries are check results, not recovered payload bits.
### Reflection
Why can the syndrome be zero even when the decoded payload is wrong?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Encoding creates a legal word; checking only establishes legality under H.
Public cases: 3; prerequisite IDs: LDPC-01.

## LDPC-03: Tanner graph: store connections
Turn each row of the binary parity matrix into a list of variable indices. Ordering is ascending variable index.
A parity rule checks whether a selected group of bits has an even number of ones. We store its selection in a matrix H: rows are rules, columns are bit positions, and a 1 means a connection exists. This assignment turns that table into lists of connected bit positions, so a calculation can visit only the bits it needs.

Use H=[[1,1,0,1,0,0], [0,1,1,0,1,0], [1,0,1,0,0,1]]. Bit b0 means column 0; check c0 means row 0. An edge is one bit-to-rule connection. Later, the decoder will exchange confidence scores along these edges; the edge itself is not a transmitted bit.

A Tanner graph draws H as connections: bit nodes b0..b5, check nodes c0..c2, and one edge for each 1. Node indices name bits or checks; edge indices name connections. Number its edges row by row, from left to right: e0=(c0,b0), e1=(c0,b1), e2=(c0,b3), e3=(c1,b1), e4=(c1,b2), e5=(c1,b4), e6=(c2,b0), e7=(c2,b2), e8=(c2,b5).

Your function returns check-to-bit lists [[0,1,3], [1,2,4], [0,2,5]]. The bit-to-check table is a provided view, not an additional function TODO. A row of zeros returns an empty neighbor list under this assignment's contract, even though later decoding fixtures require check degree at least two.

This tiny matrix teaches indices, not practical sparsity or error performance. A separate large-matrix schematic would have many empty cells and a small number of connections per row; do not infer large-code behavior from nine toy edges.

## Your task
Write check_neighbors(h) in python/graph.py. Return a list of bit-index lists, one for each row of H. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- h: shape (m,n); return list of m lists of integer indices. Empty rows produce an empty list.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
How many edges leave check c0?

### Worked visual: Toy 3×6 matrix; row-major GLOBAL edge IDs
Fixture: toy-edges. supplied teaching fixture; not learner output
An edge has two endpoints and two directed messages, not a transmitted bit.

#### Global edge table

| Edge | Check | Bit | Message addresses |
| --- | --- | --- | --- |
| e0 | c0 | b0 | q[e0], r[e0] |
| e1 | c0 | b1 | q[e1], r[e1] |
| e2 | c0 | b3 | q[e2], r[e2] |
| e3 | c1 | b1 | q[e3], r[e3] |
| e4 | c1 | b2 | q[e4], r[e4] |
| e5 | c1 | b4 | q[e5], r[e5] |
| e6 | c2 | b0 | q[e6], r[e6] |
| e7 | c2 | b2 | q[e7], r[e7] |
| e8 | c2 | b5 | q[e8], r[e8] |
An edge has two endpoints and two directed messages, not a transmitted bit.

#### Bit-to-check view

| Bit | Connected checks | Global edges |
| --- | --- | --- |
| b0 | c0, c2 | e0, e6 |
| b1 | c0, c1 | e1, e3 |
| b2 | c1, c2 | e4, e7 |
| b3 | c0 | e2 |
| b4 | c1 | e5 |
| b5 | c2 | e8 |
b1 has distinct outgoing messages on e1 and e3.

Visual specification:
```json
{
  "labels": [
    "Edge",
    "Check",
    "Bit",
    "Message addresses"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Global edge table",
    "Bit-to-check view"
  ],
  "expected_observation": "An edge has two endpoints and two directed messages, not a transmitted bit.",
  "caption": "Toy 3×6 matrix; row-major GLOBAL edge IDs",
  "text_fallback": "Global edge table\nEdge | Check | Bit | Message addresses\ne0 | c0 | b0 | q[e0], r[e0]\ne1 | c0 | b1 | q[e1], r[e1]\ne2 | c0 | b3 | q[e2], r[e2]\ne3 | c1 | b1 | q[e3], r[e3]\ne4 | c1 | b2 | q[e4], r[e4]\ne5 | c1 | b4 | q[e5], r[e5]\ne6 | c2 | b0 | q[e6], r[e6]\ne7 | c2 | b2 | q[e7], r[e7]\ne8 | c2 | b5 | q[e8], r[e8]\n\nBit-to-check view\nBit | Connected checks | Global edges\nb0 | c0, c2 | e0, e6\nb1 | c0, c1 | e1, e3\nb2 | c1, c2 | e4, e7\nb3 | c0 | e2\nb4 | c1 | e5\nb5 | c2 | e8",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Select e3. Locate H[1,1], b1, c1, and q[e3]/r[e3]. Then select e1 and explain why the bit endpoint is unchanged but the message address differs.
### Progressive hints
1. Look for ones in each row.
2. Return indices, not the selected values.
3. Use a stable increasing index order.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Store endpoints or adjacency lists rather than every zero. One q and one r per edge is edge-only storage; our dense arrays reserve padding for nonedges to make early code easier to inspect.

b1 has neighbors c0,c1. It has separate outgoing messages on e1 and e3 because each destination must be excluded separately. q[e1] is b1→c0; r[e1] is c0→b1. A dense representation stores them at q[0,1],r[0,1]; an edge-only representation stores them at indices 1. State the representation before indexing.
### Misconception
An edge is not an extra transmitted bit. A local e0 in a NEW fixture need not refer to this graph's e0.
### Reflection
Why does an edge list save storage but require careful indexing?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
A matrix 1, graph edge and message address must identify the same connection.
Public cases: 2; prerequisite IDs: LDPC-02.

## LDPC-04: Soft bits: hard decisions from LLRs
Use LLR = log(P(bit 0)/P(bit 1)). Positive favors zero, negative favors one. Exactly zero chooses zero in this course.
A radio receiver measures a noisy signal and estimates which bits were sent. It may be confident about one position and unsure about another. Instead of keeping only a guessed bit, it can keep a signed confidence score called a log-likelihood ratio, or LLR.

In this course, positive scores favor bit 0 and negative scores favor bit 1. A larger absolute value means stronger evidence. For example, +2.6 strongly favors 0, while -0.2 only weakly favors 1. Exactly zero is a tie; we choose bit 0.

Consider the input scores [2.6,0.3,-0.2,-4.2,0]. Keeping only the favored bits gives [0,0,1,1,0]. This conversion is called a hard decision: it keeps the guess but discards how confident we were.

Your input is already an array of LLRs. You do not need to model the radio channel or derive these scores. The observation-to-score table below shows where they can come from in a simple teaching channel; the probability formula is optional. Your function does not receive the transmitted bits as an answer key.

## Your task
Write hard_decisions(llrs) in python/channel.py. Return one integer bit per input confidence score, with the same array shape. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- llrs: finite 1-D real array; return binary integer array of same length. No mutation.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Which is more confident: +0.15 or -2.1?

### Worked visual: Teaching BPSK channel: 0→+1, 1→−1, equal priors
Fixture: awgn-llr. supplied teaching fixture; not learner output
The hard-decision function receives LLRs, not y or the transmitted truth.

#### Observation → score → decision (variance 1)

| Observation y | Noise variance | L=2y/variance | Hard bit |
| --- | --- | --- | --- |
| 1.3 | 1 | 2.6 | 0 |
| 0.15 | 1 | 0.3 | 0 |
| -0.1 | 1 | -0.2 | 1 |
| -2.1 | 1 | -4.2 | 1 |
| 0 | 1 | 0 | 0 |
The hard-decision function receives LLRs, not y or the transmitted truth.

#### Controlled variant: Same observations, noise variance 4

#### More assumed noise

| y | Variance | LLR | Hard bit |
| --- | --- | --- | --- |
| 1.3 | 4 | 0.65 | 0 |
| 0.15 | 4 | 0.075 | 0 |
| -0.1 | 4 | -0.05 | 1 |
| -2.1 | 4 | -1.05 | 1 |
| 0 | 4 | 0 | 0 |
Signs stay the same here; confidence magnitude falls by four. This is not an error-rate benchmark.

Visual specification:
```json
{
  "labels": [
    "Observation y",
    "Noise variance",
    "L=2y/variance",
    "Hard bit"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Observation → score → decision (variance 1)"
  ],
  "expected_observation": "The hard-decision function receives LLRs, not y or the transmitted truth.",
  "caption": "Teaching BPSK channel: 0→+1, 1→−1, equal priors",
  "text_fallback": "Observation → score → decision (variance 1)\nObservation y | Noise variance | L=2y/variance | Hard bit\n1.3 | 1 | 2.6 | 0\n0.15 | 1 | 0.3 | 0\n-0.1 | 1 | -0.2 | 1\n-2.1 | 1 | -4.2 | 1\n0 | 1 | 0 | 0",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Select variance 4 after predicting which values change sign. Record the new magnitudes. Compare y=−0.1 under variances 1 and 4; do not call this small deterministic comparison a BER measurement.
### Progressive hints
1. Decisions depend on sign.
2. Magnitude is confidence, not a decoded bit.
3. Use a strict negative comparison to implement the zero tie.
### Optional maths / reading
For equal priors and real Gaussian noise, expand the squared distances (y−1)^2 and (y+1)^2 in the density ratio. The difference divided by 2*sigma_squared is 2*y/sigma_squared. The continuous p(y|bit) values are densities, not probabilities of one exact real observation.
### Optional hardware
A demapper/channel model produces LLRs; a decoder may quantize them for storage. Hard decisions need a sign comparator plus the declared tie behavior, but discarding magnitude too early loses usable evidence.
### Misconception
An LLR is not a probability, bit value, or raw amplitude.
### Reflection
Why must the zero tie policy be fixed before comparing decoders?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
The score means evidence under a model; the hard bit keeps only its sign.
Public cases: 2; prerequisite IDs: LDPC-03.

## LDPC-05: Check-node messages: exclude the recipient
For each edge, exclude that edge; multiply signs of the others and use their minimum absolute value. Zero has positive sign but zero magnitude. Degree must be at least two.
A decoder estimates bits using noisy observations and known parity rules. An even-parity rule requires an even number of ones in its group. If one bit is uncertain, the other bits in the group can help us decide what that bit should be. This assignment computes that advice.

The input q contains one confidence score from each connected bit. Positive scores favor 0, negative scores favor 1, and a larger magnitude means stronger support. The output contains one message back to each bit. A message is another score, computed inside the decoder—not an extra bit sent over the radio.

For this example, one rule connects to four bits. Their incoming scores are q=[+7,−3,+5,−9]. We label the four connections e0 through e3, in input order.

To advise e0, exclude +7 and use [−3,+5,−9]. The other proposed bits contain two ones, so the target should favor 0 (positive sign). The weakest magnitude is 3, so uncorrected Min-Sum sends +3. The sign is parity reasoning; the magnitude is an approximation to confidence, not an exact probability.

Predict destinations e1 and e2 before opening the full table. All outputs are [+3,−5,+3,−3]. The rule sends advice to every neighbor, not only a bit whose current guess appears wrong.

Zero has positive sign and zero magnitude. [0,4,6] gives [4,0,0]: only excluding the sole zero can produce nonzero advice. [3,3,5,9] gives [3,3,3,3]. [−2,2,8] gives [2,−2,−2]. Never divide by an input to remove its sign; division fails at zero.

After the direct implementation, study the min1/min2 extension (LDPC-18, available after this checkpoint). Second minimum counts multiplicity. It reduces repeated work but must produce the same per-destination messages.

## Your task
Write check_messages(q) in python/minsum.py. Return one outgoing float score per input edge, excluding that edge from its own advice. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- q: finite 1-D float array length d >= 2; return float array (d,). Preserve input.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
What changes when two incoming magnitudes share the minimum?

### Worked visual: New star fixture: local edges e0–e3 are not the 3×6 graph IDs
Fixture: check-exclusion. supplied teaching fixture; not learner output
Sign asks what bit parity requires; minimum is an approximate confidence, not an exact probability.

#### Predict outputs to e1 and e2 before revealing

| Destination | Excluded input | Other inputs used | Outgoing r |
| --- | --- | --- | --- |
| local e0 | 7 | [-3,5,-9] | 3 |
| local e1 | -3 | [7,5,-9] | -5 |
| local e2 | 5 | [7,-3,-9] | 3 |
| local e3 | -9 | [7,-3,5] | -3 |
Sign asks what bit parity requires; minimum is an approximate confidence, not an exact probability.

#### One check advises all three bits (chapter 5 fixture)

| Destination | Excluded q | Inputs used | Advice r | L+r |
| --- | --- | --- | --- | --- |
| b0 | 4 | [-0.2,3] | -0.2 | 3.8 |
| b1 | -0.2 | [4,3] | 3 | 2.8 |
| b2 | 3 | [4,-0.2] | -0.2 | 2.8 |
All neighbors receive advice, not just the least-confident bit.

#### Controlled variant: Repeated minima [3,3,5,9]

#### Multiplicity matters

| Destination | Excluded | Others | Outgoing |
| --- | --- | --- | --- |
| local e0 | 3 | [3,5,9] | 3 |
| local e1 | 3 | [3,5,9] | 3 |
| local e2 | 5 | [3,3,9] | 3 |
| local e3 | 9 | [3,3,5] | 3 |
Excluding one minimum leaves the other minimum.

#### Controlled variant: Single zero [0,4,6]

#### Excluding the only zero

| Destination | Excluded | Others | Outgoing |
| --- | --- | --- | --- |
| local e0 | 0 | [4,6] | 4 |
| local e1 | 4 | [0,6] | 0 |
| local e2 | 6 | [0,4] | 0 |
Only the destination at the zero can receive nonzero advice.

#### Controlled variant: Signed tied minima [-2,2,8]

#### Sign exclusion and ties

| Destination | Excluded | Others | Outgoing |
| --- | --- | --- | --- |
| local e0 | -2 | [2,8] | 2 |
| local e1 | 2 | [-2,8] | -2 |
| local e2 | 8 | [-2,2] | -2 |
Sign of zero is positive; do not divide by a message to remove its sign.

Visual specification:
```json
{
  "labels": [
    "Destination",
    "Excluded input",
    "Other inputs used",
    "Outgoing r"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Predict outputs to e1 and e2 before revealing",
    "One check advises all three bits (chapter 5 fixture)"
  ],
  "expected_observation": "Sign asks what bit parity requires; minimum is an approximate confidence, not an exact probability.",
  "caption": "New star fixture: local edges e0–e3 are not the 3×6 graph IDs",
  "text_fallback": "Predict outputs to e1 and e2 before revealing\nDestination | Excluded input | Other inputs used | Outgoing r\nlocal e0 | 7 | [-3,5,-9] | 3\nlocal e1 | -3 | [7,5,-9] | -5\nlocal e2 | 5 | [7,-3,-9] | 3\nlocal e3 | -9 | [7,-3,5] | -3\n\nOne check advises all three bits (chapter 5 fixture)\nDestination | Excluded q | Inputs used | Advice r | L+r\nb0 | 4 | [-0.2,3] | -0.2 | 3.8\nb1 | -0.2 | [4,3] | 3 | 2.8\nb2 | 3 | [4,-0.2] | -0.2 | 2.8",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Select the repeated-minimum, single-zero and signed-tie cases. Predict which output can be nonzero with a zero input. Compare against the provided table AFTER recording your reasoning.
### Progressive hints
1. Construct the other-edge messages for each output.
2. Treat zero consistently; its minimum magnitude forces zero.
3. Test [3,3,5,9] before optimizing to a two-minimum network.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Min-Sum needs signs, absolute values and comparisons. A two-minimum summary stores min1,min2,argmin and negative-sign parity; serial edge traversal and a parallel comparison network are different hardware choices.
### Misconception
A passing check is not disabled; all scheduled checks supply soft advice.
### Reflection
Why would including the recipient's own message create misleading confidence?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
A check message excludes its target and summarizes the other neighbors.
Public cases: 4; prerequisite IDs: LDPC-04.

## LDPC-06: Variable-node messages: remove the destination
Compute posterior = channel LLR + sum incoming. Outgoing edge j equals posterior minus incoming[j].
A receiver has an original confidence score for a bit, but that bit may also receive advice from several parity rules. A parity rule checks whether a connected group contains an even number of ones; its advice is a score suggesting which value a bit should take. Positive scores favor 0 and negative scores favor 1.

Here you will combine the original observation with that advice, then prepare a separate reply to each rule. The combined score is often called the posterior. It answers what the bit currently believes after considering all its available evidence.

A bit has its fixed channel score L and incoming advice r from connected checks. It combines them into posterior A=L+sum(r). To send q back to a particular check, remove that check's contribution: q_to_c=A−r_from_c. The posterior is used for the bit decision; outgoing q is destination-specific evidence.

For ONE bit, channel=2 and incoming=[3,−1] from local c0,c1: A=2+3−1=4. To c0, q=4−3=1, using only channel and c1. To c1, q=4−(−1)=5, using channel and c0. The scalar channel remains fixed; new arrays are returned without changing incoming.

Why addition? Independent evidence contributes multiplicative likelihood ratios; logarithms turn that into addition. In cyclic graphs, messages can become correlated. Excluding the destination prevents immediate echoing but does NOT make every piece of evidence globally independent.

Input incoming[i] is advice from one neighboring check, not a bit index. Output outgoing[i] returns to that SAME neighbor. This local function returns (posterior scalar, outgoing array); it is not a whole-graph iteration.

## Your task
Write variable_messages(channel_llr, incoming) in python/variable.py. Return the posterior scalar and an array of outgoing scores in the same neighbor order as the incoming array. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- channel_llr: scalar; incoming: finite 1-D floats; return tuple (posterior scalar, outgoing array).
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Which value is used for the bit decision: posterior or outgoing e0?

### Worked visual: One bit, two incoming check messages
Fixture: variable-contributions. supplied teaching fixture; not learner output
Posterior includes both checks; each outgoing message excludes its own destination.

#### Combine and exclude

| Quantity | Available evidence | Value |
| --- | --- | --- |
| Channel L | Fixed radio evidence | 2 |
| r0 | Advice from check 0 | 3 |
| r1 | Advice from check 1 | -1 |
| Posterior A | L+r0+r1 | 4 |
| q to check 0 | A−r0 = L+r1 | 1 |
| q to check 1 | A−r1 = L+r0 | 5 |
Posterior includes both checks; each outgoing message excludes its own destination.

#### Controlled variant: Change only r0 from 3 to 7

#### One contribution changes

| Quantity | Original | After change |
| --- | --- | --- |
| Posterior | 4 | 8 |
| q to check 0 | 1 | 1 |
| q to check 1 | 5 | 9 |
The outgoing message TO c0 does not echo the changed c0 evidence.

Visual specification:
```json
{
  "labels": [
    "Quantity",
    "Available evidence",
    "Value"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Combine and exclude"
  ],
  "expected_observation": "Posterior includes both checks; each outgoing message excludes its own destination.",
  "caption": "One bit, two incoming check messages",
  "text_fallback": "Combine and exclude\nQuantity | Available evidence | Value\nChannel L | Fixed radio evidence | 2\nr0 | Advice from check 0 | 3\nr1 | Advice from check 1 | -1\nPosterior A | L+r0+r1 | 4\nq to check 0 | A−r0 = L+r1 | 1\nq to check 1 | A−r1 = L+r0 | 5",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Change r0 from 3 to 7 in the visual. Predict A, q_to_c0 and q_to_c1. Notice q_to_c0 stays 1, because c0's own changed advice must not echo back to c0.
### Progressive hints
1. First compute the full posterior.
2. Broadcast the scalar posterior against the incoming array.
3. Return both the posterior and extrinsic messages.
### Optional maths / reading
Independent likelihood ratios 4 and 2 combine to 8. Taking logs gives ln(4)+ln(2)=ln(8). Posterior odds are conditioned on the evidence. On graphs with cycles, messages can be correlated; the simple product argument is a local modeling intuition, not a guarantee of global independence.
### Optional hardware
Accumulate in a declared intermediate width, then form one subtract per destination. Store posterior per bit and messages per edge. Saturation can break algebraic equivalence; widths and clip points need explicit policies in a later fixed decoder.
### Misconception
Posterior and outgoing q are different quantities. Do not send the full posterior to every check.
### Reflection
How does subtracting the destination prevent feedback from reinforcing itself?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Posterior includes all connected advice; each outgoing message excludes one destination.
Public cases: 2; prerequisite IDs: LDPC-05.

## LDPC-07: One flooding iteration: freeze old messages
Compute all check messages from old v2c, then all posteriors and new v2c. Store zero at nonedges.
A decoder starts with confidence scores for the received bits. A positive score favors 0, a negative score favors 1, and a score farther from zero is stronger evidence. Parity rules connect groups of bits and require each group to contain an even number of ones. Bits and rules exchange scores to improve the guesses.

This assignment performs one complete round of that exchange. A message from a rule to a bit uses the other connected bits; a reply from a bit to a rule uses its original observation and advice from the other rules. Leaving out the recipient avoids immediately sending its own evidence back to it. To form a rule's outgoing message, multiply the signs of the other scores and use their smallest magnitude. At a bit, add its original score to all incoming rule messages. Its reply to a particular rule subtracts that rule's contribution.

Use the small graph H=[[1,1,0], [0,1,1]], L=[3,−1,−1]. Its four edges are e0=(c0,b0), e1=(c0,b1), e2=(c1,b1), e3=(c1,b2). A degree-two even-parity check requires its bits to agree; its uncorrected Min-Sum output to either bit is the other bit's q.

Four states have separate meanings: fixed channel L (n values); q (one V→C per edge); r (one C→V per edge); posterior A (n values). Initialize q from the channel score of each edge's bit, r to zero and A to L. Hard bits come from A's sign with zero→0.

For the dense teaching representation, H,q,r have shape (m,n)=(2,3). Nonedges are stored as ZERO and never used as neighbors. L,A have shape (3,). In an edge-only representation, q/r would each have four entries; the view table states which edge each entry belongs to.

A flooding round freezes all old q while checks compute a fresh r. Then bits combine L with all fresh r and form new q excluding each destination. Only after the whole check phase is complete may new q replace old q. Passing checks update too.

Round 1 gives r=[[-1,3,0], [0,-1,-1]], A=[2,1,-2], new q=[[3,-2,0], [0,2,-1]]. b1→c1 is A[1]−r[1,1]=1−(−1)=2. That new message supplies b2's next-round evidence. The edge and dense views are the same data, not different schedules.

## Your task
Write flooding_step(h, channel, v2c) in python/iteration.py. Return fresh check messages, fresh variable messages and the posterior scores for one flooding round. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- h: binary (m,n) with every check degree >=2; channel: (n,); v2c: (m,n). Return (c2v, new_v2c, posterior).
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
For the new chain H=[[1,1,0],[0,1,1]], L=[3,-1,-1], predict whether ONE flooding round makes every rule pass. Keep old q separate from new q.

### Worked visual: NEW fixture H=[[1,1,0],[0,1,1]], L=[3,-1,-1]
Fixture: flooding-chain. supplied teaching fixture; not learner output
Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.

#### Four kinds of state

| Quantity | Meaning | Shape | Initialization / lifetime |
| --- | --- | --- | --- |
| L | Original received evidence | (n,) | supplied; fixed during decoding |
| q (V→C) | Bit evidence excluding destination | (m,n), edges only nonzero | H*L; old/new buffers |
| r (C→V) | Check advice from other neighbors | (m,n), nonedges 0 | zero before update |
| A | Channel plus all current incoming advice | (n,) | L initially; changes each round |
Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.

#### New equality-chain fixture: stable local edge IDs

| Edge | Endpoints | Initial q | Round 1 r | Round 1 new q | Round 2 r |
| --- | --- | --- | --- | --- | --- |
| e0 | c0,b0 | 3 | -1 | 3 | -2 |
| e1 | c0,b1 | -1 | 3 | -2 | 3 |
| e2 | c1,b1 | -1 | -1 | 2 | -1 |
| e3 | c1,b2 | -1 | -1 | -1 | 2 |
Round 2 checks consume round 1 NEW q; no partially updated q is read in the check phase.

#### Two iterations are genuinely needed

| Stage | Posterior A | Hard bits | Syndrome | Weight |
| --- | --- | --- | --- | --- |
| Initial | [3,-1,-1] | [0,1,1] | [1,0] | 1 |
| Round 1 | [2,1,-2] | [0,0,1] | [0,1] | 1 |
| Round 2 | [1,1,1] | [0,0,0] | [0,0] | 0 |
A failed check changes identity while syndrome weight stays 1. Progress need not be monotonic.

#### Dense arrays corresponding to the edge table

| Quantity | Round 1 | Round 2 |
| --- | --- | --- |
| Old q | [[3,-1,0],[0,-1,-1]] | [[3,-2,0],[0,2,-1]] |
| New r | [[-1,3,0],[0,-1,-1]] | [[-2,3,0],[0,-1,2]] |
| New q | [[3,-2,0],[0,2,-1]] | [[3,-2,0],[0,2,-1]] |
(m,n)=(2,3). Matrix zeros remain zero in q/r. All checks update, including passing checks.

Visual specification:
```json
{
  "labels": [
    "Quantity",
    "Meaning",
    "Shape",
    "Initialization / lifetime"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Four kinds of state",
    "New equality-chain fixture: stable local edge IDs",
    "Two iterations are genuinely needed",
    "Dense arrays corresponding to the edge table"
  ],
  "expected_observation": "Dense nonedge zeros are padding, never graph connections. Edge-only arrays use one element per listed edge.",
  "caption": "NEW fixture H=[[1,1,0],[0,1,1]], L=[3,-1,-1]",
  "text_fallback": "Four kinds of state\nQuantity | Meaning | Shape | Initialization / lifetime\nL | Original received evidence | (n,) | supplied; fixed during decoding\nq (V→C) | Bit evidence excluding destination | (m,n), edges only nonzero | H*L; old/new buffers\nr (C→V) | Check advice from other neighbors | (m,n), nonedges 0 | zero before update\nA | Channel plus all current incoming advice | (n,) | L initially; changes each round\n\nNew equality-chain fixture: stable local edge IDs\nEdge | Endpoints | Initial q | Round 1 r | Round 1 new q | Round 2 r\ne0 | c0,b0 | 3 | -1 | 3 | -2\ne1 | c0,b1 | -1 | 3 | -2 | 3\ne2 | c1,b1 | -1 | -1 | 2 | -1\ne3 | c1,b2 | -1 | -1 | -1 | 2\n\nTwo iterations are genuinely needed\nStage | Posterior A | Hard bits | Syndrome | Weight\nInitial | [3,-1,-1] | [0,1,1] | [1,0] | 1\nRound 1 | [2,1,-2] | [0,0,1] | [0,1] | 1\nRound 2 | [1,1,1] | [0,0,0] | [0,0] | 0\n\nDense arrays corresponding to the edge table\nQuantity | Round 1 | Round 2\nOld q | [[3,-1,0],[0,-1,-1]] | [[3,-2,0],[0,2,-1]]\nNew r | [[-1,3,0],[0,-1,-1]] | [[-2,3,0],[0,-1,2]]\nNew q | [[3,-2,0],[0,2,-1]] | [[3,-2,0],[0,2,-1]]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Trace round 1 and then select round 2. Compare the old-q buffer read by each check. Which value carries b0's positive evidence through b1 to b2? Do not overwrite old q while processing checks.
### Progressive hints
1. Compute a separate c2v array first.
2. For a variable, select rows connected to that variable.
3. Use your variable helper, writing new v2c only after checks finish.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Old/new buffers avoid read-after-write scheduling changes. A memory cycle is one scheduled time step; a read port permits a stated number of reads per cycle. Buffering may cost storage; use a declared schedule before estimating latency.
### Misconception
Only updating failed checks, or mutating q halfway through, is not the declared flooding algorithm.
### Reflection
Which arrays are old and which are new during each phase?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Freeze old messages, calculate all check messages, then calculate new variable messages.
Public cases: 3; prerequisite IDs: LDPC-06.

## LDPC-08: Assemble a toy decoder
Initialize v2c from channel at edges. Check initial syndrome. Run flooding steps until zero syndrome or the iteration cap. Return bits, iterations used, and syndrome weight history including initial state.
A toy LDPC decoder tries to recover bits from confidence scores and a set of known even-parity rules. Positive scores favor 0, negative scores favor 1, and exactly zero chooses 0 here. A matrix H records which bits each rule includes.

After forming guesses, the decoder evaluates the rules. Their results form the syndrome: 0 means a rule passes and 1 means it fails. If any rules fail, the decoder exchanges advice between rules and bits, makes new guesses and checks again. Your task is to manage that repetition and decide when it should stop.

The starter imports small helper operations: syndrome checks the rules; hard_decisions converts scores to bits; flooding_step performs one round of message updates. Your loop will connect those operations rather than call a decoder library.

For example, the equality chain H=[[1,1,0], [0,1,1]], L=[3,−1,−1] has initial bits [0,1,1], syndrome [1,0]. After round 1: A=[2,1,−2], bits [0,0,1], syndrome [0,1]. After round 2: A=[1,1,1], bits [0,0,0], syndrome [0,0]. History is [1,1,0], updates used 2. Information needs two exchanges here; the weight does not decrease in round 1 even though the failing check changes.

Record initial syndrome weight before any update. Test initial validity; zero iterations is a legitimate parity-valid result. Otherwise update all checks, derive decisions, record weight, then test parity or the cap. max_iterations=0 performs no update. The history length is iterations+1.

Return exactly bits, iterations, syndrome_weights under the existing contract. Derive parity-valid from the final weight. Truth-correct requires comparison with sent bits held by an experimenter, NOT an input to the decoder. If sent 000 but L=[−3,−3,−3], initial 111 passes both checks and stops at zero iterations: valid but wrong. With L=[3,−1,−1] and cap 1, final 001 is still invalid: limit reached before recovery. This capped failure is not a proof that it never converges.

## Your task
Write decode_toy(h, channel, max_iterations) in python/decoder.py. Return a dictionary containing bits, iterations and syndrome_weights. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Return dict: bits array (n,), iterations int, syndrome_weights list. max_iterations >=0. Toy code only.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Compare the new chain after one versus two rounds. Can a legal initial 111 candidate reveal that simulation actually sent 000?

### Worked visual: Toy outcomes: truth belongs to the experimenter, not decoder
Fixture: decoder-outcomes. supplied teaching fixture; not learner output
A failed check changes identity while syndrome weight stays 1. Progress need not be monotonic.

#### Two iterations are genuinely needed

| Stage | Posterior A | Hard bits | Syndrome | Weight |
| --- | --- | --- | --- | --- |
| Initial | [3,-1,-1] | [0,1,1] | [1,0] | 1 |
| Round 1 | [2,1,-2] | [0,0,1] | [0,1] | 1 |
| Round 2 | [1,1,1] | [0,0,0] | [0,0] | 0 |
A failed check changes identity while syndrome weight stays 1. Progress need not be monotonic.

#### Three different outcomes

| Setup | Final bits | Updates used | History | Interpretation |
| --- | --- | --- | --- | --- |
| L=[3,-1,-1], cap=2; sent 000 | [0,0,0] | 2 | [1,1,0] | Valid and truth-correct in this experiment |
| L=[-3,-3,-3]; sent 000 | [1,1,1] | 0 | [0] | Valid but wrong: early stop cannot detect truth |
| L=[3,-1,-1], cap=1 | [0,0,1] | 1 | [1,1] | Cap reached with a failed check |
The decoder returns bits, iterations and syndrome_weights, not a truth-correct flag. Derive parity-valid from the final syndrome.

#### Controlled variant: One-round cap instead of two

#### Limit reached

| Bits | Iterations | History | Parity valid? |
| --- | --- | --- | --- |
| [0,0,1] | 1 | [1,1] | No |
A cap can stop before a fixture converges; this is not a claim it never converges.

Visual specification:
```json
{
  "labels": [
    "Stage",
    "Posterior A",
    "Hard bits",
    "Syndrome",
    "Weight"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Two iterations are genuinely needed",
    "Three different outcomes"
  ],
  "expected_observation": "A failed check changes identity while syndrome weight stays 1. Progress need not be monotonic.",
  "caption": "Toy outcomes: truth belongs to the experimenter, not decoder",
  "text_fallback": "Two iterations are genuinely needed\nStage | Posterior A | Hard bits | Syndrome | Weight\nInitial | [3,-1,-1] | [0,1,1] | [1,0] | 1\nRound 1 | [2,1,-2] | [0,0,1] | [0,1] | 1\nRound 2 | [1,1,1] | [0,0,0] | [0,0] | 0\n\nThree different outcomes\nSetup | Final bits | Updates used | History | Interpretation\nL=[3,-1,-1], cap=2; sent 000 | [0,0,0] | 2 | [1,1,0] | Valid and truth-correct in this experiment\nL=[-3,-3,-3]; sent 000 | [1,1,1] | 0 | [0] | Valid but wrong: early stop cannot detect truth\nL=[3,-1,-1], cap=1 | [0,0,1] | 1 | [1,1] | Cap reached with a failed check",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Compare caps 0,1,2 on the equality chain and record bits, updates and history. Then compare parity-valid and truth-correct for the supplied wrong-valid case. Keep transmitter truth outside the function inputs.
### Progressive hints
1. Initialize edge messages from each bit's channel LLR.
2. Record syndrome weight before the loop.
3. Return on parity success or after the maximum permitted updates.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Early-stop control needs a syndrome evaluation at declared boundaries. Worst-case work is bounded by the cap; typical work may be lower. Average iterations alone cannot establish worst-case latency or throughput.
### Misconception
A history need not decrease monotonically; zero final weight is not a truth-correct flag.
### Reflection
Why should syndrome history include the initial hard decision?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
A bounded decoder estimates a parity-valid candidate; only an experiment knows the original truth.
Public cases: 6; prerequisite IDs: LDPC-07.

## LDPC-09: Correct Min-Sum confidence
Start from uncorrected check_messages. Preserve sign; output magnitude alpha * max(abs(r)-beta,0). alpha in (0,1], beta >=0. beta=0 is NMS; alpha=1 is OMS.
A check message is advice from an even-parity rule to one of its connected bits. It uses the other bits' confidence scores, leaving out the recipient. In the Min-Sum approximation, the other scores determine the sign and their smallest magnitude determines the strength. Positive messages favor 0; negative messages favor 1.

This simple calculation is inexpensive, but it can make advice too strong. Here you will explore two ways to reduce its magnitude without changing its direction: subtract a small offset or multiply by a scale factor.

Sum-Product uses probability-model message combination (often represented with nonlinear functions); Min-Sum keeps cheaper arithmetic but may overstate magnitude. This is an algorithm approximation, not a property of H.

Our q=[7,−3,5,−9] produces raw [3,−5,3,−3]. Offset Min-Sum (OMS) uses alpha=1 and beta=1: [2,−4,2,−2]. Normalized Min-Sum (NMS) uses alpha=0.5 and beta=0: [1.5,−2.5,1.5,−1.5]. This assignment's combined experimental rule is sign*alpha*max(magnitude−beta,0); alpha=0.5,beta=1 gives [1,−2,1,−1]. Do not call the combined setting pure OMS or NMS.

Making a message weaker does not guarantee fewer decoding errors. To judge that, we would need to decode many known messages under a stated noise model and count how often recovery succeeds. Preserve signs and input arrays; clipping a magnitude at zero must not reverse its favored bit.

## Your task
Write corrected_messages(q, alpha=1.0, beta=0.0) in python/corrected.py. Return corrected check messages using the declared alpha and beta parameters. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Finite q length >=2; return array same shape. No mutation.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
What happens to magnitude 0.5 with offset 1?

### Worked visual: Same star fixture q=[7,-3,5,-9]
Fixture: correction-modes. supplied teaching fixture; not learner output
Compare one parameter at a time, not a universal best setting.

#### Isolate algorithm changes

| Mode | Parameters | Outputs |
| --- | --- | --- |
| Min-Sum | alpha=1, beta=0 | [3,-5,3,-3] |
| OMS | alpha=1, beta=1 | [2,-4,2,-2] |
| NMS | alpha=0.5, beta=0 | [1.5,-2.5,1.5,-1.5] |
Compare one parameter at a time, not a universal best setting.

#### Controlled variant: Combined experimental correction (not pure OMS/NMS)

#### Combined rule

| alpha | beta | Outputs |
| --- | --- | --- |
| 0.5 | 1 | [1,-2,1,-1] |
This supported primitive uses alpha*max(magnitude−beta,0).

#### Controlled variant: Large offset beta=5

#### Evidence can disappear

| Mode | Outputs |
| --- | --- |
| OMS | [0,0,0,0] |
Offset clips magnitude at zero; it must not reverse the sign.

Visual specification:
```json
{
  "labels": [
    "Mode",
    "Parameters",
    "Outputs"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Isolate algorithm changes"
  ],
  "expected_observation": "Compare one parameter at a time, not a universal best setting.",
  "caption": "Same star fixture q=[7,-3,5,-9]",
  "text_fallback": "Isolate algorithm changes\nMode | Parameters | Outputs\nMin-Sum | alpha=1, beta=0 | [3,-5,3,-3]\nOMS | alpha=1, beta=1 | [2,-4,2,-2]\nNMS | alpha=0.5, beta=0 | [1.5,-2.5,1.5,-1.5]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Use the three correction views and then beta=5. Vary beta with alpha fixed at 1; separately vary alpha with beta fixed at 0. Record numerical differences, not a claim of universally optimal parameters.
### Progressive hints
1. Reuse your uncorrected primitive.
2. Clip magnitude after offset at zero.
3. Keep the original sign when scaling magnitude.
### Optional maths / reading
Optional algorithm reading: Valentin Savin, Self-Corrected Min-Sum decoding of LDPC codes, arXiv:0803.1090v2, introductory comparison on page 1 and classical Min-Sum initialization/check/posterior equations on page 2. Ignore the extra self-correction rule for now: we implement classical Min-Sum, OMS and NMS, not that paper's proposed variable-message erasure method. URL: https://arxiv.org/pdf/0803.1090
### Optional hardware
An offset adds subtract-and-clamp logic; normalization adds scaling with a stated rounding policy in fixed point. The cost depends on representation and implementation, not just the mathematical name.
### Misconception
NR does not mandate these receiver correction parameters.
### Reflection
Why does a correction parameter need an experiment rather than being called a universal constant?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Compare isolated corrections first; distinguish numerical changes from coding-performance evidence.
Public cases: 3; prerequisite IDs: LDPC-08.

## LDPC-10: Layered update: remove old, add new
For this one check layer, q = posterior[indices] - old_messages; compute new check messages; replace those contributions in a copy of posterior.
A decoder combines a bit's original confidence score with advice from its parity rules. Positive scores favor 0, negative scores favor 1, and each rule requires an even number of ones among its connected bits. The combined score, or posterior, tells us what the bit currently believes. We call it A, the original observation L, the rule's advice r, and the score sent back to a rule q. To compute new advice, use the other connected bits' signs and their smallest score magnitude; this is the Min-Sum check update.

A rule's advice may need to be recalculated as other bits change their beliefs. When replacing that advice, we must first remove its old contribution from the combined score. Otherwise the same rule gets counted twice. This assignment follows that replacement for one group of bits.

Call a selected group of check updates a layer; here each row is one layer. Layered decoding replaces that layer's stored messages immediately. Its later layer may read the new posterior, unlike flooding.

Use H=[[1,1,0], [0,1,1]], whose two rules require neighboring bits to agree. Start it with A=L=[3,−1,−1] and old r=0. c0 on bits [0,1] reads q=[3,−1], emits r=[−1,3], and writes A=[2,2,−1]. c1 on bits [1,2] now reads q=[2,−1] (b1 is NEW), emits [−1,2], and writes A=[2,1,1]. A full layered iteration here is a sweep c0 THEN c1; syndrome is checked after that sweep. This faster propagation is specific to this fixture, not a universal latency guarantee.

For nonzero stored messages, first remove old contributions: A=[5,1,4], indices=[0,1], old r=[2,−1]. Extrinsic q=[3,2]. New r=[2,3]. Replace selected posterior values with q+new r to obtain [5,5,4]; untouched b2 remains 4. Adding new r directly to old A would double-count the old contribution.

Your function updates ONE layer and returns fresh arrays. It does not implement the full layered decoder or decide the global stopping rule. Indices refer to posterior bit positions; old_messages aligns one-to-one with those selected positions.

## Your task
Write layer_update(posterior, old_messages, indices) in python/layered.py. Return the updated posterior array and replacement messages for one layer. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- indices: unique ascending indices, degree >=2; old_messages: same length. Return (new_posterior, new_messages).
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Start A=[3,-1,-1] with zero stored r. After updating c0 on bits 0,1, what input does c1 see at bit 1?

### Worked visual: Same equality chain as flooding; layer order c0 then c1
Fixture: layered-chain. supplied teaching fixture; not learner output
c1 consumes UPDATED b1=2; flooding would still use the previous q. Faster here is not universally faster.

#### Posterior timeline

| Stage | Indices | Extrinsic q | New r | Posterior A |
| --- | --- | --- | --- | --- |
| Initial | — | — | all zero | [3,-1,-1] |
| c0 | [0,1] | [3,-1] | [-1,3] | [2,2,-1] |
| c1 | [1,2] | [2,-1] | [-1,2] | [2,1,1] |
c1 consumes UPDATED b1=2; flooding would still use the previous q. Faster here is not universally faster.

#### Nonzero stored contribution replacement

| Operation | Values |
| --- | --- |
| Old A | [5,1,4] |
| Selected indices | [0,1] |
| Old r | [2,-1] |
| q=A[selected]−old r | [3,2] |
| New r | [2,3] |
| Replace A=q+new r | [5,5,4] |
Do not add the new r to A without removing the old r.

Visual specification:
```json
{
  "labels": [
    "Stage",
    "Indices",
    "Extrinsic q",
    "New r",
    "Posterior A"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Posterior timeline",
    "Nonzero stored contribution replacement"
  ],
  "expected_observation": "c1 consumes UPDATED b1=2; flooding would still use the previous q. Faster here is not universally faster.",
  "caption": "Same equality chain as flooding; layer order c0 then c1",
  "text_fallback": "Posterior timeline\nStage | Indices | Extrinsic q | New r | Posterior A\nInitial | — | — | all zero | [3,-1,-1]\nc0 | [0,1] | [3,-1] | [-1,3] | [2,2,-1]\nc1 | [1,2] | [2,-1] | [-1,2] | [2,1,1]\n\nNonzero stored contribution replacement\nOperation | Values\nOld A | [5,1,4]\nSelected indices | [0,1]\nOld r | [2,-1]\nq=A[selected]−old r | [3,2]\nNew r | [2,3]\nReplace A=q+new r | [5,5,4]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Trace c0 then c1 and identify b1's changed value read by c1. Contrast with flooding round 1. In the replacement fixture, calculate the wrong result if old r is not removed, then explain the discrepancy.
### Progressive hints
1. Extract selected posterior values and subtract stored old messages.
2. Compute new messages from that extrinsic vector.
3. Replace only selected positions; preserve the other entries.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
RAW means read-after-write: c1 needs b1 after c0 writes it. A pipeline has a latency from input to corresponding output and an initiation interval between accepted inputs; these differ. Waiting, forwarding/bypassing or reordering needs a declared correctness argument.
### Misconception
A later layer must not read a stale posterior when the declared order requires the updated value.
### Reflection
When could two layers run at once without sharing a posterior entry?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Remove the layer's old message before adding its replacement, then honor dependencies.
Public cases: 3; prerequisite IDs: LDPC-09.

## LDPC-11: QC rotation: follow the indices
Rotate right by shift modulo vector length: output[i] = input[(i-shift) mod Z]. Reject empty vectors with ValueError.
Imagine a row of values arranged in a circle. Moving every value one place to the right puts the last value at the front rather than losing it. That is a cyclic rotation.

Structured LDPC graphs use cyclic patterns to describe which bits connect to which rules. Let Z be the group's number of positions and k the requested shift. Modulo Z means taking a remainder to wrap an index back into positions 0 through Z-1. Before using these patterns, we need an exact definition of direction: rotating a list of values is not the same operation as multiplying it by a matrix whose columns were shifted right.

QC (quasi-cyclic) groups repeat connections with modular index shifts. State what operation moves what values: a matrix block and a standalone right-vector rotation name different operations.

For Z=4 and coefficient k=1, shifting identity COLUMNS right produces rows selecting columns [1,2,3,0]. P@[a,b,c,d]=[b,c,d,a]. A right_rotate([a,b,c,d],1) helper returns [d,a,b,c]. They are inverse rotations for a column vector.

Check-side gather uses gathered[i]=bit_vector[(i+k)%Z]. To return a message for check position i to its bit endpoint, scatter to bit_vector[(i+k)%Z]. Across all i, the inverse association is i=(j−k)%Z. These rules define connections; the right-rotation helper still uses out[i]=input[(i−k)%Z]. No matrix must be stored to calculate these addresses.

Normalize signed shift modulo Z, which is one group's width, not the whole codeword length. At Z=8, right shift 3 maps [0,1,2,3,4,5,6,7] to [5,6,7,0,1,2,3,4]; shift 11 is identical. Support negative shifts and preserve dtype/shape under the contract.

## Your task
Write qc_rotate(values, shift) in python/rotation.py. Return a cyclic right rotation of the input vector, preserving its shape and dtype. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Nonempty 1-D array, integer shift (negative supported); return same shape and dtype, no mutation.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Where does input index 0 appear after right shift 3?

### Worked visual: Columns of identity shift right; vector helper rotates right
Fixture: rotation-directions. supplied teaching fixture; not learner output
Name the operation AND indexing; a right-shifted matrix does not right-rotate a column vector.

#### Z=4, shift=1: different operations

| Operation | Index rule | Actual output |
| --- | --- | --- |
| P @ [a,b,c,d] | gather[i]=x[(i+1)%4] | [b,c,d,a] |
| right_rotate(x,1) | out[i]=x[(i−1)%4] | [d,a,b,c] |
| Scatter check message back | bit[(i+1)%4] += message[i] | inverse address association |
Name the operation AND indexing; a right-shifted matrix does not right-rotate a column vector.

#### Z=8, shift=3

| Input | Right-rotated output |
| --- | --- |
| [0,1,2,3,4,5,6,7] | [5,6,7,0,1,2,3,4] |
Shift 11 gives the same output because 11 mod 8=3.

Visual specification:
```json
{
  "labels": [
    "Operation",
    "Index rule",
    "Actual output"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Z=4, shift=1: different operations",
    "Z=8, shift=3"
  ],
  "expected_observation": "Name the operation AND indexing; a right-shifted matrix does not right-rotate a column vector.",
  "caption": "Columns of identity shift right; vector helper rotates right",
  "text_fallback": "Z=4, shift=1: different operations\nOperation | Index rule | Actual output\nP @ [a,b,c,d] | gather[i]=x[(i+1)%4] | [b,c,d,a]\nright_rotate(x,1) | out[i]=x[(i−1)%4] | [d,a,b,c]\nScatter check message back | bit[(i+1)%4] += message[i] | inverse address association\n\nZ=8, shift=3\nInput | Right-rotated output\n[0,1,2,3,4,5,6,7] | [5,6,7,0,1,2,3,4]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Try shift 1 at Z=4 and compare P@x with the right helper. Use distinct indexed values (not identical ones) so an opposite-direction bug is observable. Then select Z=2,8,32,96,192,384 in the rotation explorer; small vectors are complete and large displays are labeled slices.
### Progressive hints
1. Reduce shift modulo Z.
2. Map each output index to its source index.
3. Try shifts 0, Z, Z+1 and -1.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
An 8-position barrel shifter can combine conditional shifts 1,2,4. Address generation can replace data movement if the memory organization supports it; non-power-of-two widths need a deliberate routing or multi-cycle scheme.
### Misconception
A right-shifted identity block does not imply right rotation when multiplying a column vector.
### Reflection
Could memory address mapping replace physical movement for this operation?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Always attach an exact source-index rule to a named rotation.
Public cases: 4; prerequisite IDs: LDPC-10.

## LDPC-12: Lift a toy QC base matrix
Replace -1 by zero block; nonnegative k by identity with columns rotated right k mod Z. Set block[i,(i+k) mod Z]=1.
A parity-check matrix describes connections: each row is a rule, each column is a bit, and each 1 connects that rule to that bit. A large matrix can be cumbersome to write down. A quasi-cyclic, or QC, representation describes it using a smaller table of repeated blocks.

Let Z be each block's width. An identity block has a 1 on its diagonal and zeros elsewhere, so each row selects the column with the same index. Moving those 1s cyclically changes which column each row selects. Here you will expand the small table into its full connection matrix. The expansion makes the address rules visible, so you can check exactly which bit each rule selects.

Base entries compact repeated connections. In toy B=[[0,1,−1], [2,−1,0]], a nonnegative k means a shifted Z×Z identity block; −1 means a zero block. With Z=4, two base rows become 8 checks and three base columns become 12 bits.

For B[r,c]=k, expanded check=r*Z+i and expanded bit=c*Z+((i+k)%Z), for i=0..Z−1. For B[0,1]=1, check-to-bit pairs are (0,5),(1,6),(2,7),(3,4). One base entry generates FOUR edges, not one. −1 generates none. H has 16 ones in this fixture.

The complete 8×12 matrix is in the visual, with boundaries after columns 3 and 7. Compare its row positions with the implicit index table before coding expansion. This dense expansion is a teaching tool; production storage can keep base coefficients and calculate connections.

B is NOT BG1/BG2. The right-shifted identity convention is the same kind of construction used by the pinned standard, but that does not make this authored toy an NR configuration.

## Your task
Write expand_qc(base, z) in python/qc.py. Return the expanded binary parity-check matrix for the base table and Z. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- base: integer (r,c), entries >=-1; z positive int. Return binary array (r*z,c*z). Toy base only.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
How many ones does one nonempty Z×Z permutation block contain?

### Worked visual: Toy B=[[0,1,-1],[2,-1,0]], Z=4
Fixture: qc-full. supplied teaching fixture; not learner output
Each nonempty base entry contributes four edges; −1 contributes none. H has 16 ones.

#### Complete 8×12 H: block boundaries after bits 3 and 7

| Check | b0..b3 | block 0 | b4..b7 | block 1 | b8..b11 | block 2 |
| --- | --- | --- | --- |
| c0 | 1 0 0 0 | 0 1 0 0 | 0 0 0 0 |
| c1 | 0 1 0 0 | 0 0 1 0 | 0 0 0 0 |
| c2 | 0 0 1 0 | 0 0 0 1 | 0 0 0 0 |
| c3 | 0 0 0 1 | 1 0 0 0 | 0 0 0 0 |
| c4 | 0 0 1 0 | 0 0 0 0 | 1 0 0 0 |
| c5 | 0 0 0 1 | 0 0 0 0 | 0 1 0 0 |
| c6 | 1 0 0 0 | 0 0 0 0 | 0 0 1 0 |
| c7 | 0 1 0 0 | 0 0 0 0 | 0 0 0 1 |
Each nonempty base entry contributes four edges; −1 contributes none. H has 16 ones.

#### Select base entry B[0,1]=1

| Lifted position i | Expanded check 0*4+i | Expanded bit 1*4+(i+1)%4 |
| --- | --- | --- |
| 0 | 0 | 5 |
| 1 | 1 | 6 |
| 2 | 2 | 7 |
| 3 | 3 | 4 |
Base-row index, base-column index and lifted position select different things.

Visual specification:
```json
{
  "labels": [
    "Check",
    "b0..b3 | block 0",
    "b4..b7 | block 1",
    "b8..b11 | block 2"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Complete 8×12 H: block boundaries after bits 3 and 7",
    "Select base entry B[0,1]=1"
  ],
  "expected_observation": "Each nonempty base entry contributes four edges; −1 contributes none. H has 16 ones.",
  "caption": "Toy B=[[0,1,-1],[2,-1,0]], Z=4",
  "text_fallback": "Complete 8×12 H: block boundaries after bits 3 and 7\nCheck | b0..b3 | block 0 | b4..b7 | block 1 | b8..b11 | block 2\nc0 | 1 0 0 0 | 0 1 0 0 | 0 0 0 0\nc1 | 0 1 0 0 | 0 0 1 0 | 0 0 0 0\nc2 | 0 0 1 0 | 0 0 0 1 | 0 0 0 0\nc3 | 0 0 0 1 | 1 0 0 0 | 0 0 0 0\nc4 | 0 0 1 0 | 0 0 0 0 | 1 0 0 0\nc5 | 0 0 0 1 | 0 0 0 0 | 0 1 0 0\nc6 | 1 0 0 0 | 0 0 0 0 | 0 0 1 0\nc7 | 0 1 0 0 | 0 0 0 0 | 0 0 0 1\n\nSelect base entry B[0,1]=1\nLifted position i | Expanded check 0*4+i | Expanded bit 1*4+(i+1)%4\n0 | 0 | 5\n1 | 1 | 6\n2 | 2 | 7\n3 | 3 | 4",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Select the index mapping and locate all four ones for B[0,1]. Compare k=1 with k=5 at Z=4. Remove a nonempty block conceptually: how many edges disappear and which dimensions stay fixed?
### Progressive hints
1. Allocate the expanded shape first.
2. For each nonempty block, write exactly one one per block row.
3. Use modulo indexing for the shifted column.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Store a coefficient instead of Z² binary entries. A gather/scatter address unit then computes endpoints; it still needs bandwidth and memory layout to serve those requests.
### Misconception
A base entry's indices are not the same as an expanded edge's indices.
### Reflection
Why can we store a shift coefficient instead of Z squared binary entries?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Lifted rows and columns come from base indices plus the within-block position.
Public cases: 3; prerequisite IDs: LDPC-11.

## LDPC-13: NR lifting sizes: legal is not every integer
Return the set index 0..7 for a legal NR lifting size from provided LIFTING_SETS. Unsupported Z raises ValueError.
In a structured LDPC code, a small base graph is expanded by replacing its entries with square blocks. The width of each block is called the lifting size, Z. It tells us how many positions belong to one expanded group—not how many bits belong to the whole codeword.

For 5G NR, Z must be one of a specified set of allowed sizes. The sizes are grouped into eight sets, numbered 0 through 7. Your function identifies the set containing a requested Z, or rejects it if it is not allowed.

The provided NR table contains 51 allowed lifting sizes grouped by set index; not every integer 2..384 is legal. The lookup returns which coefficient-table set contains Z. Z=8 is set 0; Z=96 is set 1; Z=104 is set 6; Z=97 is invalid.

Once Z is selected, reduce a nonnegative shift coefficient modulo Z. Coefficient 137 at Z=32 gives effective shift 9; the range is 0..Z−1. One group contains Z positions, while a codeword contains many groups. Use complete small arrays and labeled large slices when inspecting rotations.

This function is a legal-set lookup, not base-graph selection or rate recovery. A legal Z alone does not establish a valid NR configuration. A restricted NR milestone still needs declared graph, ordering, filler/puncture treatment, rate-matching boundary and independent fixtures; those are not implemented by this lesson.

## Your task
Write lifting_set_index(z) in python/lifting.py. Return the lifting-set index containing Z; raise ValueError if Z is not allowed. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- z integer. Return Python int. Standards data: TS38.212 V17.9.0 Table 5.3.2-1.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Is 97 legal just because it lies between 2 and 384?

### Worked visual: Standard-derived lifting-set lookup only
Fixture: lifting-set. supplied teaching fixture; not learner output
A legal Z alone is not a configured NR decoder. Z=97 is illegal.

#### Legal lifting sizes and group counts

| Z | Set index | Effective shifts | Groups at P=32 | Last valid lanes |
| --- | --- | --- | --- | --- |
| 2 | 0 | 0..1 | 1 | 2 |
| 8 | 0 | 0..7 | 1 | 8 |
| 32 | 0 | 0..31 | 1 | 32 |
| 96 | 1 | 0..95 | 3 | 32 |
| 104 | 6 | 0..103 | 4 | 8 |
| 192 | 1 | 0..191 | 6 | 32 |
| 384 | 1 | 0..383 | 12 | 32 |
A legal Z alone is not a configured NR decoder. Z=97 is illegal.

Visual specification:
```json
{
  "labels": [
    "Z",
    "Set index",
    "Effective shifts",
    "Groups at P=32",
    "Last valid lanes"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Legal lifting sizes and group counts"
  ],
  "expected_observation": "A legal Z alone is not a configured NR decoder. Z=97 is illegal.",
  "caption": "Standard-derived lifting-set lookup only",
  "text_fallback": "Legal lifting sizes and group counts\nZ | Set index | Effective shifts | Groups at P=32 | Last valid lanes\n2 | 0 | 0..1 | 1 | 2\n8 | 0 | 0..7 | 1 | 8\n32 | 0 | 0..31 | 1 | 32\n96 | 1 | 0..95 | 3 | 32\n104 | 6 | 0..103 | 4 | 8\n192 | 1 | 0..191 | 6 | 32\n384 | 1 | 0..383 | 12 | 32",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Look up Z=104 then compare its four P=32 groups with Z=96's three full groups. Try Z=97 and explain why the lookup must reject it even though rotating 97 elements is mathematically possible.
### Progressive hints
1. Search each provided set.
2. The position of the containing set is the result.
3. Raise ValueError when no set contains z.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
A set index controls which coefficient data are selected. Parameter support requires more than a large address counter: configuration validation and memory/routing assumptions must match the supported path.
### Misconception
Mathematically possible vector lengths are not necessarily standardized lifting sizes.
### Reflection
How is lifting size different from total codeword length?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Legal Z is one configuration condition, not proof of NR compatibility.
Public cases: 3; prerequisite IDs: LDPC-12.

## LDPC-14: Saturation: overflow must be deliberate
Clip integer values to two's-complement signed range [-2^(w-1),2^(w-1)-1]. Width >=2. Return int64 array.
A decoder stores signed confidence scores. Positive scores support bit 0 and negative scores support bit 1. When those scores are represented by a fixed number of binary bits, there is a limit to the integers we can store. An arithmetic result may fall outside that limit.

We will handle that situation with saturation: keep an in-range value unchanged, but replace an out-of-range value with the nearest representable endpoint. This is different from allowing overflow to wrap around and potentially reverse the sign.

Signed width w permits integer codes −2^(w−1)..2^(w−1)−1. At width 4, clamp to −8..7. Clamping keeps out-of-range signs; accidental wrapping can turn a positive confidence into a negative one.

Inputs here are integer codes, not floating scores. Use a wide intermediate before clipping and preserve the input array. A most-negative stored value needs care: abs(−8)=8 does NOT fit the same signed 4-bit positive range. Our teaching policy is widened magnitude arithmetic; choose sufficient width before computing abs.

Channel L, edge q/r, posterior A and accumulators can require different widths and clipping points. Saturating A before removing an old message loses information: true A=10, old r=3 gives q=7; clipped A=7 minus old r=3 gives q=4. Do not assume algebraically equivalent float expressions remain bit-equivalent after clipping. This primitive is not a full bit-accurate decoder.

## Your task
Write saturate_signed(values, width) in python/fixed.py. Return saturated integer codes for the requested signed width. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- values: integer array representable in int64; width 2..32. Use wider intermediates, preserve input.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
What is the largest positive value in six signed bits?

### Worked visual: Implementation choice: signed 4-bit storage
Fixture: saturation-boundaries. supplied teaching fixture; not learner output
Limit wider values before narrowing to the storage type.

#### Clamp, do not wrap

| Integer | Lower bound | Upper bound | Stored |
| --- | --- | --- | --- |
| -12 | -8 | 7 | -8 |
| -8 | -8 | 7 | -8 |
| -1 | -8 | 7 | -1 |
| 0 | -8 | 7 | 0 |
| 7 | -8 | 7 | 7 |
| 11 | -8 | 7 | 7 |
Limit wider values before narrowing to the storage type.

#### Magnitude and replacement hazards

| Operation | Result | Consequence |
| --- | --- | --- |
| abs(-8) in widened arithmetic | 8 | Does not fit positive signed 4-bit range |
| True A=10, old r=3: subtract | 7 | Before clipping |
| Store clip(A)=7, then subtract old r=3 | 4 | Lost information: not algebraically equivalent |
Choose widened magnitude arithmetic. Posterior and accumulator widths need separate policies.

Visual specification:
```json
{
  "labels": [
    "Integer",
    "Lower bound",
    "Upper bound",
    "Stored"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Clamp, do not wrap",
    "Magnitude and replacement hazards"
  ],
  "expected_observation": "Limit wider values before narrowing to the storage type.",
  "caption": "Implementation choice: signed 4-bit storage",
  "text_fallback": "Clamp, do not wrap\nInteger | Lower bound | Upper bound | Stored\n-12 | -8 | 7 | -8\n-8 | -8 | 7 | -8\n-1 | -8 | 7 | -1\n0 | -8 | 7 | 0\n7 | -8 | 7 | 7\n11 | -8 | 7 | 7\n\nMagnitude and replacement hazards\nOperation | Result | Consequence\nabs(-8) in widened arithmetic | 8 | Does not fit positive signed 4-bit range\nTrue A=10, old r=3: subtract | 7 | Before clipping\nStore clip(A)=7, then subtract old r=3 | 4 | Lost information: not algebraically equivalent",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Check boundaries −9,−8,7,8. Compare clipping with four-bit wrap behavior by hand. Trace the A=10, old r=3 replacement example with and without premature clipping.
### Progressive hints
1. Derive asymmetric positive and negative limits.
2. Use a wide dtype before clipping.
3. Do not cast to a narrow integer before limiting values.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Compare before narrowing. Widen accumulators and magnitude paths explicitly, then choose storage clipping points. A saturated posterior may need a different replacement design to preserve required extrinsic information.
### Misconception
Computing abs in the narrow signed type can overflow at the most-negative value.
### Reflection
Why is saturating a posterior safer than relying on accidental NumPy overflow?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Width, intermediate arithmetic and clipping location are separate choices.
Public cases: 2; prerequisite IDs: LDPC-13.

## LDPC-15: Quantization: scale, round, clip
Return stored integer codes: values * 2^fraction_bits, round ties to even, then signed saturation. fraction_bits >=0; inputs finite.
A floating-point confidence score might be 1.25 or -0.1, but a small hardware storage field holds an integer code. To preserve fractional information, we choose a scale: for example, stored code 2 can represent real value 1 when each code step means one half.

Quantization is the process of converting the real score into that limited code. In this assignment it has three stages: scale the value, round to an integer, and clip to the range the storage width allows. Dividing the result by the scale tells us which real value was actually preserved.

To store a real score, scale by 2^fraction_bits, round ties to even, then saturate the integer code. Reconstruct by dividing that stored code by the SAME scale. Total width bounds codes; fraction_bits controls step and real range.

At width=4,fraction_bits=1, codes −8..7 represent −4..3.5 with step 0.5. Inputs [1.25,1.75,−1.25,10] scale to [2.5,3.5,−2.5,20], round to [2,4,−2,20], clip to [2,4,−2,7], reconstruct to [1,2,−1,3.5]. Notice rounding and clipping are different operations.

A first decision can diverge already at the channel quantizer: −0.1 rounds to code 0, reconstructed 0, and this course's tie chooses bit 0; the float score chose 1. By contrast, 1.25 becomes 1 but keeps bit 0. A primitive-level comparison is not a complete float-versus-fixed decoder experiment.

Return int64 codes using your saturation helper. Do not narrow before rounding/clipping. Each eventual decoder intermediate needs its own policy; these experiments do not define a whole receiver implementation.

## Your task
Write quantize_signed(values, width, fraction_bits) in python/quantize.py. Return int64 stored codes, not reconstructed floating values. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Return int64 array. Real reconstructed value = code / 2^fraction_bits. Use saturate_signed helper.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Why does 1.25 round differently from 1.75 at this scale?

### Worked visual: width=4, fraction_bits=1, ties-to-even
Fixture: quantize-pipeline. supplied teaching fixture; not learner output
Code range −8..7 means reconstructed range −4..3.5 with step 0.5.

#### Scale → round → clip → reconstruct

| Real input | Scaled ×2 | Rounded | Stored code | Reconstructed |
| --- | --- | --- | --- | --- |
| 1.25 | 2.5 | 2 | 2 | 1 |
| 1.75 | 3.5 | 4 | 4 | 2 |
| -1.25 | -2.5 | -2 | -2 | -1 |
| 10 | 20 | 20 | 7 | 3.5 |
Code range −8..7 means reconstructed range −4..3.5 with step 0.5.

#### First decision divergence at quantization

| Float score | Stored code | Reconstructed | Float bit | Fixed bit |
| --- | --- | --- | --- | --- |
| -0.1 | 0 | 0 | 1 | 0 |
| 1.25 | 2 | 1 | 0 | 0 |
Quantization changes the first decision; another value changes magnitude but not its bit. This is not a complete fixed decoder.

#### Controlled variant: Change fractional bits to 2, keep width 4

#### More precision, less range

| Real | Scaled ×4 | Rounded | Stored | Reconstructed |
| --- | --- | --- | --- | --- |
| 1.25 | 5 | 5 | 5 | 1.25 |
| 1.75 | 7 | 7 | 7 | 1.75 |
| -1.25 | -5 | -5 | -5 | -1.25 |
| 10 | 40 | 40 | 7 | 1.75 |
Reconstructed range is −2..1.75, step 0.25. More fractional bits can clip sooner.

Visual specification:
```json
{
  "labels": [
    "Real input",
    "Scaled ×2",
    "Rounded",
    "Stored code",
    "Reconstructed"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Scale → round → clip → reconstruct",
    "First decision divergence at quantization"
  ],
  "expected_observation": "Code range −8..7 means reconstructed range −4..3.5 with step 0.5.",
  "caption": "width=4, fraction_bits=1, ties-to-even",
  "text_fallback": "Scale → round → clip → reconstruct\nReal input | Scaled ×2 | Rounded | Stored code | Reconstructed\n1.25 | 2.5 | 2 | 2 | 1\n1.75 | 3.5 | 4 | 4 | 2\n-1.25 | -2.5 | -2 | -2 | -1\n10 | 20 | 20 | 7 | 3.5\n\nFirst decision divergence at quantization\nFloat score | Stored code | Reconstructed | Float bit | Fixed bit\n-0.1 | 0 | 0 | 1 | 0\n1.25 | 2 | 1 | 0 | 0",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Keep width 4 and change fraction_bits from 1 to 2 in the visual. Record range, step and the FIRST changed intermediate for the same values. Try −0.1 and 1.25 to contrast changed versus unchanged hard decisions.
### Progressive hints
1. Scale before rounding.
2. np.rint uses the chosen ties-to-even convention.
3. Apply your saturation helper to rounded wide codes.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Assign widths separately to channel, q/r, posterior and accumulators. A full decoder comparison must locate the first divergent intermediate, not just compare final bits. That complete model belongs to the later accelerator milestone.
### Misconception
More fractional bits at fixed total width reduce range; they do not improve every input.
### Reflection
What changes if the fractional-bit count increases but total width stays fixed?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Scale, round, clip and reconstruct are four explicit stages.
Public cases: 3; prerequisite IDs: LDPC-14.

## LDPC-16: 32 lanes: model work, not clock frequency
Partition z independent lifted positions into groups of at most lanes. Return groups count, valid count per group, utilization = z/(groups*lanes). Positive integers only.
A lane is one processing unit that handles one item at a time. Several lanes let us work on several positions together, but they do not automatically finish an entire decoding operation in one step. First we need to say which items go to which lanes.

Here Z is the number of positions in a lifted group of an LDPC graph, and P is the number of available lanes. Your function divides those positions into groups of at most P and reports how many lanes are useful in each group. No decoding arithmetic is required for this function.

A lane is one processing unit handling one item under a stated schedule. Here P=32 lanes process different lifted positions i for one base-edge group per issue cycle. Neighbor degree d is a SEPARATE axis: each lane reduces the d neighbor messages for its own check position.

For Z=104, four groups contain [32,32,32,8] valid positions; utilization is 104/128=81.25%. Z=32,96,192,384 need 1,3,6,12 groups. Z=352 is divisible by 32 and needs 11 full groups, unlike 104.

See the two-position/three-neighbor table: position 0 has [7,3,5] and minimum 3; position 1 has [1,9,8] and minimum 1. Do NOT reduce unrelated positions into one minimum. If lanes instead process edges of a single check, the mapping and reduction network are different.

A cycle is a scheduled time step. An issue cycle accepts one vector of up to P messages in this toy schedule. Declare enough independent bandwidth, buffering or rereads, a first pass collecting per-position signs/two minima, and a second pass emitting outputs. A nonoverlapped model has 2*d*ceil(Z/P) issue cycles BEFORE overhead: d=3,Z=104 gives 24. The full table shows every read, group and dependency. This is not measured physical timing or a universal decoder formula.

Your lane_plan function still returns GROUPS, valid lanes and utilization—not cycles. Pipeline latency (input→output delay), initiation interval (spacing between accepted inputs), memory stalls and overlapping layers require separate assumptions.

## Your task
Write lane_plan(z, lanes) in python/lanes.py. Return groups, valid lane counts and utilization, not total decoder cycles. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Return dict with groups:int, valid:list[int], utilization:float. This is a lane-issue model, not total decoder cycles.
- Never mutate input arrays; tests run in a fresh Python process.
- Public-only learning checks; complete submits rerun the same public suite.
### Prediction
Which group needs masking for Z=104 and P=32?

### Worked visual: Teaching P=32; positions are parallel, neighbors are reduced
Fixture: lane-schedule. supplied teaching fixture; not learner output
One lane processes one lifted position for one edge in an issue cycle.

#### Grouping is not latency

| Z | Groups | Valid lanes | Utilization |
| --- | --- | --- | --- |
| 32 | 1 | [32] | 1 |
| 96 | 3 | [32,32,32] | 1 |
| 104 | 4 | [32,32,32,8] | 0.8125 |
| 192 | 6 | 6×32 | 1 |
| 384 | 12 | 12×32 | 1 |
One lane processes one lifted position for one edge in an issue cycle.

#### Two axes of a check layer

| Lifted position (parallel axis) | Neighbor edge 0 | Neighbor edge 1 | Neighbor edge 2 | Minimum over NEIGHBORS |
| --- | --- | --- | --- | --- |
| 0 | 7 | 3 | 5 | 3 |
| 1 | 1 | 9 | 8 | 1 |
Never reduce different positions together. Each active lane retains its own reduction state.

#### Declared nonoverlapped schedule: degree=3, Z=104

| Issue cycle | Pass | Base edge | Group | Valid lanes | Read | Compute / write | Dependency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | reduce | 0 | 0 | 32 | q edge 0 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 2 | reduce | 0 | 1 | 32 | q edge 0 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 3 | reduce | 0 | 2 | 32 | q edge 0 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 4 | reduce | 0 | 3 | 8 | q edge 0 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 5 | reduce | 1 | 0 | 32 | q edge 1 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 6 | reduce | 1 | 1 | 32 | q edge 1 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 7 | reduce | 1 | 2 | 32 | q edge 1 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 8 | reduce | 1 | 3 | 8 | q edge 1 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 9 | reduce | 2 | 0 | 32 | q edge 2 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 10 | reduce | 2 | 1 | 32 | q edge 2 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 11 | reduce | 2 | 2 | 32 | q edge 2 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 12 | reduce | 2 | 3 | 8 | q edge 2 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit |
| 13 | emit | 0 | 0 | 32 | q edge 0 group 0 | select sign/minimum; r write | previous reductions complete before emit |
| 14 | emit | 0 | 1 | 32 | q edge 0 group 1 | select sign/minimum; r write | previous reductions complete before emit |
| 15 | emit | 0 | 2 | 32 | q edge 0 group 2 | select sign/minimum; r write | previous reductions complete before emit |
| 16 | emit | 0 | 3 | 8 | q edge 0 group 3 | select sign/minimum; r write | previous reductions complete before emit |
| 17 | emit | 1 | 0 | 32 | q edge 1 group 0 | select sign/minimum; r write | previous reductions complete before emit |
| 18 | emit | 1 | 1 | 32 | q edge 1 group 1 | select sign/minimum; r write | previous reductions complete before emit |
| 19 | emit | 1 | 2 | 32 | q edge 1 group 2 | select sign/minimum; r write | previous reductions complete before emit |
| 20 | emit | 1 | 3 | 8 | q edge 1 group 3 | select sign/minimum; r write | previous reductions complete before emit |
| 21 | emit | 2 | 0 | 32 | q edge 2 group 0 | select sign/minimum; r write | previous reductions complete before emit |
| 22 | emit | 2 | 1 | 32 | q edge 2 group 1 | select sign/minimum; r write | previous reductions complete before emit |
| 23 | emit | 2 | 2 | 32 | q edge 2 group 2 | select sign/minimum; r write | previous reductions complete before emit |
| 24 | emit | 2 | 3 | 8 | q edge 2 group 3 | select sign/minimum; r write | previous reductions complete before emit |
Assume enough independent read/write bandwidth, zero added pipeline delay and buffered/re-readable q. 24 ISSUE cycles before overhead; not measured physical latency.

Visual specification:
```json
{
  "labels": [
    "Z",
    "Groups",
    "Valid lanes",
    "Utilization"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Grouping is not latency",
    "Two axes of a check layer",
    "Declared nonoverlapped schedule: degree=3, Z=104"
  ],
  "expected_observation": "One lane processes one lifted position for one edge in an issue cycle.",
  "caption": "Teaching P=32; positions are parallel, neighbors are reduced",
  "text_fallback": "Grouping is not latency\nZ | Groups | Valid lanes | Utilization\n32 | 1 | [32] | 1\n96 | 3 | [32,32,32] | 1\n104 | 4 | [32,32,32,8] | 0.8125\n192 | 6 | 6×32 | 1\n384 | 12 | 12×32 | 1\n\nTwo axes of a check layer\nLifted position (parallel axis) | Neighbor edge 0 | Neighbor edge 1 | Neighbor edge 2 | Minimum over NEIGHBORS\n0 | 7 | 3 | 5 | 3\n1 | 1 | 9 | 8 | 1\n\nDeclared nonoverlapped schedule: degree=3, Z=104\nIssue cycle | Pass | Base edge | Group | Valid lanes | Read | Compute / write | Dependency\n1 | reduce | 0 | 0 | 32 | q edge 0 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n2 | reduce | 0 | 1 | 32 | q edge 0 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n3 | reduce | 0 | 2 | 32 | q edge 0 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n4 | reduce | 0 | 3 | 8 | q edge 0 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n5 | reduce | 1 | 0 | 32 | q edge 1 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n6 | reduce | 1 | 1 | 32 | q edge 1 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n7 | reduce | 1 | 2 | 32 | q edge 1 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n8 | reduce | 1 | 3 | 8 | q edge 1 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n9 | reduce | 2 | 0 | 32 | q edge 2 group 0 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n10 | reduce | 2 | 1 | 32 | q edge 2 group 1 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n11 | reduce | 2 | 2 | 32 | q edge 2 group 2 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n12 | reduce | 2 | 3 | 8 | q edge 2 group 3 | accumulate per-position sign/min1/min2 | previous reductions complete before emit\n13 | emit | 0 | 0 | 32 | q edge 0 group 0 | select sign/minimum; r write | previous reductions complete before emit\n14 | emit | 0 | 1 | 32 | q edge 0 group 1 | select sign/minimum; r write | previous reductions complete before emit\n15 | emit | 0 | 2 | 32 | q edge 0 group 2 | select sign/minimum; r write | previous reductions complete before emit\n16 | emit | 0 | 3 | 8 | q edge 0 group 3 | select sign/minimum; r write | previous reductions complete before emit\n17 | emit | 1 | 0 | 32 | q edge 1 group 0 | select sign/minimum; r write | previous reductions complete before emit\n18 | emit | 1 | 1 | 32 | q edge 1 group 1 | select sign/minimum; r write | previous reductions complete before emit\n19 | emit | 1 | 2 | 32 | q edge 1 group 2 | select sign/minimum; r write | previous reductions complete before emit\n20 | emit | 1 | 3 | 8 | q edge 1 group 3 | select sign/minimum; r write | previous reductions complete before emit\n21 | emit | 2 | 0 | 32 | q edge 2 group 0 | select sign/minimum; r write | previous reductions complete before emit\n22 | emit | 2 | 1 | 32 | q edge 2 group 1 | select sign/minimum; r write | previous reductions complete before emit\n23 | emit | 2 | 2 | 32 | q edge 2 group 2 | select sign/minimum; r write | previous reductions complete before emit\n24 | emit | 2 | 3 | 8 | q edge 2 group 3 | select sign/minimum; r write | previous reductions complete before emit",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Compare Z=96 with 104 at P=32. Then select the cycle trace for d=3. If one memory port cannot supply the declared vector, explain which assumption fails before using 24 as a latency estimate.
### Progressive hints
1. Compute ceiling division.
2. All but the last group are full.
3. Keep the final valid-lane count and normalize useful work by issued capacity.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Retain a sign/two-minimum summary per active lifted position across edges. Emission needs original signs plus the exclusion decision: buffer or reread q. Overlapping layers sharing posterior positions have read-after-write hazards.
### Misconception
A lane-group count does not determine decoder cycles; minima reduce neighbors, not positions.
### Reflection
What extra assumptions are required to turn a group count into a decoder cycle estimate?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Declare the parallel axis, reduction axis and memory schedule before calculating time.
Public cases: 3; prerequisite IDs: LDPC-15.

## LDPC-17: Memory banking: compute lanes can still stall
Detect conflicts in a simple single-read-port modulo-banked memory.
Parallel processing units need to read their inputs from memory. Splitting memory into banks allows different banks to serve requests at the same time. A bank is one independently accessible partition; a read port is its ability to serve a read.

In this assignment each bank has one read port, so it can serve only one request per cycle. A cycle is one step in the assumed schedule. If two requests need the same bank together, they conflict even when other banks are idle. You will detect that conflict from a list of addresses.

A bank is an independently accessible memory partition. A single-read-port bank serves one read per cycle. This teaching mapping is bank=address%4 and within_bank=floor(address/4). A logical address identifies a stored bit/message; its bank ID is not that full address.

Addresses [0,4,1] request banks [0,0,1]. Bank 0 has two distinct addresses but one read port: a conflict. One possible schedule reads addresses 0 and 1 in cycle 1, then address 4 in cycle 2. This is one conflicting bank, not two conflicting banks. Empty banks must still appear in the count array.

Now derive requests from the QC toy: base row 0, Z=4, positions i=0,1. B[0,0]=0 requests bit addresses 0,1; B[0,1]=1 requests 5,6. Banks are [0,1,1,2]: addresses 1 and 5 collide in bank 1. A possible first cycle serves 0,1,6; a second serves 5. Address and bank tables show all mappings.

Assume no broadcast for duplicate requests. Only READ ports are modeled; write ports and read/write concurrency are not specified by bank_conflicts. Return bank_ids, full counts and conflict without changing addresses. This issue-group model is not an NR memory organization or a full decoder cycle simulator.

## Your task
Write bank_conflicts(addresses, banks) in python/banking.py. Return bank_ids, per-bank counts including empty banks, and a Boolean conflict result. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- addresses: nonnegative 1-D integer array; banks positive int. Return dict bank_ids (array), counts (array length banks), conflict (bool). No mutation.
- Mapping is address % banks; conflict when any count exceeds one.
- Toy single-read-port bank model, not an NR memory layout or full cycle model.
### Prediction
With four banks, can addresses 0 and 4 be read in the same cycle?

### Worked visual: Four single-read-port banks, modulo mapping, no broadcast
Fixture: bank-service. supplied teaching fixture; not learner output
Bank 0 has two requests; a single read port serves one per cycle.

#### Requests and addresses

| Logical address | Bank = address%4 | Within-bank = floor(address/4) |
| --- | --- | --- |
| 0 | 0 | 0 |
| 4 | 0 | 1 |
| 1 | 1 | 0 |
Bank 0 has two requests; a single read port serves one per cycle.

#### Possible service schedule

| Cycle | Bank 0 | Bank 1 | Bank 2 | Bank 3 |
| --- | --- | --- | --- | --- |
| 1 | address 0 | address 1 | idle | idle |
| 2 | address 4 | idle | idle | idle |
One conflicting BANK, two requests on that bank, two service cycles.

#### QC-derived issue group: B row0, Z=4, positions i=0,1

| Base edge | i | Logical bit address | Bank | Within-bank |
| --- | --- | --- | --- | --- |
| B[0,0]=0 | 0 | 0 | 0 | 0 |
| B[0,0]=0 | 1 | 1 | 1 | 0 |
| B[0,1]=1 | 0 | 5 | 1 | 1 |
| B[0,1]=1 | 1 | 6 | 2 | 1 |
Addresses come from c*Z+((i+k)%Z); addresses 1 and 5 collide in bank 1.

#### QC-derived service schedule

| Cycle | Bank 0 | Bank 1 | Bank 2 | Bank 3 |
| --- | --- | --- | --- | --- |
| 1 | address 0 | address 1 | address 6 | idle |
| 2 | idle | address 5 | idle | idle |
Port bandwidth, not arithmetic lane count, limits this group.

#### Controlled variant: Conflict-free group [0,1,2,3]

#### Each bank reads once

| Address | Bank | Within-bank |
| --- | --- | --- |
| 0 | 0 | 0 |
| 1 | 1 | 0 |
| 2 | 2 | 0 |
| 3 | 3 | 0 |
All four reads can be issued together under the stated model.

Visual specification:
```json
{
  "labels": [
    "Logical address",
    "Bank = address%4",
    "Within-bank = floor(address/4)"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Requests and addresses",
    "Possible service schedule",
    "QC-derived issue group: B row0, Z=4, positions i=0,1",
    "QC-derived service schedule"
  ],
  "expected_observation": "Bank 0 has two requests; a single read port serves one per cycle.",
  "caption": "Four single-read-port banks, modulo mapping, no broadcast",
  "text_fallback": "Requests and addresses\nLogical address | Bank = address%4 | Within-bank = floor(address/4)\n0 | 0 | 0\n4 | 0 | 1\n1 | 1 | 0\n\nPossible service schedule\nCycle | Bank 0 | Bank 1 | Bank 2 | Bank 3\n1 | address 0 | address 1 | idle | idle\n2 | address 4 | idle | idle | idle\n\nQC-derived issue group: B row0, Z=4, positions i=0,1\nBase edge | i | Logical bit address | Bank | Within-bank\nB[0,0]=0 | 0 | 0 | 0 | 0\nB[0,0]=0 | 1 | 1 | 1 | 0\nB[0,1]=1 | 0 | 5 | 1 | 1\nB[0,1]=1 | 1 | 6 | 2 | 1\n\nQC-derived service schedule\nCycle | Bank 0 | Bank 1 | Bank 2 | Bank 3\n1 | address 0 | address 1 | address 6 | idle\n2 | idle | address 5 | idle | idle",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Compare the colliding and conflict-free groups. Explain why four arithmetic lanes cannot make one read port serve two distinct addresses in one cycle. Then locate the QC-derived collision and propose a two-cycle service table.
### Progressive hints
1. Assign each address a bank ID.
2. Count requests per bank, keeping empty banks.
3. Compare each count against the one read port available.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Extra ports, changed layout, buffering or scheduling have costs. Shared posterior writes impose additional layer dependencies; a bank-conflict count alone cannot establish throughput or memory feasibility.
### Misconception
Logical address, bank ID and within-bank address name different things.
### Reflection
Could a different layout, a second port, or staggering reads avoid the conflict?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
Count requests per declared port capacity before assuming lanes can run together.
Public cases: 3; prerequisite IDs: LDPC-16.

## LDPC-18: Min1/min2: summarize a check
Reconstruct extrinsic outputs from two minima and sign parity.
An even-parity rule advises a bit using the confidence scores of the other bits connected to it. Positive scores favor 0, negative scores favor 1. The Min-Sum check update multiplies the other signs and takes the smallest of their magnitudes. The recipient's own score is excluded.

Doing a separate search for every recipient repeats a lot of work. This assignment uses a summary of the whole group—two smallest magnitudes, the position of one minimum, and the parity of the negative signs—to reconstruct all the replies.

The optimized calculation must return the same outgoing scores as the direct calculation. We are changing how much repeated work it performs, not what each message means.

For q=[7,−3,5,−9], magnitudes=[7,3,5,9], min1=3, min2=5, argmin=1. argmin is the FIRST index of a minimum; min2 is the second-smallest value WITH MULTIPLICITY. Total negative-sign parity is 0 (two negative inputs). For each destination, remove its sign and use min2 only when excluding that selected argmin; otherwise use min1. Expected outgoing=[3,−5,3,−3].

For [3,3,5,9], min1=min2=3 and argmin=0. For [0,4,6], min1=0,min2=4,argmin=0 and outgoing=[4,0,0]. For [−2,2,8], min1=min2=2,argmin=0,negative parity=1, outgoing=[2,−2,−2]. Sign of zero is positive; never divide by q to remove a sign.

Return a dict with min1,min2,argmin,negative_parity,outgoing. q is finite float shape (d,), d≥2. Preserve inputs. The public checks examine summary AND messages so a correct-looking final vector cannot hide a broken tie policy. The TODO remains yours.

## Your task
Write check_messages_fast(q) in python/minima.py. Return min1, min2, argmin, negative_parity and outgoing in a dictionary. Leave the input arrays unchanged. The input/output requirements below give the precise contract.
### Input/output contract
- Finite 1-D float q, degree >=2. Preserve input.
- Return min1, min2 including duplicates, first-index argmin, negative_parity, and outgoing float array.
- Zero sign is positive; handle ties and degree-two checks.
### Prediction
Does excluding one of two equal minima change the minimum?

### Worked visual: Min1/min2 extension: first minimum index wins ties
Fixture: minima-summary. supplied teaching fixture; not learner output
Use min2 only when excluding the selected argmin. Zero has positive sign and zero magnitude.

#### Signed fixture summary

| q | min1 | min2 (with multiplicity) | argmin | negative parity | outgoing |
| --- | --- | --- | --- | --- | --- |
| [7,-3,5,-9] | 3 | 5 | 1 | 0 | [3,-5,3,-3] |
| [3,3,5,9] | 3 | 3 | 0 | 0 | [3,3,3,3] |
| [0,4,6] | 0 | 4 | 0 | 0 | [4,0,0] |
| [-2,2,8] | 2 | 2 | 0 | 1 | [2,-2,-2] |
Use min2 only when excluding the selected argmin. Zero has positive sign and zero magnitude.

Visual specification:
```json
{
  "labels": [
    "q",
    "min1",
    "min2 (with multiplicity)",
    "argmin",
    "negative parity",
    "outgoing"
  ],
  "view_type": "indexed tables and selectable static trace",
  "selected_element": "one view or row",
  "step_sequence": [
    "Signed fixture summary"
  ],
  "expected_observation": "Use min2 only when excluding the selected argmin. Zero has positive sign and zero magnitude.",
  "caption": "Min1/min2 extension: first minimum index wins ties",
  "text_fallback": "Signed fixture summary\nq | min1 | min2 (with multiplicity) | argmin | negative parity | outgoing\n[7,-3,5,-9] | 3 | 5 | 1 | 0 | [3,-5,3,-3]\n[3,3,5,9] | 3 | 3 | 0 | 0 | [3,3,3,3]\n[0,4,6] | 0 | 4 | 0 | 0 | [4,0,0]\n[-2,2,8] | 2 | 2 | 0 | 1 | [2,-2,-2]",
  "data_origin": "supplied teaching fixture; not learner output"
}
```

### Experiment
Predict the summary before looking at the repeated-minimum and zero rows. Compare outputs with your direct checkpoint-05 function in your own experiment; agreement alone is not the independent correctness test.
### Progressive hints
1. Separate signs and magnitudes.
2. Keep two minima including duplicates.
3. Remove recipient sign; choose min2 for the first minimum index, min1 otherwise.
### Optional maths / reading
No extra derivation is required to solve the core assignment. Trace the indexed supplied values before using vectorized notation.
### Optional hardware
Serial hardware updates two minima and an index while traversing neighbors; a parallel network compares multiple edges at once. Sign XOR, widened absolute value and output selectors serve each check position. Do not reduce different lifted positions together.
### Misconception
Second-smallest does not mean second DISTINCT value.
### Reflection
Why must min2 count repeated values?
### Completion
Run public checks, then submit the same checkpoint. Completion requires every named public case; zero checks is not passing. Explain the prediction/reflection in your own words—no keyword grading.
### Takeaway
One validated summary can generate every destination's exclusion result.
Public cases: 6; prerequisite IDs: LDPC-05.

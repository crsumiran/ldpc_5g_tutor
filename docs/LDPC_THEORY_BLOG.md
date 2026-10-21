# Understanding LDPC: the beginner story

The main reading text from the six theory chapters. Extra formulas, tables and programming references remain available in the tutor, but are omitted here to keep the story continuous.

## Chapter 1: Why do we need error correction?

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

## Chapter 2: Extra bits make mistakes recoverable

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

## Chapter 3: Parity rules, then the syndrome

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

## Chapter 4: What does LDPC actually mean?

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

## Chapter 5: How a decoder uses uncertain clues

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

## Chapter 6: From these ideas to 5G hardware

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

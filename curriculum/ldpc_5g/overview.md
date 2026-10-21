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

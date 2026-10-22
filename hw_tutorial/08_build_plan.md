# 08 · Build and verify plan

> Goal: a milestone plan for taking this from "verified rotator" to "verified
> 5G decoder", with the verification strategy for each step.

---

## Guiding principles

1. **Golden model first, RTL second.** Every RTL block gets a Python model
   that is bit-exact: same widths, same saturation, same rounding. The models
   in `model/` show the style.
2. **Compare state, not just outputs.** For the decoder, dump the L memory
   after every layer from both model and RTL and diff them. The first
   mismatching layer and column points straight at the bug. Comparing only
   decoded bits at the end tells you almost nothing.
3. **Exhaustive where it is cheap.** The rotator's input space (51 Z × all
   shifts) is small enough to test completely, as `tb_rotators.v` does.
4. **Keep "toy" and "standard" separate.** Small random QC codes are for
   debugging. Real BG1/BG2 tables are for sign-off. Label which one each test uses.

## Milestones

| # | Milestone | Deliverable | How you know it works |
|---|---|---|---|
| M0 | Environment | `./run_tests.sh` passes | `PASS: 9861 checks, 0 errors` |
| M1 | Rotator ready for production | `rot_5g` + pipeline registers + multi-frame (ch. 06 ex. 2) | Exhaustive TB extended for latency and frames |
| M2 | Base-graph data | BG1/BG2 `(row, col, V[8])` tables as files; P = V mod Z generator | Entry counts 316 / 197; spot-check rows against TS 38.212; cross-check against an independent open-source implementation (below) |
| M3 | Full-precision model | Extend `layered_qc.py` to real BG1/BG2, puncturing, variable number of layers | Decodes noiseless codewords in 1 iteration; BER curve looks sensible against published curves |
| M4 | Fixed-point model | Final W_L / W_R, saturation, offset or scaling choice | BER loss vs float model within your budget (e.g. < 0.1–0.2 dB) |
| M5 | CNU RTL | min1/min2/idx/sign reduction + R decompress | Random-vector unit test vs model, including ties and saturation extremes |
| M6 | One-layer datapath | L mem → rotator → Q → CNU → L mem, with R memory | Single layer on BG1 Z = 384 matches model memory dump |
| M7 | Full decoder | Controller, schedule, iterations, early stop | Layer-by-layer dump match across 1000s of noisy frames, all Z |
| M8 | Hazards and throughput | Overlapped phases, reordering or forwarding | Cycle count per iteration measured = model estimate |
| M9 | Implementation | Synthesis of rotator alone, then whole decoder | Area/timing report; rotator post-route timing checked (wire-dominated, ch. 04 §5) |

## Test vectors without writing an encoder

The **all-zero codeword** is valid for every linear code. A Min-Sum decoder
treats 0s and 1s symmetrically, so you can start by sending all zeros
(LLR = +big), adding Gaussian noise, and checking that the decoder returns all
zeros. This tests the whole datapath before an encoder exists. **Its blind
spot:** sign-handling bugs that happen to favour 0 go unnoticed. Add an
encoder, or random codewords from a reference implementation, before sign-off.

## Independent references for golden data

Pick at least one so that your BG tables and decoder outputs are not checked
only against your own understanding:

* **MATLAB 5G Toolbox** (`nrLDPCEncode` / `nrLDPCDecode`), if you have a licence.
* **NVIDIA Sionna** (open source, Python): includes 5G LDPC encoder/decoder.
* **AFF3CT** (open source, C++): forward-error-correction toolbox with LDPC decoders.
* **OpenAirInterface** (open source 5G stack): contains BG tables in C.

Check the version and licence of whichever you use, and record it next to the
test vectors.

## Corner cases checklist

- [ ] Z = 2 (smallest) and Z = 384 (largest); Z = 3·2^7 and Z = 15·2^4 (odd factors)
- [ ] shift = 0 and shift = Z − 1
- [ ] Punctured columns (LLR = 0 at start) and filler bits (LLR = +max)
- [ ] All-max and all-min LLRs (saturation in Q = L − R and L = Q + R)
- [ ] Ties in the min-finder (two equal minima: which idx wins must match the model)
- [ ] Iteration limit reached without convergence
- [ ] Back-to-back code blocks with different Z and BG (reconfiguration)
- [ ] Multi-frame with different shifts per frame

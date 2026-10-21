# LDPC revision delivery — 9 October 2026

Authority: `LDPC_TUTOR_DETAILED_REVISION_BRIEF.md`. This delivery implements the
Priority 0/1 foundation revision. It does **not** complete the requested NR or
hardware-accelerator course. Public contract tests are not a learning-outcome
study or a compliance certification.

## Implemented teaching changes

- Preserve all six beginner chapters and their original parity/repetition story.
  Add terminology, receiver-versus-simulation knowledge, NumPy shapes/indexing,
  legal-word distance, and construction of the six-bit toy word.
- Link the nine global edges to matrix cells, graph lines, neighbor lists and
  q/r addresses. Label the tiny matrix's unusually high density; provide a
  separately labeled sparse schematic.
- Explain BPSK sample → AWGN LLR → hard bit; show noise variance changing
  confidence. Define fixed L versus changing q, r, A and distinguish dense
  teaching storage from edge storage.
- Show every excluded-input check calculation, variable contributions and
  destination exclusion. Give a two-round flooding trace with full arrays,
  successful decoding, a wrong-but-valid result, and iteration-cap failure.
- Show two overlapping layered updates and a nonzero-old-message replacement.
  Explain why likelihood-ratio multiplication motivates log addition and why
  cycles prevent assuming all messages remain independent.
- Separate OMS, NMS and the combined experimental correction. Identify what
  Min-Sum approximates, with a focused primary-paper reading.
- Explain right-vector rotation versus block multiplication and exact
  gather/scatter indices. Render the complete 8×12 toy QC matrix with grouped
  block columns. Keep all legal lifting sets, add exploratory Z values, and
  include nonmultiple-of-32 masking.
- Show scale/round/clip/reconstruct, signed minimum-magnitude widening, and a
  subtract-old clipping counterexample. Include changed/unchanged hard decisions.
- Define hardware vocabulary, separate position and neighbor axes, and give
  a conditional 24-issue-cycle two-pass schedule (degree 3, Z=104, P=32).
  Select issue cycles to follow reads, writes, valid lanes and dependencies.
  Explain layer RAW hazards; this is not a cycle-accurate decoder or measured RTL.
- Give arbitrary and QC-derived bank addresses, within-bank addresses, declared
  single-read-port/no-broadcast assumptions and a concrete service schedule.
- Add experiments, misconception prompts, progressive hints, optional math and
  optional hardware panels, takeaways and explicit completion criteria.
- Shared authored fixtures feed the visual and tutor context. They are labeled
  as teaching data, never learner execution evidence. Reveal controls permit a
  prediction before opening worked results; complete static tables remain available.
- Add LDPC-18, min1/min2 summary and extrinsic reconstruction, with six public
  cases including repeated minima, zeros, degree two, and first-index ties.
  Target learner functions remain TODOs.

## Compatibility and evidence

Existing LDPC-01 through LDPC-17 IDs and prerequisite paths remain unchanged.
LDPC-18 is appended to avoid renumbering, but unlocks after LDPC-05. It is an
optional branch: select it explicitly after that assignment. Existing passed
checkpoints are not silently regraded. Rerun them voluntarily to see added tests.

Existing session loads add **missing** declared Python assets only, using
exclusive file creation; existing learner files are never overwritten.
Saved progress, chat and guide settings are not reset. Cache-course behavior
and its independent session remain unchanged.

Regression checks cover author-only independent baselines for all public cases,
fixture/context contracts, migration preservation/idempotence/symlink rejection,
theory behavior and existing cache/guide transport tests. Browser smoke uses a
disposable database and workspace, not the learner's session. No live model call
is required to change or test a visual.

## Final verification

Final verification on 9 October: 77 backend regression tests, 3 real Docker
sandbox smokes, two browser smokes (six-page workflow and every assignment visual),
frontend stream regression, TypeScript checking and production build passed.
The live API reports 18 checkpoints / 58 public cases / six theory pages; API
health and web HTTP 200 were checked. Providers were mocked or unconfigured;
these checks do not measure the quality of a particular live guide model.

## Priority 2 — not implemented in this delivery


Choose and document one supported BG/Z/rate-matching configuration and input
boundary. Import and independently validate standard-derived graph assets.
Teach payload/CRC/filler/full-graph/punctured/rate-matched/receiver domains;
implement supported recovery and repetition accumulation. Distinguish known
filler evidence from unknown punctured evidence. Check independent golden
fixtures, not merely local encoder/decoder agreement. Add exact phase-specific
readings and ordered milestones only after these assets are validated.

## Priority 3 — not implemented in this delivery

Build a complete bit-accurate decoder with channel, edge, posterior and widened
intermediate policies; compare float/fixed traces at their first divergence.
Run reproducible error-rate experiments and confidence intervals. Produce a
decoder-derived memory trace, port-aware schedule and lane/Z comparisons with
explicit hazards/buffering. Export golden vectors and a justified first RTL
block. Frequency, area and power require actual implementation evidence.

## Sources / reading routing

For assignments 1–3, first read theory chapters 1–4; no standard reading is a
prerequisite. For 4–10, read chapter 5 and the operation-specific worked traces.
Optional algorithm reading: Valentin Savin, *Self-Corrected Min-Sum decoding
of LDPC codes*, [arXiv:0803.1090](https://arxiv.org/pdf/0803.1090), introduction
and algorithm background (PDF pages 1–2). Identify the approximate check update;
do not add the paper's extra self-correction/erasure method to this assignment.

For 11–13, inspect [ETSI TS 138 212 V17.9.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf),
section 5.3.2 and Table 5.3.2-1 (PDF page 21). Ask: which lifting set contains Z,
and what does one shift entry replace? The supplied eight lifting sets were
checked against this pinned table on 9 October 2026. Legal Z alone does not
validate an NR configuration. Future NR readings: segmentation 5.2.2,
construction 5.3.2, and LDPC rate matching 5.4.2.

For 14–18, the core lesson states all numeric and schedule policies. These are
teaching implementation choices, not standard-mandated decoder arithmetic.

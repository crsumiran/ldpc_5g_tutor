# Build a 5G LDPC learning course: Python first, hardware accelerator next

Created: 2026-10-07.

Give this entire document to the chat that has researched 5G NR LDPC. That chat
should turn its research into a reviewable curriculum and implementation handoff,
not begin by generating a completed decoder or replacing the tutor application.

## 1. Your role and the learner's goal

You are a communications researcher, LDPC decoder engineer, hardware architect,
and hands-on curriculum designer. Use the research already available in this
conversation, verify missing details, and teach me by having **me write Python**.

I previously learned a small direct-mapped cache by implementing one block at a
time, testing it, seeing its behavior, and asking an integrated tutor questions.
Create the same kind of experience for understanding LDPC in 5G and preparing
to design a hardware accelerator.

The final learning outcome is not merely calling an LDPC library. I should be
able to explain the code structure, implement and debug decoder primitives,
assemble a working Python decoder for an explicitly supported NR configuration,
develop a bit-accurate fixed-point model, and explain how its computations and
memory accesses map to a hardware architecture.

Default to a **decoder-focused accelerator** as a working assumption, with
encoding and rate-matching context sufficient to build valid tests. Confirm
whether the learner wants a decoder, encoder, or both before finalizing the
hardware capstone. Do not let this question block the basic parity/graph lessons.

Assume I can write basic Python and have implemented the small cache course,
but may be new to coding theory, probability, LLRs, and iterative decoding.
Start from prerequisites; teach mathematical notation when first used.

## 2. Hard requirement: the cache tutor UI, NOT Jupyter

Use the existing Verilog tutor's **notebook-style web experience**:

- Left: course/checkpoint navigation and progress.
- Center: assignment brief, concepts/contract, editable Python files, execution
  results, visualizations, and reflection sections styled as notebook cells.
- Right: persistent tutor chat that sees the current contract, learner source,
  public failures, and relevant artifacts.
- Top: existing model/key controls and selected-model connection test.

Do **not** require `.ipynb`, JupyterLab, Colab, a notebook kernel, notebook magics,
or a JupyterLab extension. Here, "notebook experience" means the presentation
and learning sequence of the existing web tutor, not the Jupyter file format.
Use regular `.py` source files and deterministic runs in fresh Python processes.

The earlier plan in `notebook_tutor/IMPLEMENTATION_STRATEGY.md` targets a different
Jupyter project. Its Jupyter architecture is **not** the requirement for this
LDPC course. Do not copy its startup prompt and build the wrong interface.

The guide uses the existing isolated **OpenCode-backed tutor integration**.
OpenCode is advisory; deterministic tests decide correctness. Do not replace
this with an unrestricted coding agent or a new custom OpenRouter transport.

## 3. Inputs and references

Known local references:

- Tutor repository: `/home/ranga/opencode/tutor`.
- CS231n reference archive:
  `/home/ranga/opencode/tutor/notebook_tutor/assignment1.zip`.
- Cache course: `curriculum/cache_lab/overview.md`, `architecture.md`,
  `manifest.json`, and its starter/public test files.
- Current learning layout: `web/src/app/page.tsx`,
  `web/src/components/notebook/NotebookCell.tsx`, and the course/editor/result/
  tutor components it uses.
- OpenCode behavior: `docs/OPENCODE_GUIDE.md`, `backend/app/opencode.py`,
  `backend/app/api/labs.py`, and `backend/app/verilog/tutor.py`.
- Existing Python adapter concept: `backend/app/adapters/python_pytest.py`.

If you cannot access these files, say so. Use the summaries in this document and
ask for the relevant files only if their contents materially affect your output.
Do not pretend to have inspected inaccessible files or run experiments.

Research inputs to fill in or infer explicitly from the existing conversation:

- Chosen 3GPP TS 38.212 version/release: `<exact version and authoritative PDF>`.
- Research papers and accelerator designs already studied: `<citations>`.
- Candidate independent reference implementation: `<repo/version/license>`.
- Learner time budget: `<unknown unless provided>`.
- Target hardware: `<FPGA/ASIC/unspecified>`.
- Required NR scope: `<base graph, lifting sizes, payload/rate/RV subset>`.

One authoritative example source is
[ETSI TS 138 212 V17.9.0 / 3GPP TS 38.212](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf).
This is a starting reference, not a claim that this is the latest or required
release. Select and pin the version appropriate to the researched course.

## 4. What to borrow from the CS231n archive

The supplied archive was inspected when this prompt was prepared. It contains
`knn.ipynb`, `FullyConnectedNets.ipynb`, other worksheets, and Python modules such
as `cs231n/layers.py`, `classifiers/k_nearest_neighbor.py`, `solver.py`, and
`gradient_check.py`. Its useful teaching patterns include:

1. Detailed function docstrings: inputs, outputs, shapes, and semantics.
2. Small TODO regions surrounded by usable scaffolding.
3. Immediate sanity checks with expected values, shapes, or error ranges.
4. A simple implementation before an optimized/vectorized version.
5. Reuse of earlier primitives in later end-to-end tasks.
6. Experiments and plots that reveal behavior, not just a final score.
7. Inline questions requiring the learner to explain observations.

Transfer these patterns, **not** CIFAR data, neural-network exercises, Colab
setup, Jupyter magics, or completed CS231n solutions. Do not copy course text or
code wholesale; author original LDPC assignments and verify licenses for any
assets you reuse. The archive's AI-use guidance also reinforces that the learner
must implement the solution rather than submit an AI-completed assignment.

Analog of the CS231n numerical check: use exact syndrome checks, hand-worked
message updates, independent decoder/reference comparisons, dense-vs-sparse
equivalence, and float-vs-fixed-point comparisons where applicable. Do not force
gradient checking onto an LDPC algorithm simply because CS231n uses it.

## 5. Teaching principles

- One main new idea per checkpoint; split tasks that hide multiple new ideas.
- Teach enough theory immediately before the code that needs it.
- Ask for a prediction, then implementation, then a small observable experiment.
- Begin with tiny matrices and short traces the learner can verify by hand.
- Introduce dense representations for understanding; sparse/QC representations
  for scaling and hardware. Explain the equivalence before optimization.
- Keep runner/setup/plotting plumbing provided. Leave meaningful mathematical
  and algorithmic operations for the learner to implement.
- Provide contracts and partial algorithms, not cryptic `pass` files and not
  almost-complete solutions with one token missing.
- Start with loops when they clarify dataflow; optimize only after correctness.
- Use deterministic unit tests for pass/fail. BER/BLER plots are experiments,
  not unreliable stochastic grading gates.
- The learner writes code. The tutor explains, diagnoses, and gives progressive
  hints; it does not return a completed decoder or whole assignment solution.
- Labels must distinguish toy LDPC, a restricted NR-compatible slice, a
  standard-defined operation, and an implementation-specific decoder choice.

## 6. Scientific and standards guardrails

Your research must establish and cite, rather than assume:

1. Where LDPC applies in the selected 5G NR data-channel processing chain. Do
   not describe all 5G channel coding as LDPC.
2. The selected base graph, lifting-set/table interpretation, graph-selection
   rules, and the scope of supported configurations.
3. The distinction between full parity-check structure, encoder inputs, mother
   codeword, shortened/filler positions, punctured positions, and transmitted
   rate-matched bits. Use separate symbols/lengths and explicit index maps.
4. CRC, segmentation, lifting selection, encoding, rate matching, and receiver
   recovery roles; identify which are supplied helpers versus learner tasks.
5. What the standard defines versus decoder algorithm, schedule, normalization,
   offset, quantization, early stopping, and architecture choices.
6. Which primary papers support sum-product, min-sum variants, scheduling, and
   fixed-point/accelerator techniques. Pin sources instead of inventing details.

Keep a claim ledger with exact standard clause/table or paper page/equation.
Do not paste large standards tables into the prompt; use verified authored data
assets with provenance, hashes, permitted redistribution, and validation tests.

Do not conflate these success conditions:

- Zero syndrome: the candidate satisfies the parity checks.
- Correct payload: it matches the originally transmitted payload in a test.
- CRC acceptance: it passes the selected integrity check.

A decoder can converge to a different valid codeword. Track these separately.

Fix all conventions in an explicit convention sheet before coding:

- Bit order, matrix orientation, edge order, and circular-shift direction.
- LLR definition/sign, BPSK mapping, noise variance and SNR units.
- Hard-decision rule, including the zero-LLR tie policy.
- Variable/check message meanings and whether updates are extrinsic.
- Flooding/layered iteration definitions and when syndrome is evaluated.
- Treatment of unknown, punctured, repeated, and known filler positions.
- Floating precision; clipping, infinities/NaNs, sign of zero, and degree edge cases.
- Fixed-point format, rounding, saturation, accumulator width and update order.

Do not accept a self-consistent wrong convention merely because two learner
functions cancel the same error. Use independent fixtures and hand calculations.

## 7. Suggested learning progression — refine using your research

This is a topic scaffold, not permission to invent NR parameters or force every
topic into one session. Propose roughly 12–20 short checkpoints, grouped into
phases. Split hard steps and identify optional extensions.

### Phase A: understand a tiny LDPC code

- XOR / GF(2) parity and why ordinary real-valued matrix arithmetic is wrong here.
- Parity-check matrix, syndrome, valid codeword, and error-detection limitations.
- Tanner graph, neighbors, sparse edge indexing, and equivalent representations.
- Channel observations, hard decisions, confidence, and LLR conventions.

First exercises should not require knowledge of 3GPP tables, CRC polynomials,
or a full NR chain. Every toy example must be labeled non-NR.

### Phase B: implement iterative decoding primitives

- A single check-node update with manually computed signs and magnitudes.
- Variable-node/extrinsic message updates and exclusion of the recipient edge.
- One complete flooding iteration with a trace of every message.
- Assemble a small decoder with iteration limit and well-defined early stopping.
- Compare a teaching algorithm and the chosen practical min-sum variant;
  explain what approximation changes. Sum-product may be a small provided
  numerical baseline if implementing it distracts from the hardware goal.
- Controlled noisy experiments: successes, failures, and wrong valid codewords.

Account for repeated minimum magnitudes, zero messages, small degrees, clipping,
and numerical stability. Supply exact tests, not "the output seems plausible".

### Phase C: make it genuinely relevant to 5G NR

- QC structure, base-graph entries, lifting and modulo shifts.
- Trace one expanded check and compare dense expansion with sparse/QC traversal.
- Use a verified NR configuration and independently generated codeword/fixtures.
- Explain and implement an appropriately bounded portion of rate recovery and
  its index/LLR semantics before feeding transmitted observations to the decoder.
- Show a decoder working on the explicitly supported slice, then explain what
  remains unsupported. Do not call a toy lifted graph a standards-compliant code.

Provide trustworthy table data/encoding fixtures early enough that missing
encoder plumbing does not stop decoder learning. Decide whether full encoder,
CRC, segmentation, rate matching, and HARQ combining are required learner tasks
or provided/optional components; justify the choice.

### Phase D: turn the Python decoder into a hardware model

- Layered scheduling and the relationship between stored check messages and
  updated posterior information; compare against flooding carefully, not by
  demanding their intermediate states be identical.
- Fixed-point min-sum primitives, explicit saturation/rounding, and wider
  intermediate arithmetic. Do not rely on accidental NumPy integer overflow.
- Compare float and bit-accurate fixed-point behavior on controlled fixtures.
- Two-minimum check-node processing, sign parity, QC shifts, and sparse storage
  as hardware-oriented primitives rather than just Python optimizations.
- Model memory accesses, bank conflicts, hazards, parallel lanes, and scheduling.
- Build a logical/cycle schedule model with explicit assumptions and generate
  reproducible golden vectors for a future RTL/Chisel implementation.

A Python runtime benchmark is not hardware throughput. Label estimated cycles,
bytes accessed, operations, lane utilization, and assumed clock/bandwidth;
do not claim synthesized frequency, area, power, or timing closure.

### Capstone

Demonstrate a narrowly scoped, testable decoder design and an accelerator
architecture proposal backed by the learner's Python experiments:

- Supported standard/configuration and limitations.
- Algorithm, message precision, stopping rules, and performance experiments.
- Datapath primitives, memory layout, layer/control schedule and hazards.
- Bit-accurate golden model and vectors, expected intermediate states, reset/
  transaction conventions, and a first hardware block to implement next.

RTL implementation is a later course unless explicitly requested. Teach the
hardware reasoning now, without turning the Python tutorial into an HDL course.

## 8. Mandatory checkpoint specification

For **every** checkpoint, produce these fields, not just a title and paragraph:

1. ID, title, phase, prerequisite IDs, estimated time, difficulty.
2. Learning goal: what I should be able to explain after finishing.
3. New concepts and a concise beginner-readable explanation.
4. Source citations, identifying standard requirements vs chosen algorithm.
5. A tiny hand-worked example with intermediate values.
6. Observable requirements, including corner cases and unsupported inputs.
7. Exact function signature(s), input/output shapes, dtypes, units, mutation
   rules, indexing, and error behavior. Name provided and editable files.
8. Starter scaffolding: useful setup/partial algorithm plus clearly bounded TODOs.
9. Public tests: names, explicit small inputs, expected outputs, tolerances,
   requirement tested, and what a failure teaches.
10. Cross-check strategy independent of the learner code under test.
11. A short experiment, its deterministic seed/configuration, and displayed
    plots/tables/traces. State whether observations are probabilistic.
12. Prediction question, reflection question, and three graduated hints.
13. Common misconceptions and diagnostic evidence the guide needs to spot them.
14. Hardware connection: what this teaches about arithmetic, storage, addressing,
    control, bandwidth, precision, or parallelism. Don't force irrelevant links.
15. Completion criteria and reusable outputs for later checkpoints.

Keep normal checkpoints about 20–45 minutes as a design target; hard tasks may
take longer and should be split when they introduce independent concepts.
Allow the researcher to revise estimates based on actual scope.

### Illustrative first checkpoint, not a complete course solution

Goal: implement a syndrome function for a **toy** binary parity-check matrix.

```python
def syndrome(bits: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Return the parity-check results over GF(2).

    bits: one-dimensional binary array of length n.
    h: binary array of shape (m, n).
    return: binary array of shape (m,), without mutating either input.

    TODO: Validate the agreed input contract and compute each check's parity.
    """
    raise NotImplementedError("Implement the syndrome calculation")
```

The finalized assignment must add agreed dtypes, invalid-input behavior, a small
hand-worked matrix, public expected syndromes, an all-zero example, and a
flipped-bit example. A provided display helper can highlight violated checks.
The learner should explain why a zero syndrome alone does not prove recovery
of the transmitted word. Do not fill in the TODO in learner-facing output.

## 9. Experiments and evidence the web UI should display

Use visuals when they answer a learning question:

- Binary parity matrix / sparse graph with the relevant check highlighted.
- Edge-index table: check, variable, shift, message and update ordering.
- One-iteration message trace with expected/observed values.
- Per-iteration syndrome weight and decision changes.
- Decoded vs transmitted payload, with parity and CRC status distinguished.
- Float/fixed comparison, clipped-value counts, and first divergent update.
- BER/BLER curves with configuration, seeds, trial counts, stopping criteria,
  SNR convention, and uncertainty/sample limitations.
- Memory access schedule, bank conflicts and logical-cycle trace for the model.

Small correctness experiments should run quickly on CPU with no external
downloads. Longer Monte Carlo sweeps are explicit experiments with time/sample
budgets and cancellation; they must not block a small unit-test checkpoint.
Never grade a random BER threshold without a carefully justified deterministic
fixture. Zero observed errors in a finite simulation is not proof of zero BER.

The runner should expose named public checks and preserve artifacts such as
`trace.json`, `messages.csv`, `metrics.json`, and plot images per run. No VCD is
required for pure Python; use structured algorithm traces now and hardware
waveforms only in a future HDL stage.

## 10. Tutor-chat requirements: address my actual doubt

The guide receives the question, checkpoint contract, relevant learner code,
public test results/trace, saved-source hash, conventions, and recent scoped
chat. It must **not** receive private reference solutions or hidden test source.

It should:

1. Answer the direct question first.
2. Point to a relevant requirement, code line, public assertion, index, value,
   or iteration/layer trace when available.
3. Explain the underlying concept and suggest one small check/experiment.
4. State missing evidence or stale source honestly rather than guessing.
5. Give progressive hints, not complete drop-in implementations.

Do not reproduce the old unhelpful pattern:
"Read the contract / no evidence / concept: iterative decoding / which signal
is unclear?" for every question. Conceptual questions can be answered without
a run. Debugging questions need actual available evidence.

Include example questions and model-answer rubrics such as:

- "My syndrome is zero, why is the decoded payload wrong?"
- "Why must this update exclude the message from the destination check?"
- "The loop and vectorized versions match on one input; how can I validate them?"
- "Why does layered decoding use updated values within an iteration?"
- "The floating decoder passes; where does the fixed-point decoder diverge?"
- "The plot looks right, but why does this public test fail?"
- "Why do repeated minimum magnitudes break my two-minimum shortcut?"
- "Why are some rate-recovered positions neutral but known filler positions not?"
- "How do I know whether this shift convention is the wrong way around?"
- "Which memory dependency stops me from processing these layers in parallel?"

Rubrics must identify needed evidence and acceptable explanations, not hardcode
a diagnosis for cases where the actual run may show a different cause.

Preserve selected-model testing, live status, Stop/cancellation, scoped chat,
ephemeral key handling, explicit backup choice, actual served model, and labeled
local fallback. No model request on each keystroke, save, plot refresh, or cursor
selection. Provider limits still apply when using OpenCode.

## 11. Engineering handoff for adapting the cache tutor

Your first job is curriculum design, but make the deliverables implementable.
Specify these adaptations without silently doing them:

- Add a Python course/adapter; preserve the working cache course and learner data.
- Keep the notebook-style Next.js layout, CodeMirror editing and tutor rail.
- Use Python syntax highlighting, file tabs, save feedback, and normal `.py` files.
- Rename "Compile & elaborate" to "Check syntax/imports" for Python. Any import
  execution is inside the sandbox, not the API process.
- Actions: Check syntax, Run public tests, Run experiment, Submit/Complete,
  Explain result, Hint, Reflect. Clearly separate experiment output from grades.
- Fresh deterministic execution against immutable source snapshots; store code
  hash, course revision, parameters, seeds, dependency/image versions and artifacts.
- Use pytest or equivalent structured public reports; distinguish exceptions,
  zero collected tests, timeout, infrastructure error and assertion failures.
- Use a Python-specific result/context adapter, not Verilog-reset heuristics.
- Save/restore work and chat; unlock prerequisites without losing edits.
- Parameterize schemas/routes for Python instead of forcing the `iverilog`
  manifest or inventing fields unsupported by the current implementation.
- Isolate learner code in bounded, network-disabled execution containers. No
  host credentials, reference solutions, Docker socket, or OpenCode runtime mounts.
- Whitelist artifact downloads and bound source, logs, arrays, and run time.

Public tests are enough for the first educational slice. If proposing hidden
grading, remember that read-only private test files are still readable by Python
executing in the same container. Do not claim secrecy from mounting them read-only;
use a separate trusted grading protocol or explicitly defer private grading.

Sketch a target course package using ordinary source and authored content:

```text
curriculum/ldpc_5g/
  manifest.json
  overview.md
  conventions.md
  architecture.md
  lessons/LDPC-XX.md
  starter/ldpc/*.py
  provided/                         # approved tables, helpers, fixtures
  tests/public/test_*.py
  experiments/                      # authored bounded experiment drivers
  provenance.json
```

Private references remain outside learner-served paths. Provide a proposed
language-neutral manifest plus an explicit schema-migration note; do not claim
the existing Verilog API accepts the new manifest unchanged.

## 12. Outputs I need from this research chat

Produce these deliverables in order, as Markdown/source snippets or downloadable
files if your environment supports file creation:

### A. `LDPC_COURSE_RESEARCH_BRIEF.md`

- Learner-friendly explanation of the target and a scope/non-goals statement.
- Standard version, sources, claim ledger, convention sheet, and supported slice.
- Decoder/encoder scope assumption and choices needing approval.
- Research uncertainties, independently verified facts, and experiments not yet run.

### B. `LDPC_CURRICULUM_PLAN.md`

- Phase/checkpoint DAG and a compact table of IDs, goals, TODOs, tests, artifacts,
  prerequisites, time estimates, and hardware connections.
- Full mandatory specification for each checkpoint.
- Mark core versus optional work; give a realistic CPU-first learning route.
- State which components are learner-built versus provided, and why.

### C. `LDPC_FIRST_ASSIGNMENTS.md`

Fully author the first **two or three** small checkpoints so a coding agent can
implement them without guessing: lesson text, hand example, signatures,
unfinished starter code, executable public tests with expected outputs, display
helper contract, hints, reflection, and tutor diagnosis rubric. Verify expected
numbers if you can; otherwise label them unverified rather than asserting a run.
Do not include complete target implementations.

### D. `LDPC_TEST_AND_REFERENCE_PLAN.md`

- Independent fixtures and provenance; supported codeword/rate-recovery vectors.
- Exact vs toleranced comparisons, iteration/layer traces, numerical corner cases.
- Float/fixed-point validation and directed fault tests for common misconceptions.
- Fast checks versus longer performance experiments; reproducibility/limits.
- Reference-library version/license and how it is used without becoming a
  black-box substitute for the learner's implementation.

### E. `LDPC_TUTOR_UI_AND_IMPLEMENTATION_HANDOFF.md`

- The required cache-style, non-Jupyter UI and the Python execution adaptations.
- Source mapping, result/plot/trace contracts, run freshness, and tutor context.
- OpenCode integration reuse, useful-answer acceptance criteria and failure UX.
- Incremental implementation milestones: first two checkpoints end to end,
  then decoding primitives, verified NR slice, fixed point, accelerator model.
- Preservation/security requirements and acceptance tests for each milestone.

### F. `LDPC_ACCELERATOR_BRIDGE.md`

- Map learned primitives to candidate hardware blocks and memory structures.
- Define bit-accurate interfaces, golden vectors, hazards, scheduling assumptions,
  and estimated-resource/cycle metrics without fabricated synthesis results.
- Recommend a first small hardware block and its verification contract.
- Clearly identify remaining work before any complete 5G accelerator claim.

End with a short prompt I can give an implementation agent. It must say:
read the generated course documents, preserve the cache tutor/data, build only
the first Python vertical slice in the existing notebook-style web interface,
reuse OpenCode tutor chat, run actual verification, and report what works.

## 13. Start with this instruction

Use the 5G LDPC research already in this conversation. First summarize the
established scope and source/version choices, then produce a dependency-ordered
curriculum using this prompt. Do not restart a generic literature survey if the
necessary research is already present. Verify missing standards facts and label
uncertainty. The aim is a practical course in which I implement, observe, debug,
explain, and gradually derive an accelerator-ready model—not another long report
or an AI-written complete decoder.

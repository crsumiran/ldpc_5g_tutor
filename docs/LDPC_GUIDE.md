# LDPC Python tutor — first working release

Implemented 2026-10-07 in the existing cache-style web application, not Jupyter.

## Open it

- LDPC: http://localhost:3000/?course=ldpc-5g
- Friendly redirect: http://localhost:3000/labs/ldpc-5g
- Cache course remains at http://localhost:3000/?course=cache-lab

Use the same URLs in VS Code's embedded browser or Windows Edge/Chrome if the
WSL Firefox process is unstable. Check service health first if a page refuses
connection. Run `docker compose up -d api web` from the repository root if the
web/API containers have stopped. Build changed application code using
`docker compose build api web` before restarting those services.

## What is implemented

### Printed public-test examples and guide fix (2026-10-20)

Every LDPC public test call now prints its named inputs (including array shapes
and dtypes), expected output, and actual output or exception. This also happens
for passing checks. Run tests again to generate these details; old run artifacts
are not rewritten. The results panel automatically opens “Inputs, expected
outputs and actual results.” No printing is required in the learner's functions.

Trusted expectations live in `curriculum/ldpc_5g/public_cases.json`, independently
checked against author baselines and the existing public assertions. The runner
mounts only the active checkpoint's expectations and trace plugin, not private
implementations. To regenerate the author metadata, use
`PYTHONPATH=backend .venv/bin/python scripts/export_ldpc_public_cases.py`
(stdout only). Original assertions and grading counts are unchanged.

The guide previously discarded an otherwise useful answer whenever it contained
any function definition, even a signature. It now omits full function blocks
while preserving the explanation; signatures and empty interfaces are allowed.
An answer containing only a solution still falls back with an explicit reason.
This was checked against the stored Nemotron assignment-5 answer without making
a new provider request.

### Self-contained assignments (2026-10-10)

Each assignment now starts with its own explanation of the problem and local
terms rather than a prerequisite recap or revision note. The generic “what
changes and what stays fixed” block and repeated scope/task boilerplate were
removed. Assignment 1 explains parity, masking, AND, XOR and GF(2) in that order.
Introductions cover local notation without requiring the reader to remember an
earlier explanation. Coding prerequisites, contracts and saved work are unchanged.

### Reading-flow rewrite (2026-10-09)

All six theory chapters now read as continuous blog-style articles, not a stack
of numbered notebook cells. Chapter 5 keeps one three-bit example throughout;
formulas, the second-round trace and message-address tables live in optional
panels after the story. Visuals and assignment links are optional too. No
checkpoint contracts, learner files or saved progress were changed.
The main text is also available in `docs/LDPC_THEORY_BLOG.md`; reproduce it with
`node scripts/export_ldpc_review.mjs --theory-only` (stdout only).

### Start with theory (2026-10-08)

The LDPC course now opens with six ungraded beginner pages before the coding:

1. Why transmission errors need correction.
2. Payload, redundancy, codewords and code rate through a repetition-code toy.
3. Parity/XOR, your `gf2_dot`, and what a syndrome actually tells you.
4. Low-density connection tables, Tanner graphs and neighbor lists.
5. Soft confidence and the iterative decoding conversation.
6. How these ideas lead toward 5G structures and hardware constraints.

Each page has a worked visual, small reading sections, a revealable understanding
question, and links explaining the purpose of relevant assignments. Theory is
available even when later assignments are locked; it does not unlock or grade
them. “Resume assignments” preserves your existing work. Assignment pages have
“Read the theory behind this assignment” and “Start from the beginning” links.
Reading position is stored separately under `ldpc-theory-view-v1`; existing
session identifiers and learner files are unchanged.

The guide receives the trusted authored page when you ask from theory mode,
not old coding failures. Without a working model, it explicitly shows authored
background instead of claiming a tailored AI answer. Content is maintained in
`curriculum/ldpc_5g/theory.json`. The hardware page links the pinned ETSI standard;
toy examples remain explicitly separate from full NR decoding.

Chapter 5's big-picture panel was rewritten after learner feedback. It now
walks through five visual stages: radio clues, test the rule, other bits advise,
revise the guess, and test again. Bit cards distinguish guesses from confidence;
the advice diagram shows the two other bits feeding a rule and the rule advising
the middle bit. Signed scores are introduced only at the combine stage, and the
Min-Sum calculation is in optional expandable maths. The channel scores remain
fixed while combined scores change. The surrounding prose follows the same toy
example and separates decoder messages from transmitted radio information.

### Coding path

18 checkpoints, 58 named public checks. The original 17-step path is preserved;
LDPC-18 is an optional min1/min2 branch available after LDPC-05:

1. GF(2) dot/parity.
2. Syndrome and validity versus original payload recovery.
3. Sparse check-neighbor lists / Tanner graph.
4. LLR hard decisions and sign/zero convention.
5. Extrinsic Min-Sum check messages, repeated minima and zero.
6. Variable posterior/extrinsic messages.
7. One complete flooding iteration.
8. Bounded flooding toy decoder with syndrome history.
9. Offset / normalized Min-Sum primitive.
10. One layered remove-old/add-new update.
11. Right vector rotation with modulo indexing.
12. Toy QC block expansion and matrix/vector direction distinction.
13. Verified NR lifting-set indices.
14. Signed integer saturation.
15. Quantization with explicit scale / ties-to-even rounding / clipping.
16. Physical lane group count / utilization.
17. Single-read-port memory bank conflicts.
18. Two-minimum/sign-parity summary and extrinsic reconstruction.

The 9 October revision adds operation-specific worked tables, controlled
experiments, optional math/hardware panels, progressive hints and explicit
completion criteria. New assets are added without overwriting saved code.
See `docs/LDPC_REVISION_STATUS.md` for delivered versus pending scope and
`docs/LDPC_TUTOR_REVISED_REVIEW.md` for the current complete teaching export.
The older `LDPC_THEORY_AND_BIG_PICTURE_REVIEW.md` is a pre-revision snapshot.

Every checkpoint includes plain-language teaching, worked values, conventions,
an unfinished Python function, a prediction, hints, reflection and a visual.
Visual helpers are provided teaching fixtures, explicitly **not** the learner's
run output. Interactive views include bit/check selection and linked Tanner
graph, LLR confidence, per-edge message exclusion, flooding steps, QC rotations
at Z=2/8/32/96/192/384, a permutation block, signed clipping, lane masking and
bank conflicts. Large rotations show a labeled representative slice.

Use Check syntax, Run public tests, then Submit checkpoint. Syntax checks do not
complete checkpoints. Submit reruns the public suite and unlocks the next task
only when it passes. There are no secret tests in this Python course.

## Runner and state

Normal `.py` files, NumPy, pytest, fresh Docker execution. No notebook kernel.
The existing execution sandbox has networking disabled, dropped capabilities,
resource/time limits, no secrets, no host Docker socket, and no references.
The host/API holds Docker authority; this remains a local educational deployment,
not an authenticated public/multi-tenant grading service.

Runs capture source before queuing. The runner operates on a disposable copy of
the snapshot, not the current editor files. AST parsing does not import learner
code. Public pytest XML reports are normalized with strict expected case counts;
missing/malformed reports, skips, zero checks, timeouts or exit failures cannot
pass. These learner-process reports are not tamper-proof grading authority.

- Sources: `data/labs/<session-id>/workspace/python/`.
- Run snapshot: `data/labs/runs/<run-id>/source/` (not an exposed download).
- Public downloadable report: `data/labs/runs/<run-id>/public-report.json`.
- Session, progress and chat: existing `data/tutor.db`, scoped to `ldpc-5g`.
- Browser session storage: `ldpc-lab-session`; cache retains `rtl-lab-session`.

Original cache sessions, source, progress, and credential files were not reset
or migrated. Switching courses uses separate saved session IDs. Predictive
scratch text is intentionally local to the open lesson view; send it to chat
if you want it retained. Source edits and completed chat messages are saved.

## Tutor

The Python guide uses the existing isolated OpenCode runtime and top-bar AI
settings. Its context contains Python contract/lesson, bounded source, public
tests, run evidence, freshness and recent chat. It does not use cache-specific
reset/handshake diagnosis or receive private author baselines.

2026-10-08 quality refinement: `backend/prompts/ldpc_tutor.txt` requests direct,
beginner-friendly prose, answers to every part of a question, checked numerical
examples, and a distinction between arithmetic, coding constraints, and what
the transmitter/receiver know. Theory questions do not automatically become
quizzes or coding exercises. Model prose is displayed without appending local
fallback metadata; legacy partial JSON only displays model-supplied fields.
This fixes duplicated/unrelated "Next step" and "Think about" sections. There
is no extra model-review request. Better instructions and clean presentation
do not guarantee correctness or equal quality across models; tests validate
prompt/context/formatting using synthetic model replies, not live model quality.

Use a server-configured key or enter a key in this tab. Provider credentials are
temporary in the isolated harness and cleaned after use. Optional fallback
honors the checkbox even for the default model. Status/heartbeat stream and Stop
use the existing transport. With no model/key or an unavailable provider the
answer is explicitly labeled local authored explanation/diagnostic feedback;
it is not claimed as a successful model answer. No model calls occur when
changing a visual, typing or saving.

## Standards and remaining scope

The provided lifting sets were checked against **TS 38.212 V17.9.0, Table
5.3.2-1**, and block-construction direction against Section 5.3.2.
[Authoritative ETSI publication](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.09.00_60/ts_138212v170900p.pdf)

All parity graphs, expanded bases and decoder fixtures in this release are
authored toys, not BG1/BG2. This is a functioning foundational LDPC tutor, **not
a complete standards-conformant 5G decoder** or an implemented accelerator.

Remaining research/implementation milestones from the main prompt:

- Independently verified BG1/BG2 coefficients, encoder/codeword fixtures, graph
  selection, CRC/segmentation, rate recovery and supported NR configurations.
- Full layered decoder, float/fixed comparison and bit-accurate complete decoder.
- Channel/noise modeling, BER/BLER experiments with sample limits/uncertainty.
- Real memory layout, hazard-aware cycle schedule and golden hardware vectors.
- Cited CPU/GPU/FPGA case studies, validated performance figures and RTL course.

Do not interpret lane group counts as full decoder cycles, or Python execution
time as hardware performance. No synthesized frequency, area or power is claimed.

## Verification

Install the author-only dependency with
`.venv/bin/pip install -r tests/requirements-ldpc.txt` if necessary.
Use a disposable `DATA_DIR` and `DATABASE_URL` for API tests.

- 62 focused backend tests passed, including 17 independent author-baseline
  checks covering all 44 public course cases and cache/OpenCode regressions.
- 2 real Docker/API smoke tests passed (`tests/test_ldpc_live.py`, opt-in
  `LDPC_DOCKER_SMOKE=1` with temporary storage).
- 3 frontend SSE parsing tests passed.
- Frontend typecheck and production build passed.
- Browser smoke passed: `web/tests/ldpc-ui.smoke.cjs`. Requires temporary Playwright and
  a separate temporary API on localhost:8021; redirects all browser API traffic
  there so it cannot modify the real learner database. See experiment log for
  the actual latest result rather than assuming that a script's existence means
  it has passed.

The public fixtures are independently sanity checked in test infrastructure
outside the curriculum. Do not mount or send that author-only baseline file to
the learner runner or model.

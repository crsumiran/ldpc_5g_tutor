# Python + Chisel Jupyter tutor: complete implementation strategy

Created: 2026-10-02. Status: design / implementation handoff, not implemented.
Project root: `/home/ranga/opencode/tutor/notebook_tutor`.

## 1. Outcome and scope

Build a reusable assignment tutor with the same learning loop as the cache
tutor, but with real Jupyter notebooks as the main learning surface:

1. Read a short explanation and an observable assignment contract.
2. Predict a result before running an experiment.
3. Implement a small TODO in Python or Chisel / Scala.
4. Explore interactively in the notebook.
5. Run reproducible public checks in an isolated fresh environment.
6. Ask an OpenCode-backed guide about the actual code, results, or artifact.
7. Fix the misconception, explain the reasoning, and unlock the next checkpoint.

Support assignments authored directly, or proposed from a paper / related
papers / a code repository. An author approves the curriculum before it becomes
executable. This is a tutor, not an unrestricted coding agent that completes
the learner's assignment.

Deliver Python first, then the integrated guide, then Chisel. No GPU, distributed
services, automatic paper merging, or Scala notebook kernel is required for MVP.
For a future FP64-via-FP8 course, begin with numerical experiments in Python;
use hardware assignments only where they materially teach the technique.

## 2. What to preserve from the existing tutor

The parent application already demonstrates useful patterns:

- Authored checkpoint contracts and prerequisite-based unlocking.
- Saved learner work and chat, deterministic run results, downloadable artifacts.
- Diagnostic distinctions between compilation, simulation, timeout, and failures.
- OpenCode behind the existing guide UI rather than hand-written model transport.
- A selected-model connection test through the same bridge as real questions.
- Progress events, cancellation, scoped conversations, and checked final answers.

Useful source references to **inspect**, not blindly transplant:

| Parent path | Reusable lesson |
| --- | --- |
| `../docs/OPENCODE_GUIDE.md` | Verified harness architecture and lifecycle |
| `../backend/app/opencode.py` | Async session bridge, status, auth cleanup |
| `../harness/Dockerfile`, `../harness/opencode.json` | Pinned isolated runtime, denied tools |
| `../backend/app/api/labs.py` | Saved chat, run ownership, guide SSE route |
| `../backend/app/verilog/tutor.py` | Grounded responses and context boundaries |
| `../backend/app/verilog/runner.py` | Immutable run copies and public artifacts |
| `../backend/app/adapters/python_pytest.py` | Existing Python adapter concept |
| `../web/src/lib/api.ts`, `../web/tests/guide-stream.test.cjs` | Robust SSE parsing |
| `../docs/security-model.md` | Path, resource, and output limits |

The existing Verilog schemas and reset-specific diagnostics are not the new
generic assignment schema. The old recovery prompt and data-engineering plan
contain historical direct-OpenRouter assumptions; do not treat them as current
harness instructions. New application state must be independent.

## 3. Architecture and decisions

```text
JupyterLab notebook + guide panel       VS Code notebook + companion guide
                  \                       /
                   authenticated application API
                     /          |          \
       workspace / snapshot   run jobs    guide context builder
              |                 |                 |
        SQLite + artifacts   execution worker    OpenCode bridge
                                |                 |
                   Python / Chisel sandboxes    isolated OpenCode
                                |                 |
                     deterministic results   OpenRouter / selected model
```

These are proposed application components, not currently running services.

| Area | Decision |
| --- | --- |
| Main UI | JupyterLab 4-compatible pinned release, real `.ipynb` documents |
| Integrated guide | Prebuilt JupyterLab extension with right-side panel |
| Alternative UI | VS Code notebooks plus companion guide page using the same API |
| Backend | FastAPI, Pydantic, SQLAlchemy, SQLite migrations |
| Job execution | Separate runner worker; bounded queue and one active job initially |
| Notebook tools | `nbformat`, `nbclient`, `ipykernel`; locked dependencies |
| Python checks | `pytest` with structured report; trusted report validation |
| Chisel checks | Pinned Scala / sbt / Chisel / compiler plugin / ChiselSim / Verilator |
| Tutor runtime | Isolated pinned OpenCode server, no learner execution tools |
| Deployment | Separate Compose project and localhost-bound ports |
| Grading | Deterministic; fresh process / kernel, no LLM scoring |
| Hidden grading | Deferred until a separate trusted black-box protocol exists |
| Course creation | Human-approved authored manifest, optionally AI-assisted |

Use Jupyter's editor, kernel integration, outputs, and file handling rather than
reimplementing a notebook editor in React. A JupyterLab extension is frontend
TypeScript; calling the project Python-based does not imply zero frontend code.
It can be packaged as a prebuilt Python-distributed extension. JupyterLab's
documentation describes prebuilt extensions and compatibility considerations.
[JupyterLab extension documentation](https://jupyterlab.readthedocs.io/en/stable/extension/extension_dev.html)

## 4. Target folder structure

Create this incrementally; do not generate placeholder implementations for all
directories before a working vertical slice.

```text
notebook_tutor/
  README.md
  AGENTS.md
  CODEX_START_PROMPT.md
  IMPLEMENTATION_STRATEGY.md
  HANDOFF.md                         # created when implementation starts
  EXPERIMENT_LOG.md
  pyproject.toml
  uv.lock                           # or another explicitly chosen lock format
  .env.example                      # no real credentials
  compose.yaml
  backend/
    app/
      api/                          # courses, sessions, snapshots, runs, guide
      models.py
      schemas.py
      config.py
      persistence/
      courses/                      # validation and authoring boundaries
      workspaces/                   # paths, revisioning, immutable snapshots
      notebook/                     # nbformat, cell mapping, output sanitization
      runs/                         # job lifecycle and result normalization
      adapters/                     # base.py, python.py, chisel.py
      guide/                        # context.py, bridge.py, grounding.py
    migrations/
  runner/
    worker.py
    images/python/Dockerfile
    images/chisel/Dockerfile
    trusted_grader/                  # later; separate private volume/process
  harness/
    Dockerfile
    opencode.json
  jupyter/
    Dockerfile
    server_config.py
    server_extension/               # authenticated forwarding, not grading
  labextension/
    package.json
    src/                            # panel, notebook context, toolbar, settings
  guide_web/                        # small companion UI / VS Code fallback
  tutor_sdk/                        # thin notebook-facing job/artifact helpers
  curriculum/
    python_basics/
      manifest.json
      starter/lesson.ipynb
      starter/src/learner.py
      public_tests/
      assets/
    chisel_basics/
      manifest.json
      starter/lesson.ipynb
      starter/src/main/scala/Learner.scala
      public_tests/
      assets/
  author_private/                   # never served or mounted to kernels/harness
    references/
    private_cases/
  tests/
    unit/
    integration/
    e2e/
  docs/
    SECURITY.md
    COURSE_AUTHORING.md
    TOOLCHAIN_LOCK.md
    RUNBOOK.md
  data/                             # generated, ignored; separate from parent
    tutor.db
    sessions/<session-id>/workspace/
    snapshots/<snapshot-id>/
    runs/<run-id>/artifacts/
```

Exclude `.env`, `data/`, local caches, and private course assets from version
control as appropriate. A notebook output can contain secrets; excluding `.env`
alone is insufficient. Do not publish executed learner notebooks automatically.

## 5. Notebook contract and source of truth

### 5.1 Two assignment styles

Support both, explicitly selected by each checkpoint:

- `module`: notebook explains and imports learner functions in `src/`. Public
  checks import that module in a fresh interpreter. Recommended first slice.
- `notebook_cells`: the implementation lives in tagged cells. Grading executes
  an approved notebook snapshot from top to bottom in a fresh kernel, then uses
  the authored export contract to check its outputs or function behavior.

Do not infer implementation cells from execution counters, displayed output,
position alone, or a regex. Use stable cell IDs and authored checkpoint mapping.
Course-author metadata is loaded from the trusted manifest; notebook metadata
is learner-editable and cannot authorize private files or runner commands.

### 5.2 Recommended notebook shape

Each checkpoint includes:

1. Learning objective, prerequisites, and a precise observable contract.
2. One small worked explanation that does not implement the target TODO.
3. Prediction question and a place for the learner's reasoning.
4. Setup/import cell, editable implementation cell or module link.
5. Small public experiment / visualization.
6. Public-test action and result summary.
7. Reflection question and guide action.

Cell IDs survive saves. Use tags such as `checkpoint:PY-01`, `implementation`,
`experiment`, and `reflection` for navigation, not for access control.
Notebook outputs and execution counts are not proof that a checkpoint passes.

### 5.3 Saving and snapshots

Before `Run public tests`, save the notebook and all declared source files.
JupyterLab waits for its document save promise; filesystem snapshotting occurs
on the backend, not by trusting a reported client hash. For VS Code MVP, require
Save All and return exactly which saved revisions the run used. Add document
snapshot submission for unsaved edits only when conflict checks exist.

Normalize snapshots:

- Validate `nbformat` schema and reject oversize documents / cells / attachments.
- Store original source securely but strip prior outputs and execution counts
  from the execution copy. Never execute stale output or trust its metadata.
- Hash relative paths plus source bytes, relevant manifest revision, dependency
  lock, and runner image digest. Distinguish notebook source hash from module
  source hash and include both in the snapshot identity.
- Record cell ID -> source mapping and the notebook path.
- Make the snapshot immutable. Grade that snapshot, not a mutable working tree.
- Use optimistic revisions for saves; reject conflicts rather than silently
  overwriting another UI's edits.

A later edit marks the displayed run stale. The guide must say whether it is
discussing the saved snapshot or newer live code. Passing unlocks a checkpoint
for a recorded curriculum version; expose revalidation when prior work changes.

### 5.4 Notebook execution policy

Interactive execution is for exploration and may have out-of-order state.
Graded execution always starts a new kernel / interpreter inside the sandbox,
executes the declared setup sequence, and applies per-cell and total deadlines.
Disable `allow_errors` for required graded cells; optional experiment failures
must be declared by the author, not silently ignored globally.

`nbclient` supports fresh notebook execution, kernel choice, working directory,
and cell timeouts. Wrap it in a process / container with a separate overall
deadline and resource limits; its cell timeout is not a full security boundary.
[nbclient execution documentation](https://nbclient.readthedocs.io/en/latest/client.html)

In the notebook-cell style, checkpoint dependencies define an explicit approved
cell sequence. Start with one notebook per checkpoint or straightforward linear
execution. Do not build a magical dependency engine or extract Python using
naive concatenation. Exported names / results must be an authored contract.

## 6. Assignment manifest and authoring

Use strict typed schemas, unknown-field rejection, schema versioning, safe
relative paths, valid unique IDs, and an acyclic prerequisite DAG. An example
**proposed** public manifest:

```json
{
  "schema_version": 1,
  "id": "python-basics",
  "title": "Learn by implementing and testing",
  "revision": "1",
  "checkpoints": [{
    "id": "PY-01",
    "title": "Validate a sequence",
    "adapter": "python",
    "implementation_style": "module",
    "notebook": "lesson.ipynb",
    "implementation_cells": ["py01-contract", "py01-experiment"],
    "editable_files": ["src/learner.py", "lesson.ipynb"],
    "source_files": ["src/learner.py", "lesson.ipynb"],
    "provided_files": [],
    "prerequisites": [],
    "requirements": [
      "Return a new sequence without modifying the input",
      "Handle the empty input as documented"
    ],
    "public_test_targets": ["public_tests/test_sequence.py"],
    "expected_public_checks": 4,
    "runner_profile": "python-small",
    "artifacts": ["public-report.json", "executed.ipynb"],
    "concepts": ["mutation", "edge cases"],
    "hints": ["Inspect aliasing", "Compare input before and after", "Test empty input"],
    "reflection": "Why should this function avoid changing its argument?"
  }]
}
```

Keep private evaluator configuration separate, never serialized into a public
course response. Runner profiles map to administrator-authored argument arrays;
the browser, notebook metadata, or model cannot supply shell commands. Public
test targets are trusted author input checked at course approval.

The authoring pipeline:

1. Ingest only approved local paths / uploaded papers / repositories safely.
2. Inventory without executing imported code, notebook cells, build scripts,
   package hooks, or commands embedded in paper text.
3. Extract topic/prerequisite summaries with exact paper or file references.
4. Propose checkpoint DAG, conceptual explanations, TODOs, tests, and hints.
5. Separate verified claims from assumptions and teaching simplifications.
6. Human reviews the draft and its test/resource profiles.
7. In trusted author CI, verify test behavior on correct and deliberately wrong
   implementations; then publish only starter/public material.

Generated assets are untrusted until reviewed. A course is not auto-gradable
unless its adapter and toolchain smoke tests actually work.

## 7. Common deterministic run protocol

### 7.1 Job lifecycle

`queued -> preparing -> executing -> collecting -> completed`

Terminal alternatives: `failed`, `timed_out`, `cancelled`, `infrastructure_error`.
Persist state transitions and heartbeat timestamps. A worker crash produces a
recoverable interrupted run, not an indefinitely running job or an invented
grade. On restart mark orphaned runs; never automatically execute a submission
again without an explicit retry policy / idempotency key.

One job per session at a time initially. Queue saturation returns a clear busy
response. Cancellation terminates the whole container/process group and cleans
temporary work; it must not merely close the UI spinner.

### 7.2 Normalized result

Implement a shared result type with at least:

```text
run_id, session_id, checkpoint_id, manifest_revision
snapshot_id, source_hash, toolchain_digest
mode: public | submit
job_status, stage, exit_code, timed_out, cancelled, runtime_ms
execution: ok | error | timeout | infrastructure_error
checks: collected, passed, failed, errors, skipped
public_cases: id, status, file/cell, message, expected, observed (bounded)
diagnostics: category, severity, location, bounded message
artifacts: id, relative_name, kind, size, digest
passed: boolean, explanation
```

No universal parsing of human terminal output. Prefer a pytest reporter/plugin
and ScalaTest structured / XML reports. Correlate stage exit codes and report
completeness. Reject malformed, truncated, forged-looking, or inconsistent
reports; reports made in learner execution are diagnostic evidence, not a secure
hidden-grade authority. Courses with adversarial grade integrity require the
separate trusted grader described below.

Public pass requires clean execution, expected checks collected, no unexpected
skips, zero failures/errors, complete report, and no timeout/cancellation.
Collection counts must match the authored expectation / approved test inventory.
`0 passed / 0 failed` is never a passing test run. Separate syntax errors,
import errors, missing dependencies, assertion failures, timeouts, JVM failures,
elaboration failures, and simulator infrastructure errors.

For numeric checks, record tolerance and scale explicitly. For hardware checks,
record sampling edge, reset semantics, expected cycle, observed cycle, and
bounded public trace context. Correct-looking plots do not override assertions.

### 7.3 Artifacts

Persist artifacts at `data/runs/<run-id>/artifacts/`, including optional
`executed.ipynb`, `public-report.json`, sanitized logs, plots, `generated.sv`,
and `wave.vcd`. Normalize simulator output paths into that directory; do not
assume every simulator writes a file named `wave.vcd` automatically.

Every artifact has a manifest allowlist, size limit, owning run/session, and
hash. Download routes validate identity and ownership; reject symlinks and
traversal. Do not recursively expose a simulation build directory. Generated
RTL may appear only when public course policy permits it. Hidden trace artifacts
are never learner-visible.

Render untrusted notebook outputs under Jupyter's trust rules. Do not insert
arbitrary HTML/SVG/JavaScript into the guide panel. Prefer escaped text, bounded
tables, and sanitized raster plots. Never silently trust an executed notebook.

## 8. Python execution adapter

First implement module assignments:

1. Snapshot declared module and notebook files.
2. Prepare a temporary workspace with public fixtures/test files only.
3. Start a pinned offline Python image with no host mounts beyond that snapshot
   and a bounded artifact directory; do not inherit host environment secrets.
4. Run `python -m pytest` with administrator-authored argv and a structured
   reporting mechanism; do not execute a command typed into a notebook as the
   grader's command.
5. Normalize failures by function, file/line, exception type, expected/observed
   value, and declared requirement. Avoid dumping giant arrays or datasets.
6. Store results and artifacts; leave original files untouched.

Then add notebook-cell assignments with `nbclient` in the same isolation model.
Include a test demonstrating that a notebook which only works due to an old
interactive variable fails clean-kernel grading with a useful cell-ID diagnostic.

Suggested starting limits, explicitly configurable profiles: 1 CPU, 512 MiB,
128 processes, 30 seconds per graded cell, 120 seconds total, 128 KiB text log,
20 MiB artifact budget. They are starting policy values, not universal adequate
limits. Avoid arbitrary pip installs, internet retrieval, or unbounded file I/O
inside learner grading. Bake approved dependencies / datasets into images.

## 9. Chisel assignments from a Python notebook

### 9.1 Recommended first Chisel workflow

Keep the notebook's kernel Python. Use Scala project files as the implementation:

- Explanations, timing diagrams, plots, predictions, and questions in notebook.
- Learner edits `src/main/scala/Learner.scala` directly, or uses an explicitly
  documented `%%writefile` cell that writes this file into the learner workspace.
- Run actions call a narrow `tutor_sdk` helper which submits a checkpoint job to
  the API, not a general shell executor.
- Runner performs Scala compilation, Chisel elaboration, simulator compilation,
  and public simulation in an isolated Chisel image.
- Notebook displays normalized checks, generated public RTL if allowed, and
  links to waveform artifacts / cycle tables.

Direct file editing and `%%writefile` cannot both be authoritative silently:
pick one per checkpoint and show which source revision is graded. If the course
uses a source-writing cell, save and execute that cell before snapshotting the
resulting Scala file. A stale cell must not overwrite a newer direct edit.

A Python kernel cannot execute Scala just because a cell contains Chisel.
Notebook magic writes text; the runner executes Scala in the toolchain image.
An Almond / Scala kernel can be a later optional mode with its own compatibility,
isolation, and clean-kernel tests. It is not required for a coherent MVP.

### 9.2 Toolchain gate

Use sbt for the first multi-file course; a separately verified Scala CLI profile
is optional for tiny examples. The official installation guide documents Chisel
as a Scala library/compiler plugin and describes build-tool options.
[Chisel installation](https://www.chisel-lang.org/docs/installation)

Modern Chisel documentation describes ChiselSim with ScalaTest integration and
simulators including Verilator. Prefer that route for new courses, subject to
actual pinned-version compatibility. Do not assume an older `chiseltest` example
compiles with a new Chisel release.
[Chisel testing](https://www.chisel-lang.org/docs/explanations/testing)

Before the first real assignment, lock and record:

- JDK, sbt, Scala full version, Chisel library and compiler plugin.
- ScalaTest and simulator integration, firtool, Verilator and C++ toolchain.
- Dependency lock/cache strategy, OS image digest, environment and command argv.
- Exact working compile, elaborate, test, and trace-generation commands.

Image-build time may access networks to fetch dependencies; learner execution
may not. Pre-warm sbt/Coursier/Ivy and native dependencies in the image. Provide
a writable per-run copy/overlay of required cache state, not a shared writable
cache poisoned by learner runs. Offline verification is mandatory: network
disabled, empty learner workspace caches, simple module compiles and simulates.
If firtool or dependencies try to download on first run, the gate has failed.

Suggested Chisel profile: 2 CPUs, 2–4 GiB memory, bounded JVM heap and subprocess
count, 180-second compile budget, 300-second total. Measure cold/warm behavior
and adjust for the host; do not apply the Python timeout unchanged.

### 9.3 Public result evidence

Distinguish Scala syntax/type errors, Chisel connection/width/elaboration errors,
RTL emission errors, simulator compile errors, assertion failures, and exhausted
cycle budgets. Parse machine reports where possible and bound compiler logs.

Show actual values and cycles from public checks. A waveform question requires
the correct run's trace, signal mapping, width/signedness, reset contract,
sampling edge, and expected latency. If those are missing, say what evidence
is missing rather than inventing a mismatch explanation.

Start curriculum: combinational mux -> width/signedness -> counter and reset ->
valid/ready handshake -> small pipeline -> compare Python reference model with
public hardware outputs. Keep numerical formats / paper-specific blocks later.

## 10. Notebook-facing SDK and UI

Proposed thin API for trusted notebook setup cells:

```python
from tutor_sdk import TutorSession

session = TutorSession.from_environment()  # scoped app identity, never model key
run = session.run_public("PY-01")         # saved source snapshot; returns job
result = run.wait(timeout=150)             # poll status, allow cancellation
result.display()
session.show_artifacts(run.id)
```

This is an interface to implement, not an existing import. Scoped app credentials
must authorize only this session's public jobs/artifacts, have expiry, and never
grant Docker, OpenCode auth, author-private, admin, or other sessions' access.
Kernel-visible session capability is not the OpenRouter key. Model settings and
key entry live in the guide UI, not cells; MVP need not allow model calls from
the kernel at all.

### JupyterLab guide panel

- Top settings: model picker, optional ephemeral key entry, connection test,
  explicit optional fallback, actual served model / source indicator.
- Notebook context: course, session, checkpoint, selected cell/source file.
- Actions: Run public checks, Submit (disabled before private grading exists),
  Ask guide, Explain failure, Reflect, Stop guide, Cancel run.
- Run display: stage, count, timing, source freshness, public errors, artifacts.
- Chat: question, status, checked answer, evidence references, small next step.

Read notebook context from JupyterLab document APIs; do not scrape page HTML.
Save source before grading. Only explicit actions transmit code/question; never
call the model per keystroke, selection, autosave, or kernel output update.

Guide question modes include concept, diagnostic, experiment interpretation,
and reflection. Modes shape context, not a canned answer structure. A direct
conceptual question should receive a direct answer, even before any run exists.

### Authentication and routing

JupyterLab browser -> authenticated Jupyter server extension -> internal FastAPI
is the preferred same-origin route. Enforce Jupyter auth, XSRF checks, and route
ownership; forward only a narrow set of application endpoints. Do not proxy
arbitrary URLs or expose an unrestricted OpenCode endpoint. Redact secrets from
proxy logs. Configure streaming/heartbeats so the proxy does not buffer SSE.

For an early companion UI, serve it same-origin through the Jupyter extension
or give the standalone API explicit local authentication and strict allowed
origins. Being on localhost is not sufficient auth; do not solve routing by
disabling Jupyter token auth or allowing `*` origins with credentials.

### VS Code / WSL path

VS Code can edit `.ipynb` / Scala files and attach to the local authenticated
Jupyter server. Its notebook UI does not load a JupyterLab sidebar extension.
Provide a companion guide page using the same API and saved-file workflow;
open it beside the notebook in an embedded browser or Windows Edge/Chrome.
Keep VS Code as a supported alternate surface, not a second notebook engine.
If integrated routing fails, check service health first, then auth and port
forwarding. Do not assume `ERR_CONNECTION_REFUSED` is an editor problem.

## 11. OpenCode integration: reuse the harness, keep the tutor boundary

### 11.1 Runtime

Use a separate internal OpenCode container. Parent integration pins 1.18.31;
that is a known starting point, not a recommendation to assume latest behavior.
Inspect the selected binary's `/doc` OpenAPI schema before copying request
fields; newer versions may change permissions, message types, or lifecycle.
Record and test the version actually deployed.

OpenCode's official server API provides health, sessions, asynchronous prompts,
message/status retrieval, abort, and provider auth. The bridge should encapsulate
these calls, not expose the harness directly to notebooks or browsers.
[OpenCode server API](https://opencode.ai/docs/server/)

Runtime restrictions:

- No host-published harness port, notebook mounts, author assets, Docker socket,
  host home, host OpenCode settings, or host credentials.
- Use private tmpfs for auth/session/cache runtime state and disable auto-update.
- Deny tools globally, per tutor agent, and per session according to the pinned
  runtime schema. Verify an attempted read/shell/edit is denied, not merely that
  a config file contains the word `deny`.
- Restrict outbound network where practical to provider requirements; do not
  permit arbitrary learner/model tool fetches. No remote MCP tools in MVP.

### 11.2 Credential lifecycle and concurrency

Key entry is in-memory in the UI by default. Never put it in saved notebook
code/outputs, browser local storage, URL parameters, chat history, exceptions,
or persistent server logs. If a future persistent key option exists, it requires
explicit consent and a proper secret store, not plaintext SQLite.

With a shared runtime, provider auth is global: acquire a single serialization
lock for credential install -> provider-instance disposal -> model request ->
abort/cleanup -> credential removal -> disposal. Release in `finally`, including
cancellation and parse failures. Gate calls if cleanup fails. Do not reuse a
Python threading lock across multiple API workers and claim isolation; MVP uses
one worker and one owning guide queue. Queue waiting also needs timeout/cancel.

For multiple users or workers, isolate runtimes per credential owner or introduce
a single credential broker with cross-process locking and tested guarantees.
Set session identity to `(user, session, course revision, checkpoint, model,
key fingerprint)`; never store raw keys in the map. Restore a bounded amount of
saved chat when a runtime restarts. User identity must precede client-supplied
session identifiers.

### 11.3 Request and retry behavior

- Build a bounded context from trusted contract + current public evidence.
- Set requested provider/model exactly; model IDs come from current catalog /
  configuration, not hardcoded claims that a named model stays free forever.
- Use async prompt and short status polls (or a verified native event stream).
- Let OpenCode handle provider-native streaming/retries; do not wrap it in an
  unbounded additional retry loop.
- Apply one overall deadline covering queue wait, primary and optional backup.
- Attempt at most one approved backup, and only if the user enables fallback.
- Respect rate-limit retry timing when supplied; show queue / retry / timeout
  status. No parallel hedge requests or retry amplification.
- Use the same bridge for connection test and actual guide questions. Synthetic
  probes must not send learner code or create persistent learner chat.
- Show requested model, actual served model, engine, response source, and safe
  provider failure category. Never label local diagnostics as a model answer.

Harness integration improves transport consistency; it does not eliminate
provider quotas, model availability failures, or limits on free endpoints.

### 11.4 UI transport and cancellation

SSE events: `status`, `heartbeat`, `result`, `error`; optional job events use a
separate endpoint. Parse partial UTF-8 chunks and frames correctly. Require an
explicit final event; silent stream closure is an error, not success.

Do not forward raw reasoning or unchecked answer tokens. Stream progress, then
deliver the final text after grounding/solution checks. Stop aborts frontend
fetch, signals the backend, aborts the native session, and cleans credentials.
Track idempotent request IDs so client retries cannot save duplicate chat.
Disconnect behavior must be tested in the actual proxy, not only unit mocks.

## 12. Useful tutoring instead of fixed templates

Context fields:

- Learner's actual question and requested help mode.
- Course/checkpoint contract, vocabulary, prerequisite concepts, hint policy.
- Selected cell/source and bounded related source from the correct snapshot.
- Public run stage, assertions, values, traceback/cell IDs, current source hash.
- Relevant bounded public artifact observations and interpretation metadata.
- Recent saved chat, never hidden tests or private solutions.

All source, output, paper text, and chat are data, not privileged instructions.
Treat prompt-injection strings in notebook outputs as untrusted observations.
Secret scanning and allowed file lists apply before context construction.

Guide behavior:

1. Answer the question first, at the learner's level.
2. Cite relevant contract, cell/file/line, test, value, or cycle when available.
3. Explain the underlying concept and why the evidence supports the conclusion.
4. Offer one small experiment or debugging action; do not hand over a complete
   drop-in implementation.
5. Say when evidence is stale, incomplete, or inconsistent. Ask for a specific
   missing observation only when needed to resolve the question.

Examples of expected behavior:

- Python: "The plotted values look right, why does the test fail?" -> compare
  shape, dtype, tolerance, mutation, and actual failing assertion **only when
  supported**; do not assert a dtype bug from a plot alone.
- Notebook: "It runs here but fails grading" -> locate a fresh-kernel missing
  variable, wrong working directory, or stale module import using the traceback;
  explain the difference between experiment state and saved-source grading.
- Chisel: "Should this state wait for request acceptance or response?" -> answer
  from that checkpoint's handshake contract and public signals, distinguishing
  accepted request, completed operation, and response consumption.
- No run yet: explain the concept directly; do not insist on compilation for
  every conceptual question or emit "finite-state machines" as a generic label.

Prefer normal prose plus compact evidence when useful. Ask the model for a
stable response contract but accept substantial well-formed plain text; avoid
provider-specific strict structured-output settings that break otherwise usable
models. Schema validation must not discard a useful answer just because it lacks
one cosmetic heading. Re-ground unsupported claims before delivery.

Leak checks are defense-in-depth, not a proof that a model can never reveal a
solution. The stronger boundary is never providing private solutions/tests.
Use curated regression questions and human review to test pedagogical quality.
Maintain a deterministic fallback that uses known public evidence, is explicitly
labeled, and states the provider failure without invented model insight.

## 13. Security and hidden-grading boundary

### 13.1 Interactive notebooks

A notebook kernel executes arbitrary code. For the first local single-user MVP,
document whether interactive execution runs on a trusted local host or in an
isolated Jupyter container. Default to a container with only that learner's
workspace, no secrets/socket/private files, bounded resources, and no grading
privileges. Do not call a shared host kernel sandboxed.

Jupyter server/token isolation, kernel isolation, runner isolation, and model
permissions are separate boundaries. The server extension may proxy authorized
requests; it cannot stop Python code from accessing anything mounted to its
kernel container. Restrict mounts and credentials accordingly. Multi-user
deployment requires per-user isolation/auth design beyond this single-user MVP.

### 13.2 Public runner isolation

Run with network disabled, dropped capabilities, non-root user, read-only root
filesystem, no-new-privileges, memory/CPU/PID/time/output limits, bounded tmpfs,
and a disposable writable workspace copy. Backend never imports learner modules.
Reject symlinks, traversal, oversized files, and archive escapes before copying.

Only the runner control service may access Docker. The Docker socket is effectively
host-level authority, not a harmless mount. It must not be reachable from the
notebook, browser, OpenCode, or learner execution containers. Limit and audit the
worker's accepted image/profiles/mount roots; use stronger isolation for hostile
multi-tenant workloads. Container controls alone are not a universal security
guarantee.

### 13.3 Private tests: do not repeat an unsafe shortcut

Read-only means "cannot modify", not "cannot read". If a hidden Python test or
Scala suite is mounted into the same container as learner code, that code can
usually inspect it or expose private data in outputs. Redacting HTTP response
fields does not restore secrecy. This applies to the parent runner pattern too;
do not inherit its hidden-test mounting strategy for arbitrary notebook code.

MVP: public tests only, with clear disclosure that checks are a learning aid, not
tamper-proof assessment. Disable Submit or define it as public-only completion.

Later trusted grading:

- Keep private cases in a grader service/container with no learner mounts or
  learner imports. It generates inputs and compares observed outputs itself.
- Start a separate learner execution container with no private source, expected
  outputs, references, secrets, or grading credentials.
- Exchange bounded protocol messages through a controlled channel. For Python,
  a fixed function/JSON interface can support many beginner assignments. The
  trusted grader owns comparisons and final pass/fail, not learner report files.
- For Chisel, compile learner HDL in an untrusted compile stage, validate the
  artifact, and evaluate via a separate restricted simulation/protocol pipeline.
  Generated RTL and simulator code are still untrusted; do not load them into
  the private grader process. Design this boundary before enabling secret cases.
- Do not claim every notebook, arbitrary Python object, or arbitrary hardware
  test can use the initial protocol. Unsupported assignments stay public-only.
- Inputs intentionally delivered to learner execution are necessarily visible
  to it; promise secrecy of test source/reference/expected data, not impossible
  secrecy of values sent to the program. Never return private raw stdout/traces.

A locally controlled learner can inspect local services/volumes outside the app;
hidden-test confidentiality against the machine owner requires a remote trusted
grader. State the threat model honestly.

## 14. Proposed application API and persistence

All routes below are **new contracts to implement**, not parent API routes.
They require authentication/ownership checks and strict typed payloads.

| Method / path | Purpose |
| --- | --- |
| `GET /api/health` | Component readiness, no credentials |
| `GET /api/courses` | Public approved courses |
| `GET /api/courses/{id}` | Public manifest / revision |
| `POST /api/sessions` | Materialize new learner workspace, never overwrite |
| `GET /api/sessions/{id}` | Progress, checkpoint, saved revisions |
| `GET/PUT /api/sessions/{id}/files/{path}` | Allowlisted files, revision conflicts |
| `POST /api/sessions/{id}/snapshots` | Atomic saved-source snapshot |
| `POST /api/sessions/{id}/runs` | Queue profile-based run against snapshot |
| `GET /api/runs/{id}` | Normalized status and public results |
| `GET /api/runs/{id}/events` | Job stage progress / heartbeat |
| `POST /api/runs/{id}/cancel` | Terminate job safely |
| `GET /api/runs/{id}/artifacts/{artifact-id}` | Authorized bounded download |
| `GET /api/models` | Model catalog, no unsupported/free availability promises |
| `POST /api/guide/test` | Synthetic same-bridge selected-model probe |
| `POST /api/sessions/{id}/guide/stream` | Explicit question/context, SSE response |
| `POST /api/guide/requests/{id}/cancel` | Explicit cancel fallback to disconnect |
| `GET /api/sessions/{id}/chat` | Saved checked replies, scoped checkpoint |

Avoid HTTP GET bodies for keys; use authenticated POST for key-filtered catalog
queries if needed. No credential in URL/query string. Artifact URLs should use
opaque IDs and authorization, not raw absolute file paths.

Persistence entities: courses/revisions, sessions, checkpoint progress,
workspace revisions, snapshots, runs/stages, public cases, artifacts,
chat/messages, guide requests, and job lease/heartbeat. SQLite stores metadata;
source/artifacts are revisioned files. Backups include database plus referenced
files with a consistency plan. Browser storage is not the only way to recover
a session; provide a server-side session picker.

## 15. Deployment and runbook design

Use Compose project `notebook-tutor`, not the parent's default project. Suggested
initial ports: authenticated Jupyter UI `127.0.0.1:8889`, companion guide
`127.0.0.1:3010` only if necessary, API `127.0.0.1:8010` only for development.
Check availability before binding. OpenCode stays internal on 4096 in its own
network; identical internal port does not conflict with the parent runtime.

Services: `jupyter`, `api`, `runner`, `opencode`, plus image build targets for
Python and Chisel execution. Use narrow per-service mounts. For MVP bind only
the active learner workspace to Jupyter; session switching/multiple users require
explicit container/kernel lifecycle handling, not exposing all sessions.

If the runner uses the host Docker daemon, bind source paths must exist on the
host at the same absolute location expected by Docker. Record an explicit
project root setting; do not use an API-container-only `/workspace` path as a
host bind source. Do not mount the entire parent repo to solve that problem.

Readiness distinguishes UI serving, API database readiness, runner profile
availability, and harness health. Start dependency services with health checks;
persist jobs safely on restart. Set appropriate restart policies without using
restart loops to mask missing dependencies.

Once implemented, document these commands with actual evidence:

```bash
docker compose -p notebook-tutor config --quiet
docker compose -p notebook-tutor build
docker compose -p notebook-tutor up -d
docker compose -p notebook-tutor ps
```

Do not run them against a nonexistent Compose file and claim deployment.
Document authenticated browser entry without exposing Jupyter tokens in handoff
logs. If a UI refuses connection: inspect containers and localhost health first;
then check VS Code remote port mapping, authentication, and streaming proxy.

## 16. Milestones with concrete acceptance gates

### Milestone 0 — isolation, environment, and version decisions

Create application scaffold, separate Compose project/config, disposable storage,
auth/routing design, and Python lock. Verify no conflicts with the running parent.
Record Docker/Jupyter/Python/tool versions. Create this project's handoff/log.

Acceptance: parent state unchanged; paths/ports isolated; health tests use new
temporary data; manifests validated; no key required just to run public checks.

### Milestone 1 — Python public-test vertical slice

One authored module-style notebook assignment, session creation, save/revision,
immutable snapshot, queue/worker, Python sandbox, pytest structured results,
artifact download, and progress. Small companion guide placeholder can say
"AI integration not implemented"; do not fake a model answer.

Acceptance: deliberately wrong code fails usefully; corrected code passes;
empty collection, import error, timeout, and cancellation are distinct; restart
retains edits/progress; learner files unchanged by grading. Notebook is valid
and can be edited/executed through Jupyter and VS Code saved-source workflow.

### Milestone 2 — notebook-native grading and freshness

Add stable cell contracts, clean-kernel `nbclient` execution, executed-notebook
artifact, cell-ID diagnostics, save-before-run and stale-run indicators.

Acceptance: out-of-order hidden-state notebook fails fresh execution; renamed /
deleted implementation cells yield contract errors; old outputs never count as
checks; run snapshot still matches stored source after a concurrent edit.

### Milestone 3 — OpenCode guide end to end

Implement isolated runtime, bridge, settings/model picker/key entry, shared-path
probe, evidence context, native retries, optional backup, progress SSE, Stop,
auth cleanup, checked answers, saved scoped chat, labeled fallback.

Acceptance: synthetic selected-model question uses correct native model; no
learner content in probe; provider errors safe; no key remains after completion,
timeout/cancel/error; no tools usable; stream disconnect tested; fallbacks honor
checkbox even when using server-default model. Live model test is optional when
no key supplied; mock tests must pass and lack of live validation is disclosed.

### Milestone 4 — integrated JupyterLab panel

Ship prebuilt extension with notebook-aware sidebar, explicit context selection,
test toolbar, settings, progress, artifacts, chat, cancellation, and same-origin
authenticated forwarding. Retain companion UI for VS Code.

Acceptance: unsaved document is saved before run; save conflicts surfaced;
switching notebook/checkpoint cannot mix questions/results; no LLM requests on
autosave/typing; model dropdown stable; no persistent secret storage.

### Milestone 5 — Chisel toolchain and adapter

Pass offline toolchain gate, compile/elaborate/simulate tiny circuit, implement
staged diagnostics, reports, generated public RTL and waveform collection.
Then author two small Chisel checkpoints controlled from Python notebooks.

Acceptance: fresh network-disabled run works; wrong reset/latency case fails with
cycle evidence; compilation failure isn't zero successful tests; waveform
download corresponds to exact run; no Scala kernel requirement.

### Milestone 6 — trustworthy diagnostics and pedagogy

Curated question suite covering stale code, mutation, dtype/shape/tolerance,
missing state, valid/ready, reset/clock, no test evidence, provider failure,
prompt injection, request for full solution, and cross-checkpoint chat leakage.

Acceptance: answers address the question, cite public evidence where appropriate,
admit missing observations, propose small actions, and never invent a grade.
Human review evaluates teaching quality; unit tests cannot prove it alone.

### Milestone 7 — private black-box grading, if required

Design protocol and threat model before implementing. Keep private grading
separate from learner execution. Limit to supported function/circuit interfaces.

Acceptance: learner cannot access private sources/expected values/credentials
through its container; private results/traces excluded from app/model context;
tampered learner reports cannot authorize pass; explicitly document local-owner
limits. If these gates fail, remain public-only instead of claiming secrecy.

### Milestone 8 — paper authoring / FP64-via-FP8 specialization

Only after the paper is supplied: map math/prerequisites, reproduce toy results,
review a curriculum DAG, add Python experiments, and optional Chisel blocks.

Do not assume the paper implements general IEEE FP64 arithmetic using a single
FP8 value. It may target a specific operator, decomposition, accumulation,
matrix product, scaling, or error regime. Record exact formats, exponent ranges,
rounding, summation precision, error bounds, and hardware assumptions. Distinguish
bitwise equivalence, toleranced accuracy, and approximations. Test subnormals,
overflow/underflow, cancellation, NaN/Inf, reproducibility, and supported input
domains only as applicable to the paper's actual method.

Acceptance: each claim traceable to a supplied paper or labeled teaching model;
each assignment has a small deterministic check; reference and numerical
baseline independent of the incomplete learner implementation; no invented
performance or FP64-equivalence claim.

## 17. Required verification matrix

Before calling the product ready, test:

- Paths: traversal, symlinks, unsafe uploads, oversized cells, notebook schema.
- Ownership: other session files/runs/chat inaccessible; proxy routes restricted.
- Execution: fresh kernel, timeouts, infinite loops, subprocess leaks, memory,
  cancellation, unexpected skips, incomplete reports, zero collected checks.
- Reproducibility: source/manifest/image hash, stale indicators, immutable copies.
- Persistence: source save conflicts, restart, orphaned job, session recovery.
- Artifacts: exact owning run, allowlist, sizes, no private trace/log leakage.
- Harness: model forwarding, auth cleanup on all exits, no overlapping keys,
  session isolation, bounded retry/backup, tool denial, safe failure messages.
- Streaming: chunked UTF-8, partial frames, heartbeat, truncation, cancellation
  across the actual Jupyter/companion proxy; no duplicates after retry.
- UI: stable typing/model picker, no requests on keystroke, notebook switching,
  save-before-run, accessible status/errors, download behavior in chosen browser.
- Chisel: offline image build gate, syntax/width/elaboration/simulator distinctions,
  reset/edge/latency sampling evidence, public VCD collection.
- Security: no keys in notebooks/output/logs/SQLite/localStorage, no socket in
  learner/harness, no host home mounts, no hidden data in model context.

All automated tests use temporary database/workspace directories. Real provider
smokes use synthetic content, explicit configuration, and one bounded request;
do not burn quota by repeatedly running connection tests in CI.

## 18. Definition of done and implementation handoff

MVP is ready only when a learner can open a notebook, implement a Python TODO,
run checks from a saved snapshot, read a useful failure, ask the OpenCode guide,
receive a grounded answer, fix the code, and retain progress after restart.
Then demonstrate the same loop for a tiny Chisel assignment with cycle/trace
artifacts. Report separately if integrated panel or Chisel remains incomplete.

The implementing agent's handoff must include:

- Working features vs planned/deferred ones; public-only vs private grading.
- Exact setup/launch/authentication instructions, ports, versions, image digests.
- Tests actually run and outcomes; live model smoke if available.
- Where notebooks, source, snapshots, waveforms, and other artifacts live.
- Data preservation/recovery and service-stop/cancel behavior.
- Known limitations: interactive isolation, provider limits, numerical claims,
  missing toolchains, unsupported assignment types, local-owner threat model.
- Next milestone with a concrete acceptance command or manual scenario.

Do not report this design document itself as an implemented notebook tutor.

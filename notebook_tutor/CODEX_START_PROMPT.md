# Prompt for the implementing Codex instance

Paste the following into Codex opened in this directory:

```text
Build a new notebook-based learning tutor in this workspace. First read
AGENTS.md and IMPLEMENTATION_STRATEGY.md completely. This is a separate
application from the working cache tutor in the parent directory. Preserve
the parent's code, services, data, credentials, and learner progress.

The product must support Python assignments in real Jupyter notebooks,
Chisel/Scala hardware assignments controlled from the same notebook workflow,
and an OpenCode-backed guide that can interpret the selected assignment,
learner code, fresh public test results, and artifacts. It must answer the
learner's actual question using evidence, not a generic fixed template.

Implement milestone 0 and then milestone 1 from the strategy: validate the
environment, create an isolated application, and deliver one public-test-only
Python assignment that works end to end. You may inspect parent source for
reusable patterns. Do not copy secrets, learner data, or private curriculum.
Do not implement every later milestone speculatively. Record later work in
HANDOFF.md, with the next milestone ready to execute.

Use real .ipynb files and nbformat validation. Grade immutable snapshots in a
fresh, resource-limited, network-disabled execution container. Store source
hashes, cell IDs, results, and artifacts. Make no claim that an interactive
kernel result is a reproducible grade. Treat zero collected tests as an error.

Begin with JupyterLab as the notebook UI and a small separate guide page if
needed to complete the vertical slice. The final integrated interface is a
prebuilt JupyterLab guide panel. Keep the service contracts usable from VS
Code notebooks without requiring the JupyterLab extension there. Use separate
ports and a separate Compose project from the parent application.

Do not build a custom provider SDK or a privileged autonomous coding chatbot.
Reuse the parent isolated OpenCode-server bridge pattern, with model selection,
temporary key handling, session scoping, native retries, cancellation, useful
status events, checked final responses, and an explicitly labeled diagnostic
fallback. Implement that integration in its designated milestone.

For Chisel, default to Scala source files plus an sbt / ChiselSim / Verilator
runner controlled from a Python notebook. Before locking versions, verify a
compatible toolchain by actually compiling and simulating a tiny circuit
offline in its image. A Scala notebook kernel is optional later, not a blocker
for the Python vertical slice.

Do not implement hidden tests by mounting private test source where arbitrary
learner code can read it. Use public tests first. Later use a separate trusted
black-box grader with no private mounts in the learner container, or explicitly
document that secrecy is not provided for a given course.

Run focused automated tests and an end-to-end smoke test in temporary learner
storage. Record commands and evidence in HANDOFF.md and EXPERIMENT_LOG.md.
Report what is actually working, what is still only planned, how to launch it,
and the next concrete milestone. Do not print API keys or modify parent state.
```

## Continuing after the first slice

```text
Read AGENTS.md, IMPLEMENTATION_STRATEGY.md, HANDOFF.md, and the newest entries
in EXPERIMENT_LOG.md. Verify the last completed milestone without changing
learner state, then implement the next incomplete milestone. Preserve all
existing notebook work and services. Update the handoff with actual evidence.
```

## When a paper is supplied

```text
Use the paper and any explicitly supplied companion papers to propose a
beginner-to-paper assignment DAG for this notebook tutor. Cite claims by paper
section, page, equation, figure, or experiment. Clearly distinguish the paper's
results from teaching simplifications and unverified assumptions. Analyze
without executing downloaded code. Draft COURSE_RESEARCH.md and a manifest
proposal; do not silently approve or launch generated code. Include small
Python experiments before optional Chisel implementations, observable
contracts, public tests, hints, and reflection questions. Ask for curriculum
approval before making the draft an executable course.
```

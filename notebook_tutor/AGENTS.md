# Agent instructions for the notebook tutor

Scope: this directory and its descendants only.

## Read first

Read `README.md`, `IMPLEMENTATION_STRATEGY.md`, and `CODEX_START_PROMPT.md`
completely before implementing. The strategy distinguishes future contracts
from features verified in the parent cache tutor.

## Project boundaries

- Implement the new Python / Chisel notebook tutor here. Do not modify the
  parent cache tutor's code, Compose project, curriculum, `.env`, running
  containers, database, or learner workspaces.
- Parent source may be inspected for reusable patterns. Copy only relevant
  source after reviewing dependencies; never copy parent `data/`, `.env`,
  reference solutions, hidden tests, API keys, or host OpenCode credentials.
- Give this application its own Compose project, service ports, database,
  runtime directories, and learner storage. Never run a parent Compose command
  as part of implementing this application.
- Preserve existing work. Do not overwrite a learner notebook or module when
  creating a session. Do not execute imported paper/repository code during
  analysis.

## Implementation principles

- Build one milestone at a time, verify it, and record evidence. Start with an
  end-to-end public-test-only Python vertical slice.
- Real notebooks are the learning surface; the deterministic runner decides
  pass/fail; OpenCode is an advisory guide, not the grader.
- Notebook experimentation and clean-kernel grading are different operations.
  Persist an immutable source snapshot for every graded run.
- Do not run learner code inside the API process. Do not give notebook kernels
  or OpenCode a Docker socket, host credentials, grader secrets, or reference
  implementations.
- Do not describe read-only test mounts as secret from learner code running in
  the same process/container. Defer hidden grading until the isolated trusted
  grader protocol exists.
- Keep OpenRouter keys out of notebook cells, outputs, saved files, URLs, chat,
  logs, and browser persistent storage. Use ephemeral credential handling.
- Do not expose raw model token streams before response safety checks. Stream
  status and deliver the checked final answer.
- Pin and verify the entire Chisel toolchain with compile, simulation, artifact,
  and offline execution smoke tests. Do not guess compatible versions or APIs.
- Keep OpenCode version-specific calls behind one bridge. Verify its actual
  `/doc` schema and deny-tool behavior before upgrading its runtime.
- Never claim passing from zero collected tests or a stalled simulation.

## Handoff

Maintain `HANDOFF.md` and `EXPERIMENT_LOG.md` inside this folder as work begins.
Record exact versions, commands, results, current services, limitations, and the
next milestone. Do not record secrets. Use disposable data directories for
verification, not learner state.

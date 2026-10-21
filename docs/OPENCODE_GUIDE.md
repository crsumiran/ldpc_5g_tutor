# OpenCode guide integration

The local Compose deployment uses OpenCode 1.18.31 as the tutor runtime.
The existing FastAPI application still supplies checkpoint requirements,
learner-visible source, public test results and waveform observations, checks
the response, and saves chat/progress in the existing SQLite database.

## Running

Run `docker compose up -d --build` from the repository root, then open
http://localhost:3000. Select the OpenRouter model in AI settings as before.
`Test guide connection` now uses the same OpenCode bridge as tutor messages.
Successful model answers show `Guide model: OpenCode` and the served model ID.

Compose defaults `TUTOR_ENGINE` to `opencode`. Set `TUTOR_ENGINE=openrouter`
in `.env` and recreate `api` to use the previous direct provider transport.
`OPENCODE_TIMEOUT_SECONDS` defaults to 180 for the overall model operation.
The optional next-model attempt shares that budget. OpenCode manages retries
and streaming within each model attempt; the bridge polls its asynchronous
session API rather than buffering a long provider HTTP response.

## Conversation and credentials

- OpenCode sessions are separated by lab session, checkpoint, model and key
  fingerprint. The fingerprint is used only for the in-memory mapping.
- Existing OpenCode sessions retain conversation context. New sessions receive
  up to six recent saved messages from this checkpoint, so backend/runtime
  restarts do not discard the learner's saved chat.
- The API serializes harness calls because OpenCode provider authentication is
  shared within a runtime. It sets the request's key, disposes cached provider
  instances, performs the request, then removes the credential and disposes
  cached instances again. This deployment uses one API worker.
- The harness has no published host port. It mounts neither the repository,
  learner workspaces, host OpenCode credentials nor the Docker socket. Its
  authentication, session database and cache live on `/runtime` tmpfs and reset
  when the container is recreated. The app's learner database remains on disk.
- Global, agent and session permissions deny tools. The harness receives only
  the supplied context, with no reference implementations or hidden test code.

## Response flow

The page posts to `/api/lab-sessions/{id}/tutor/stream`. Server-sent events carry
connection/model/retry status and five-second heartbeats. Model text remains
inside the harness until the existing grounding and solution-leak checks run;
the checked result is then delivered and saved. The page reports an error if
the stream ends without a result. Stop aborts the browser request, triggers
harness cancellation, and cleans its temporary authentication.

The original JSON `/tutor` route remains available. OpenRouter's key-filtered
model catalog endpoint is retained for the model picker. A provider failure
still produces explicitly labeled deterministic diagnostic feedback.

## Verification

- `tests/test_opencode_transport.py`: async calls, selected-model forwarding,
  key cleanup, cancellation, sanitized failures, session scoping and tutor
  context boundaries.
- `tests/test_lab_api.py`: checked result/progress events and locked checkpoints.
- `node web/tests/guide-stream.test.cjs`: chunk boundaries, UTF-8, heartbeats,
  error events and truncated streams.

Use a temporary `DATABASE_URL` and `DATA_DIR` for API tests so they do not
create test sessions in the learner database. A live synthetic Nemotron
question returned a checked model answer through OpenCode in 18.5 seconds
with no provider error; no learner workspace was used for this probe.

OpenCode server API documentation: https://opencode.ai/docs/server/

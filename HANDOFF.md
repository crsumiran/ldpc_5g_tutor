# Handoff — updated 2026-10-17

## Latest update
2026-10-20 (LDPC traces + guide rejection): All 18 checkpoints now print each
public call's INPUT, EXPECTED OUTPUT, ACTUAL OUTPUT/exception. Runner copies
active metadata from curriculum/ldpc_5g/public_cases.json and trusted
tests/teaching_conftest.py; pytest -s exposes output on success and failure.
ExecutionPanel automatically opens the trace output for Python runs. Original
assertions, counts and learner functions are unchanged. Author-only generator:
scripts/export_ldpc_public_cases.py; private baseline code is never mounted.
Guide root cause confirmed from stored Nemotron reply: useful diagnosis followed
by a full function triggered the old global-def rejection. Full function blocks
are now omitted, useful prose retained, signatures permitted. No extra AI call
or retry was added. Stored real answer verified with the deployed filter.
121 regressions, three sandbox smokes, browser workflow and all-18 visual smokes,
stream regression and Docker production build passed. API/web rebuilt and
relaunched; learner minsum.py untouched. Rerun tests to see new traces; old run
artifacts and saved guide replies are not retroactively modified.

2026-10-17 (optical-flow course): New course at /?course=optical-flow and
/labs/optical-flow. Five blog-style theory chapters, 12 NumPy TODO assignments,
36 public cases, image/warp/residual explorer and a course-specific guide prompt.
Audience already knows gradients/filtering/edges. Source: curriculum/optical_flow.
The capstone is educational dense pyramidal Lucas–Kanade; no production accuracy
claim. Refinement must translate a whole patch by its CENTER's current vector,
not warp each neighbor independently before fitting one translation.
Generic Python runner now selects the trusted manifest's course ID. Theory,
navigation and chat support multiple Python courses. Flow storage keys are
optical-flow-lab-session / optical-flow-theory-view-v1; LDPC/cache keys and
existing learner work are preserved. No author solution enters learner assets.
Docs: docs/OPTICAL_FLOW_GUIDE.md and docs/OPTICAL_FLOW_TUTORIAL.md. Export via
node scripts/export_optical_flow.mjs (stdout). 94 backend tests and offline
sandbox execution of all 36 cases passed; browser workflow/isolation/mobile
checks and frontend builds passed. Live provider calls were not made.
Temporary browser tooling: /tmp/optical-flow-browser.ZYDlim; no project dependency
was added. Use disposable DATA_DIR/database for all smoke tests.

2026-10-10 (fresh-entry assignment prose): Rewrote all 18 lesson introductions
to define their local problem and terms without previous-reading assumptions.
Removed generic “what changes/stays fixed”, prerequisite recaps, migration
remarks and repeated scope/task boilerplate. Assignment 1 builds from parity
through mask/AND/XOR to GF(2); every page names its actual target function.
LdpcLesson renders the explanation as one article. Prerequisites, code TODOs,
test contracts, fixtures, learner files and grades are unchanged. Current prose
is hydrated from lesson_revisions.json, not the legacy manifest lesson strings.

2026-10-09 (blog-style theory rewrite): User asked for coherent, simple reading
without topic jumps. Rewrote all six main theory narratives. Chapter 5 uses only
the three-bit [+4,-0.2,+3] example in its main story; advanced references are now
TheoryPage.optional_sections. LdpcPrimer renders one article instead of a cell
per section, with visual/reference/address panels collapsed after the article.
docs/LDPC_THEORY_BLOG.md exports only the main story; full review also refreshed.
Assignment IDs/contracts/implementations and learner sessions are unchanged.

2026-10-09 (LDPC detailed revision brief): Delivered Priority 0/1 teaching changes.
18 stable-ID checkpoints, 58 public cases, six expanded beginner theory chapters.
Sources: curriculum/ldpc_5g/lesson_revisions.json and fixtures.json hydrate the
manifest; fixture tables/specifications reach the web and tutor context.
LDPC-18 (min1/min2) unlocks after LDPC-05 without changing the original path.
Missing Python assets migrate additively on session load; never reset an existing
workspace or overwrite saved learner work. All target implementations remain TODOs.
API/web rebuilt and left healthy at http://localhost:3000/?course=ldpc-5g.
77 backend regressions, 3 real-sandbox smokes, both browser smokes, frontend stream
test, typecheck and production build passed. Tests used disposable data and mocked
or unconfigured guide providers, not the learner's session or live AI quota.
Current readable export: docs/LDPC_TUTOR_REVISED_REVIEW.md (reproducible via
node scripts/export_ldpc_review.mjs). Older review is explicitly historical.
docs/LDPC_REVISION_STATUS.md distinguishes completed teaching work from pending
Priority 2/3 real-NR, full fixed-point, BER, decoder scheduling and RTL milestones.

2026-10-08 (chapter 5 readability): Replaced the paragraph-only EvidenceWalk
with `web/src/components/ldpc/DecodingWalk.tsx`, a five-stage visual example.
It starts with plain-language guesses/confidence, shows failed even parity,
draws other-neighbor evidence → check → middle-bit advice, combines fixed radio
scores with rule messages, and checks the revised candidate. Numeric scores are
introduced at the combine stage; Min-Sum arithmetic is optional expandable
material. Rewrote the chapter's six reading sections to match the same example.
Old big-picture panel rated 3/10 for beginner clarity: undefined signed values,
abrupt formula jump, and no actual evidence-flow visual.
Verified 71 backend tests (including independent numeric fixture comparison),
typecheck, production build, 3 stream tests, and extended disposable browser
smoke covering every decoding stage, optional maths, desktop/mobile screenshots,
mobile no-overflow, and saved assignment/code preservation. Web redeployed;
theory JSON served from the existing curriculum mount. No learner state changes.

### Previous update
2026-10-08 (guide response refinement): Fixed Python model prose inheriting
fallback evidence, next-step instructions and end-of-page quiz text. LDPC
responses now use neutral parsing defaults and a formatter that appends only
model-authored legacy JSON fields. Added `backend/prompts/ldpc_tutor.txt` with
answer-first beginner teaching, compound-question coverage, arithmetic/code/
communication distinctions, worked example and silent arithmetic checks.
Added encoder/shared-check-rule explanation to the parity theory page. Kept
one model-call workflow and existing provider controls; no live provider probes
or learner state changes. 70 focused backend tests pass, including prompt and
plain/partial-JSON formatting regressions. Provider quality remains variable;
these tests validate integration, not live answer correctness.

### Previous update
2026-10-08: Added six beginner theory pages before LDPC coding: transmission
errors, redundancy/codewords, parity/syndrome, sparse Tanner graphs, soft-input
message passing, and the 5G/hardware roadmap. Content lives in
`curriculum/ldpc_5g/theory.json`; a dedicated reader has worked diagrams,
interactive repetition/error and decoding examples, revealable questions,
assignment-purpose links, and previous/next/resume navigation. Reading state is
independent of assignment progress (`ldpc-theory-view-v1`). Existing sessions and
learner files are retained. Guide requests can carry a validated theory page ID;
the trusted page replaces coding/run context for theory questions. Model-less
feedback is explicitly authored background, not a claimed tailored answer.
Verified 66 backend tests, 3 frontend stream tests, typecheck/production build,
and browser smoke using disposable data: all six pages, interactive errors,
theory chat, mobile no-overflow, restored reading state, saved code and passed
checkpoint retained, public submit/unlock, and cache course unaffected.

### Previous update
2026-10-07: Implemented the first working Python LDPC course in the same web
tutor, at `/?course=ldpc-5g` (also `/labs/ldpc-5g`). 17 checkpoints and 44 public
checks, original lessons, interactive visuals, Python CodeMirror mode, separate
session storage, snapshot-based offline Python/pytest runner, public reports,
public-only completion/unlocking and Python-specific OpenCode guide context.
No Jupyter dependency. Cache data preserved. This is a foundational toy decoder
and accelerator-thinking course, not full NR decoding: BG1/BG2 fixtures, receiver
plumbing, full fixed-point decoder and cycle model remain explicit milestones.
See `docs/LDPC_GUIDE.md`. Verified 62 focused backend tests, 2 real Docker smokes,
3 frontend stream tests, typecheck and production build. Latest browser/model
verification is recorded in EXPERIMENT_LOG.md.

### Previous update
Integrated a pinned OpenCode 1.18.31 service as the guide runtime. Compose now defaults `TUTOR_ENGINE=opencode`; the existing provider/model/key controls feed an isolated OpenCode tutor agent. The runtime has an empty workspace, denies tools, and stores auth/session/cache files on tmpfs. The bridge serializes credentials, removes them after each request, separates sessions by learner/checkpoint/model/key fingerprint, and restores recent saved chat when a new session is needed. The web page receives live connection/model/retry status and heartbeats, then the answer after existing grounding/leak checks; Stop cancels the request. Both the guide and connection-test button use this runtime. A synthetic exact Nemotron Ultra tutor call succeeded in 18.5 seconds with `source=model`, `engine=opencode` and no provider error. Confirmed credential cleanup and SSE forwarding through the live web proxy. Focused verification: 35 backend tests and 3 frontend stream tests pass; production frontend build/typecheck passed. Learner files, progress and chat were preserved. See `docs/OPENCODE_GUIDE.md` for startup and lifecycle details. Refresh the page to load the new client, then choose Nemotron and ask the guide.

### Previous direct OpenRouter transport diagnosis
Nemotron now fails differently: a synthetic OpenRouter probe using the server key hit the tutor client's 90-second `ReadTimeout`; a North Mini Code synthetic probe succeeded, but API logs also recorded OpenRouter HTTP 429 for that model during tutoring. No learner prompt or RTL was sent in these probes, and the tab-entered key was not read. Added one app-level attempt with the next configured model only when a tutor call ends in `ReadTimeout` and model fallbacks are enabled. Returned 429s are not retried by the app to avoid burning quota. Focused tutor tests pass (19/19); API rebuilt and healthy. Ask the learner to retry Nemotron with the fallback checkbox enabled. OpenRouter's Free plan currently lists a 50-request/day allowance; model/provider 429s can still occur before that limit.

### Previous Nemotron/Cohere test diagnosis
Checked the reported failed model tests using synthetic prompts and the server key. `cohere/north-mini-code:free` succeeds when the connection probe has a sufficient 256-token budget; the old 16-token cap let Cohere spend its response budget on reasoning and return no `content`, which the endpoint incorrectly called success. The test now allows 256 output tokens and rejects empty answers. `nvidia/nemotron-3-ultra-550b-a55b:free` returns HTTP 404 because no provider endpoint matches the server key's guardrails/data policy. The free route exists, but OpenRouter must permit it for the key. Browser-entered keys are not stored or inspectable; test results identify `key_source` on success, and the user should share only the sanitized error text if their entered key still fails.

API rebuilt and healthy. Live exact-route tests: Cohere returned `ok=true`, `served_model=cohere/north-mini-code:free`; Nemotron returned the policy-specific 404 above. Retry Cohere in AI settings. For a direct Nemotron check, turn off model fallbacks so a backup response cannot mask the selected route; the server key will still be rejected until its policy permits that provider.

### OpenRouter request pacing and model picker
Reduced avoidable OpenRouter rate-limit pressure and exposed the requested free routes. Tutor completions are paced to at most one request per 3.2 seconds for each API-key fingerprint, shared across tabs using the same key. The UI blocks duplicate in-flight tutor submits. Malformed model output now causes at most one additional model request per learner question. The connection test is labeled as consuming one request. The OpenRouter free-tier daily allowance is still shared across free model choices and is enforced upstream.

The model picker always includes `qwen/qwen3.8-27b:free` and `nvidia/nemotron-3-ultra-550b-a55b:free`, even when `/models/user` does not list one of those routes. Qwen3.8 is already a configured backup; Nemotron can be selected directly. If a route is omitted from the checked key catalog, the UI warns that its key policy may reject the request but still allows trying the free route. Rebuilt both services; Next production compile/lint/typecheck passed, API is healthy and web is HTTP 200. Refresh http://127.0.0.1:3000 to load the latest picker.

### Tutor JSON response recovery
Fixed the remaining `Guide model unavailable (JSONDecodeError)` path. The network/key connection was healthy, but free models did not reliably obey the tutor's JSON-only instruction: live synthetic probes showed both schema-invalid JSON and a useful plain-text answer despite a structured-output request. Tutor calls now request OpenRouter JSON Schema output with response healing, normalize safe field-type mismatches, preserve a substantial plain-text model answer while filling its evidence/action fields from the deterministic diagnostic, and try another configured model for genuinely malformed output. Short garbage is not accepted, and the existing reset-polarity, waveform-timing, handshake-grounding, and solution-leak guards still run after recovery. User-facing failure text now says “malformed structured response” rather than exposing `JSONDecodeError`.

Deployed and verified with no learner files: the live end-to-end tutor path returned `source=model`, `model=cohere/north-mini-code:free`, and no provider error. Full suite: 80 passed. API is healthy; web remains at http://127.0.0.1:3000. The learner can retry the same question immediately.

### Prior model failover update
Restarted and rebuilt the tutor after tracing the recurring “Guide model unavailable” result. The OpenRouter transport and configured server key are working. The immediate cause was that the selected Gemma free route returned HTTP 429 while an explicit model selection disabled all model-to-model failover; the tutor therefore dropped directly to its local deterministic diagnostic. Changed selected-model behavior so it can try the configured free backup models (unless the learner turns that option off), while still reporting the model that actually served the answer. Added an AI-settings checkbox for this policy and a “Test guide connection” action. The test uses only a synthetic `Reply with exactly OK.` prompt—never learner code—and reports the requested model, served model, whether a backup was used, and whether the browser or server key was used.

Live verification after rebuild: API health is `{"ok":true}`, web is HTTP 200, and the new connection test requested `google/gemma-4-31b-it:free` but successfully received a real response from `cohere/north-mini-code:free`. Full suite: 76 passed; frontend lint, typecheck, and production build passed. Services are running at http://127.0.0.1:3000. Refresh the page, re-enter any browser-only key, leave “Use another configured free model…” enabled, and press “Test guide connection.”

### Prior unavailable-model diagnosis
The learner still received “Guide model unavailable.” The latest saved reply was OpenRouter HTTP 404, not a missing key. A synthetic probe with the configured server key showed Nemotron 3 Ultra free returns “0 endpoints … matching your guardrail restrictions and data policy,” while Gemma models were rate-limited at that moment. OpenRouter's key-filtered `/api/v1/models/user` list contains 11 free models but excludes Nemotron. Added `/api/openrouter/models` to fetch free models allowed for the entered key (no learner prompt sent), a “Check models available to this key” button, a dynamic radio list, and safe actionable 401/402/404/429 provider messages naming the requested model without echoing provider text or secrets. Removed Nemotron from the static/default fallback list and added Cohere North Mini Code and Qwen3.8 27B; a synthetic North Mini Code tutor call returned a model answer. Full suite: 74 passed; frontend lint/typecheck and Docker build passed. Rebuilt API/web; browser check confirmed blocked Nemotron disappears and Cohere can be selected. The web proxy was verified to forward the per-request key using an invalid synthetic key. User must refresh and re-enter key, then run the new check; their key was not retained or tested.

### Prior model selector fix
The initial native `<select>` for the OpenRouter model flashed/disappeared in the learner's browser and remained on the default. Replaced it with always-visible radio choices and a selected-model indicator in both the panel and top bar. Rebuilt the web service. A headless Chromium interaction against the live page selected Gemma 26B and verified that the choice persisted after closing and reopening AI settings. Frontend lint/typecheck and Docker production build passed; API healthy, web running. The learner's key was not read or used during testing. Refresh the browser to load the updated interface.

### OpenRouter key/model feature
The tutor page now has a top-bar AI settings panel: enter an OpenRouter key (held only in tab memory), choose one of three named free models or provide a custom model ID. The browser sends the key in a per-request header only for guide messages, while the model ID is in the tutor request body. The backend uses the override without storing the key, and an explicit model suppresses model-to-model fallbacks. Regression tests verify forwarding, model selection, and absence of the key from response/saved chat. Full suite: 71 passed; frontend lint/typecheck/build successful. API and web were rebuilt, API is healthy, page serves HTTP 200. Refresh the page to load the new controls. Model provider availability is not guaranteed; deterministic tutor feedback remains a fallback.

### Previous CACHE-05 diagnosis
The active learner is on CACHE-05. They changed their controller's reset to active-low (`negedge reset`, `if (!reset)`) while the public testbench starts reset high and releases it low. Consequently the controller repeatedly resets in IDLE during the first read miss and the public testbench waits forever. The latest saved run `61e63e99-776d-4e84-bfed-39ee96689f34` misleadingly recorded 0/0 with `timed_out=false`; its tutor answer from `nex-agi/nex-n2.5-pro:free` incorrectly advised rerunning unchanged. This was fixed: SIGKILL timeout classification, explicit simulation diagnostic, reset-polarity tutor diagnosis and model-answer guard, explicit active-high reset requirement, no-checks UI, and curated free-model fallback. A fresh read-only evaluation of the current learner source reports `timed_out=true`, 0/0, and the new diagnostic. The learner source was not edited. Full suite: 68 passed; frontend lint/typecheck/build successful. API healthy; web serving 200. See newest EXPERIMENT_LOG.md entry.

## Goal
Deliver a production-shaped Jupyter-style Verilog tutoring lab for a direct-mapped cache, with deterministic checkpoint evaluation, safe Docker execution, AI tutoring, and a responsive Next.js UI.

## Current state
- `/home/ranga/opencode/tutor/IMPLEMENTATION_PLAN.md`
- `/home/ranga/opencode/tutor/opensource_tutor_strategy.md`
- `/home/ranga/opencode/tutor/DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md`
- `/home/ranga/opencode/tutor/backend/` (FastAPI app: ingest, analysis, planning, assignments, adapters, eval, tutor, api)
- `/home/ranga/opencode/tutor/sandbox/Dockerfile` + `entrypoint.sh` (de-tutor-sandbox:latest, pytest+pandas+duckdb)
- `/home/ranga/opencode/tutor/web/` (index/mentor/learner + app.js + styles.css)
- `/home/ranga/opencode/tutor/fixtures/python_etl` and `duckdb_pipeline`
- `/home/ranga/opencode/tutor/data/tutor.db` (alembic-migrated)
`curriculum/cache_lab/manifest.json`
`curriculum/cache_lab/starter/`
`curriculum/cache_lab/reference/`
`curriculum/cache_lab/tests/public/`
`curriculum/cache_lab/tests/hidden/`
`backend/app/verilog/runner.py`
`backend/app/verilog/manifest.py`
`backend/app/api/labs.py`
`web/src/app/page.tsx`
`docker-compose.yml`
`backend/Dockerfile`, `web/Dockerfile`, `sandbox/Dockerfile`
`PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q`
`docker compose build` and `docker compose up -d`
`web/src/components/editor/VerilogEditor.tsx`
`npm run lint && npm run typecheck && npm run build`
`docker compose build web` and `docker compose up -d web`
web/src/components/editor/VerilogEditor.tsx
web/src/app/page.tsx
backend/app/verilog/runner.py
curriculum/cache_lab/manifest.json
HANDOFF.md
EXPERIMENT_LOG.md
backend/app/verilog/tutor.py
backend/app/llm.py
backend/app/config.py
docker-compose.yml
.env
.env.example
backend/app/verilog/schemas.py
web/src/lib/contracts.ts
web/src/app/globals.css
tests/test_verilog_manifest.py
RECOVERY_PROMPT.md

## Last action
2026-09-17T07:08 — Created and verified a cross-machine recovery prompt and parameterized Compose with PROJECT_ROOT.

## How to resume
Tomorrow, resume the learner session at CACHE-02, submit it, confirm CACHE-03 is immediately editable, and continue the remaining cache checkpoints.

Last verified by:
docker compose config --quiet -> success
docker compose up -d --force-recreate api web -> API healthy, web running
Disposable API compile through nested Docker sandbox -> done elaboration True
curl http://127.0.0.1:8000/api/health -> {"ok":true}
curl http://127.0.0.1:3000/ -> 200

## Open questions
Locked stack: FastAPI + Docker iverilog sandbox + OpenRouter. AutoGen/OpenHands/Next.js/Hermes deferred to TASK 10-12. Do not let the small model reopen framework choices.
Locked: FastAPI+SQLite+Docker+OpenRouter. Ingest local/git/zip. Partial-algorithm assignments. Python-comfortable learner. Adapters python_pytest then sql_duckdb. dbt/pyspark plan-only until TASK 14. Do not modify IMPLEMENTATION_PLAN.md (Verilog).
Two subtle fixes landed: sandbox PATH needed python3 (not /usr/local/bin/python3) and .env SANDBOX_IMAGE corrected to de-tutor-sandbox. Adapter uses python3 -m pytest inside container. compile_assignment now upserts.窇handle_chat picks most-recent workspace. Do not modify IMPLEMENTATION_PLAN.md.
Docker-in-Docker bind mounts require runner temp directories under the shared data_dir; the web image must bake BACKEND_INTERNAL_URL=http://api:8000. Hidden testbenches are copied individually into a read-only mount. Course slug is cache-lab while its directory is cache_lab. Local MVP intentionally has no authentication. Do not expose the OpenRouter key in .env.
VerilogEditor now initializes from the file value once, lets CodeMirror own local typing state, remounts on selectedFile changes, and uses a Compartment for editable/read-only changes. The running web container was rebuilt.
VerilogEditor now initializes from the file value once, lets CodeMirror own local typing state, remounts on selectedFile changes, and uses a Compartment for editable/read-only changes. The running web container was rebuilt.
Current learner progress is CACHE-02. The CodeMirror corruption fix is complete: CodeMirror owns local document state, file switches remount via key, and editability uses a Compartment. Docker Compose services were rebuilt and left running at http://127.0.0.1:3000. Do not expose the OpenRouter key in .env.
Tutor calls https://openrouter.ai/api/v1/chat/completions using TUTOR_MODEL=openai/gpt-4o-mini when OPENROUTER_API_KEY is set; this is not a :free model route. Missing key or provider failure returns the deterministic fallback tutor. The key was visible in a terminal search during this check, so rotate it if that output is considered exposed. No Ollama route is active.
Active tutor model is google/gemma-4-31b-it:free, confirmed from the current OpenRouter catalog as text+image+video to text with zero listed prompt/completion price. Current lab UI/API sends text, selected code, and structured run data only; selecting a multimodal model does not itself add image upload. OpenRouter free-tier availability and rate limits can change. Rotate the exposed OPENROUTER_API_KEY if needed.
Existing LabSession rows and learner workspaces were not recreated or modified; progress is preserved. Checkpoints now expose description and explicit requirements. CACHE-05 has eight behavioral requirements covering IDLE capture, hit/miss paths, stable memory handshakes, write policies, response state, and reset. The reflection button now sends its actual reflection prompt instead of invoking hint(). After each run, the frontend refreshes both session progress and file editability. Code/editor ligatures are disabled so <= remains two visible characters. One browser reload is needed to download the new frontend bundle.
RECOVERY_PROMPT.md is a copy-paste handoff for another Linux machine. Transfer data/ to preserve SQLite sessions and learner workspaces, but do not transfer .env; create a fresh key. Set PROJECT_ROOT in .env to the new absolute repository path because nested Docker sandbox mounts require identical host/container absolute paths. Current learner state: CACHE-01 submitted; CACHE-02 implementation reportedly finished but not submitted. Browser localStorage key rtl-lab-session must be restored separately when moving machines. Existing local data and progress were not reset.

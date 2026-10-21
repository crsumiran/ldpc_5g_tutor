# Experiment Log

_Append-only, newest at top._

## 2026-10-20 — Public input/expected/actual traces and retained guide explanations

User requested printed examples for every assignment after LDPC-05 guide
failures. Added public-only per-checkpoint expectation metadata and a trusted
pytest wrapper that prints before invoking the learner function, and reports
actual results or exceptions afterward. It wraps every call in all 58 public
cases, including passing, mutation and expected-exception checks. Assertions
still determine grades. Results output opens automatically. No learner edits.

Inspected the already-stored Nemotron answer: it correctly identified chained
advanced-indexing and sign-combination issues, then appended a complete function.
The old def-matching guard discarded the entire response. The new filter omits
complete functions and keeps useful explanation; interface-only answers pass,
while function-only answers still fall back honestly. Verified on the stored
real reply with no new model call. No retries or provider calls added.

Verification: 121 local regressions, three real sandbox tests, browser workflow
(including visible trace panel), all-18-page smoke, guide-stream test and Docker
build passed. An isolated rerun of the learner's unchanged LDPC-05 code printed
all four expected/actual comparisons and reported one passing, three failing.
API/web relaunched with saved sessions preserved. Temporary test API stopped.

## 2026-10-18 — Optical-flow teaching and interaction rewrite

Rewrote all five theory chapters and twelve assignment lessons around worked
mathematics, using the x·y patch for equations, fitting and actual sampled
refinement. Added complete callable references and constructed invocation
examples immediately before each editor. Lessons explain all public checks;
hints and experiments are folded, with repeated notebook boilerplate removed.
Added optional section visual identifiers and nine local interactive diagrams.
Motion/refinement playback supports pause, single step, reset, navigation cleanup
and reduced motion; native controls expose numerical changes and intentional
flat/edge invariance. Scene motion is distinct from proposed flow. Existing
LDPC rendering remains the fallback when section visual metadata is absent.
Numerical explanations remain in tutor context and the refreshed Markdown export.

Verified: 81 selected backend regressions; independent arithmetic checks;
two real-Docker smokes running all 36 unchanged public cases and submit/unlock;
full Chromium audit of nine visuals, every control, five mobile chapters and
twelve mobile assignments; saved code and course isolation; LDPC/cache pages;
zero AI requests from controls; frontend stream regression, lint, typecheck and
production builds. Reviewed desktop/mobile screenshots and aligned image captions
and enlarged reset labels. Live API/course endpoints and frontend return HTTP 200.
Recorded and compared preservation hashes: all 750 existing learner files and
85 session/progress records unchanged. Tests used disposable databases/workspaces.
API/web rebuilt and launched. No live-model quality or general flow accuracy
claim; this remains an educational implementation. Function signatures, public
algorithm checks, prerequisites and learner TODOs are unchanged.

## 2026-10-17 — Optical flow with NumPy

Built and launched optical-flow alongside LDPC and cache. Five continuous theory
chapters assume gradients/filtering/edge knowledge. Twelve learner TODOs cover
derivatives, patch systems, aperture/conditioning, dense small-motion estimates,
bilinear sampling, pull-warping, patchwise refinement, filtered pyramids, vector
upsampling, coarse-to-fine assembly, endpoint error and round-trip consistency.
Contracts state array shapes, direction, units, borders and validity. Added an
interactive supplied image/warp/residual explorer and optical-specific guide
prompt/labels. Sessions and reading position are separate; old learner data was
not reset or edited. The Python runner now reads the requested trusted course ID.

Refinement was checked carefully: every observation in a local fit uses the
center's single current translation. Independently warping neighbors before
fitting a shared translation changes that model and was not retained. Synthetic
truth stays outside estimation. No production accuracy or real-time claim.

Verification: 94 backend tests passed; two real-sandbox smokes executed all 36
public cases and checked TODO failures, submit/unlock and artifacts. Optical-flow
browser checks passed for all five chapters, motion/brightness controls, all
twelve mobile assignment views, saved code and independent course sessions.
Existing LDPC/cache browser flow, stream test, typecheck and production builds
passed. Model-context checks used mocked providers; no live AI calls or quota
were used. API healthy, page HTTP 200, friendly route HTTP 307; API/web left up.
Temporary browser-test API stopped. Export: docs/OPTICAL_FLOW_TUTORIAL.md;
maintenance/limits: docs/OPTICAL_FLOW_GUIDE.md.

## 2026-10-10 — Fresh-entry assignment explanations

Removed repeated revision boilerplate from all 18 lessons, including “what
changes and what stays fixed” and prerequisite-recap sections. Each assignment
introduces its local problem and notation before the worked example, and names
the target function in its task. Assignment 1 starts with bits/transmission,
then parity, mask, AND, XOR and GF(2). Assignment explanations render as one
article; optional depth and exercises remain available. No checkpoint/test
contract, starter TODO, fixture, learner file or grade was changed.

Verification: 78 backend regressions, web production build, workflow browser
smoke and all-18-visual/mobile smoke passed. Tests used disposable data and no
live model calls. Live API confirmed 18 lessons with no removed boilerplate
and the new first sentence. Review export refreshed. Web rebuilt/relaunched;
temporary browser-test API stopped, production API/web left running.

## 2026-10-09 — Continuous beginner reading

Rewrote all six theory chapters in blog-style prose after feedback about topic
jumps and fragmented panels. Chapter 5 follows only the three-bit confidence
example through rule advice, combining and checking. Original deeper material
is preserved in optional reference panels. Main reading renders as one article,
not numbered cells. Optional panels reset closed when changing chapters.
Assignments and learner state are unchanged. Main-only export:
docs/LDPC_THEORY_BLOG.md; full review refreshed with optional material labeled.
77 backend regressions, production build and both browser smokes passed.
Live API reports five main sections and four optional references in chapter 5.
Browser checks cover reading flow, mobile fit, saved work and all assignment
visuals using disposable data; the temporary test API was stopped afterward.

## 2026-10-09 — LDPC detailed brief, foundation revision

Implemented terminology/NumPy preparation, toy encoding, stable linked edges,
AWGN→LLR, state/exclusion tables, two-round flooding, wrong-valid/capped outcomes,
two-layer traces, rotation/gather/scatter and full QC expansion. Added operation-
specific visuals, controlled variants, progressive hints, optional depth and
hardware storage/issue/service examples. New LDPC-18 targets two minima/sign parity
without providing learner implementations. Original grades and files are preserved;
new workspace files are added exclusively, never overwritten.

Verification: 77 backend checks passed, including independent recomputation of
displayed arithmetic; 18 author-only baselines execute all 58 public cases.
3 opt-in real-Docker smokes passed; six-page workflow and all-18-visual browser
smokes passed with disposable API data; the latter made zero model requests.
Frontend stream regression, typecheck and production build passed. API/web rebuilt
and healthy; disposable browser API stopped. No live provider quality claim made.
Review export and delivered/pending map are in docs/LDPC_TUTOR_REVISED_REVIEW.md
and docs/LDPC_REVISION_STATUS.md. Priority 2/3 remains unfinished, not rebranded
as completion of the full NR/accelerator outcomes.

## 2026-10-08 — Chapter 5 beginner decoding walkthrough

Reviewed the old big-picture panel and rated it 3/10 for a learner without LDPC
background. It introduced signed scores and Min-Sum without enough context,
and its buttons only changed dense paragraphs. Replaced it with five visible
stages: radio clues, failed rule, other-bit advice, revised guess, recheck.
Bit cards show guess/confidence, a diagram shows the source/destination of a
rule message, and the combine view separates unchanged radio evidence from
updated scores. Numerical convention is introduced at the point of use, with
the calculation method in optional maths. The accompanying prose is rewritten
around the same fixture; it explains messages are decoder computations, not
new transmitted signals, and that a rule failure cannot identify a guilty bit.

Verification: 71 focused backend tests, TypeScript typecheck, production build,
3 frontend stream tests, and disposable end-to-end browser smoke passed.
Independent baseline confirms channel [4,-0.2,3], outgoing messages
[-0.2,3,-0.2], posterior [3.8,2.8,2.8], and final guesses [0,0,0]. Browser
checks all five stages, optional maths visibility, fixed channel/revised score,
desktop/mobile no-overflow, grade/code preservation, and intact cache course.
Inspected `/tmp/ldpc-decoding-advice.png`, `/tmp/ldpc-decoding-desktop.png` and
`/tmp/ldpc-decoding-mobile.png`. No model calls or real learner-session mutations.

## 2026-10-08 — Direct beginner answers without fallback footer contamination

The learner's example exposed a real formatting bug: plain model replies were
copied onto the fallback object, inheriting its theory quiz and unrelated model
configuration instruction. Python model replies now parse with neutral fields,
and natural prose gets just its model attribution and body. Legacy partial JSON
remains supported without local defaults appearing as model-authored advice.
A separate authored prompt asks for direct coverage of all question parts,
missing prerequisites, checked worked examples, and communication context rather
than copied page evidence or mandatory Socratic quizzes. Added the explanation
of agreed rules and transmitted parity bits to the parity theory page.

70 focused backend tests passed in disposable storage. New regression cases
cover the learner's compound GF(2) question, clean natural prose, partial JSON,
mathematical braces, malformed JSON fallback, and no added review calls.
No live provider probe was made; answer quality still depends on the model.
No learner code, progress, key settings or chat history were rewritten.

## 2026-10-08 — Beginner LDPC theory before assignments

Added six authored theory pages with basic definitions, worked visuals,
repetition-code error toggles, a four-step soft-evidence example, understanding
questions, and links to every assignment's purpose. Theory pages are ungraded;
they neither reset nor unlock tasks. Existing learner state is preserved.
The guide receives validated server-authored theory context instead of stale
coding diagnostics; no-model fallback is labeled as non-tailored background.
The 5G paragraph links the pinned ETSI TS 138 212 V17.9.0 primary source and
distinguishes toy examples from full NR implementation.

Verification: 66 focused backend tests, 3 frontend stream tests, TypeScript
typecheck, production frontend build, and a real browser smoke passed.
Browser requests were routed to disposable backend data; demonstrated all six
theory pages, repetition failure with two flips, answer reveals, page restore,
theory guide fallback, code and passed-grade preservation, public test/submit,
next-task unlocking, mobile no-overflow, and intact cache route. Screenshots:
`/tmp/ldpc-theory-desktop.png` and `/tmp/ldpc-theory-mobile.png`.
No real provider calls were needed; the model theory-context path is mocked in
tests, and the browser checks transparent offline feedback, not live model quality.

## 2026-10-07 — Launched Python LDPC tutor in the cache-style web UI

Implemented 17 Python checkpoints / 44 named public cases, lesson text and
interactive provided visuals, Python editor mode, independent session storage,
fresh offline execution, immutable saved-source snapshots, report downloads,
public-only completion and Python-specific OpenCode context. Cache course/state
retained. No Jupyter. Explicit scope: toy decoder / verified lifting sets /
fixed-point primitives / lane and bank models, not full NR decoding or RTL.

Verification: 62 focused backend tests and 2 real Docker/API smokes passed in
temporary storage; 3 frontend stream tests passed; typecheck and production
build passed. All 44 public fixtures were checked against independent author
baselines outside learner assets. Real Docker smoke demonstrated TODO failures,
passing submission, next-checkpoint unlock, syntax failure, snapshot preservation,
provided NR lifting assets, and authorized public report download.

Browser smoke through deployed Next.js with API traffic redirected to a separate
temporary API passed: bit flip changes syndrome, Python typing, failing checks,
passing Submit, next checkpoint, guide fallback, desktop/mobile screenshot and
cache route. No real learner database was used for browser checks. Screenshots
were inspected. Source save before run/guide covers all editable dependencies.

A single synthetic model probe (no learner code or saved chat) reached the
native OpenCode bridge but OpenRouter returned HTTP 429 after 78.6 seconds.
The response was explicitly labeled local feedback. Model success is NOT claimed
for this launch; provider quota/access remains external. Confirmed temporary
OpenRouter credential absent after cleanup. User may enter their own key/select
a model using existing AI settings. Do not repeat probes automatically.

Launched URL: http://localhost:3000/?course=ldpc-5g
Runbook and remaining milestones: docs/LDPC_GUIDE.md.

---

## 2026-09-30 — Integrated OpenCode as the guide runtime

Added the isolated `opencode` Compose service (pinned 1.18.31), a Python bridge
using its asynchronous HTTP session API, and a custom tutor agent with tools
denied. The harness mounts no learner repository or host credential files;
runtime data lives on tmpfs. Entered/server keys are serialized, scoped to each
request, removed afterward, and cached provider instances disposed. Sessions
are separated by learner, checkpoint, selected model and key fingerprint.
New sessions receive recent saved chat for context restoration.

The tutor and connection-test endpoint now use OpenCode when deployed through
Compose. The UI consumes progress/retry events and heartbeats, displays the
checked final answer, and supports Stop. Existing grading, waveform grounding,
reference-leak checks and saved learner state remain in the tutor application.

Verification: 35 focused backend tests, 3 frontend stream tests, TypeScript
check and Next production build passed. A live synthetic Nemotron Ultra
question returned `source=model`, `engine=opencode`, the exact requested free
model, and no provider error in 18.5 seconds. Its answer correctly distinguished
write request acceptance from completion. No learner code or saved learner
question was replayed. Confirmed that the temporary OpenRouter credential was
absent after completion, and that SSE progress/error frames cross the web proxy.
Implementation/lifecycle notes are in `docs/OPENCODE_GUIDE.md`.

---

## 2026-09-30 — Add tutor fallback after a stalled model response

Current server-key probes found two different upstream issues: a synthetic `cohere/north-mini-code:free` connection probe returned successfully, while a synthetic `nvidia/nemotron-3-ultra-550b-a55b:free` probe ended in `ReadTimeout` at the tutor client's 90-second limit. API logs also contained an OpenRouter 429 for North Mini Code during a tutor request. These are provider/account availability failures rather than the previous Next.js 30-second proxy disconnect; the web proxy timeout is already 210 seconds.

The tutor now makes one application-level attempt with the next configured free model if a call ends in `httpx.ReadTimeout` and fallbacks are enabled. It does not issue an extra retry for HTTP 429 responses. Added regression coverage for timeout fallback and for not retrying a 429. Focused suite: 19 passed. Rebuilt/restarted API; health endpoint returns `{"ok":true}`. The synthetic probes consume OpenRouter requests; no learner files or browser-entered key were used. OpenRouter currently advertises 50 requests/day on its [Free plan](https://openrouter.ai/pricing); provider-specific 429s and slow routes can still happen.

---

## 2026-09-28 — Fixed tutor requests cut off by Next.js proxy timeout

The learner reported HTTP 500 only when asking the guide with Nemotron, even though the exact Nemotron connection probe and a synthetic structured tutor call had succeeded. Recent web logs showed `ECONNRESET` on `/tutor`; API logs showed the service stayed healthy. Next.js 14's rewrite proxy defaults to a 30-second timeout, shorter than the OpenRouter client's 90-second wait (and one structured-response retry), so long tutor responses were disconnected and surfaced as 500.

Set `experimental.proxyTimeout` to 210 seconds in `web/next.config.mjs`. Next production build passed and recognized the setting. Recreated only the web container from the built image; API is healthy and `http://127.0.0.1:3000/` returns HTTP 200. No learner prompt, source code, or browser-entered API key was replayed. Ask the learner to retry Nemotron in the existing tab.

---

## 2026-09-27 — Confirmed Nemotron Ultra works after key policy update

After the learner updated OpenRouter settings, the exact synthetic connection check for `nvidia/nemotron-3-ultra-550b-a55b:free` succeeded with `fallback_used=false` and `key_source=server`. A second synthetic request passed through the actual structured tutor response path with model fallback disabled; it returned `source=model`, the Nemotron model ID, and no provider error. The free endpoint took about 19 seconds for the structured tutor answer. No learner files or prompts were sent.

---

## 2026-09-27 — Fixed false success in short Cohere probe; confirmed Nemotron key restriction

The learner reported that Nemotron and Cohere failed in “Test guide connection.” Exact synthetic requests through the server key identified two distinct causes. Nemotron free returned OpenRouter HTTP 404 because the server key's guardrails/data policy matched no provider endpoint. Cohere North Mini Code did return HTTP 200, but with the previous 16-token test budget its `content` was null: the model used the tiny budget on its reasoning field. The connection-test endpoint incorrectly treated that as success.

Raised the synthetic test budget to 256 output tokens and made the endpoint reject responses with empty answer text. Rebuilt API. Live post-deploy exact checks: Cohere returned `ok=true`, served by `cohere/north-mini-code:free`; Nemotron produced the actionable 404 policy message. No learner prompt or source was sent. Browser-entered user keys remain tab-only and were not read.

---

## 2026-09-27 — Pacing OpenRouter calls and exposing Qwen3.8/Nemotron free routes

Added a per-API-key OpenRouter request pacer with a default 3.2-second minimum interval (about 18.75 requests/minute from this app). Duplicate in-flight tutor sends are blocked in the browser. Malformed structured output now gets at most one application-level retry on another configured model. Rate-limit messages include `Retry-After` when the provider supplies it. The limiter uses a SHA-256 key fingerprint for in-memory scheduling and never stores or logs the API key.

Kept Qwen3.8 27B (free) and added Nemotron 3 Ultra (free) as always-visible featured choices, even when OpenRouter's key-filtered catalog omits them. Selecting either route is allowed; the UI warns when the checked key does not list it so account guardrails remain visible. Qwen stays in configured backup routes. Nemotron is selectable directly but is not sent as a default backup because the server key's catalog previously excluded it under its policy.

Rebuilt API and web. Next production build passed compilation, lint, and type checking. Compose reports API healthy and web running; API health is `{"ok":true}` and page is HTTP 200. No live completion or learner code was sent for this change.

---

## 2026-09-27 — Recovered malformed and plain-text model replies

The learner still saw `Guide model unavailable (JSONDecodeError)` even though “Test guide connection” succeeded. API logs confirmed that the short OpenRouter transport probe worked and the failure occurred while decoding the full tutor answer. Synthetic live requests reproduced two free-model behaviors: schema-invalid JSON and a useful plain-text response despite requesting structured output.

Tutor requests now use OpenRouter JSON Schema response format plus the response-healing plugin. The parser safely normalizes evidence strings, invalid categories, missing explanatory fields, and hint-level types against the deterministic diagnostic. A substantial plain-text answer is retained as the model summary with deterministic evidence and next actions; short garbage or malformed JSON causes an application-level retry on another configured model. Existing evidence-grounding and solution-leak guards still validate the recovered result. Final failures report a malformed structured response rather than the implementation-level `JSONDecodeError`.

Verified: 80 Python tests passed. Rebuilt the API; Compose reports it healthy. A live end-to-end synthetic tutor call with no learner files returned `source=model`, `model=cohere/north-mini-code:free`, no provider status, and a direct answer distinguishing request acceptance from operation completion.

---

## 2026-09-27 — Restored real-model failover and added a safe live connection test

Restarted the tutor and reproduced the OpenRouter behavior with synthetic prompts only. The configured server key and chat-completions transport work. Gemma 4 31B, Gemma 4 26B, and Qwen3.8 27B free routes returned HTTP 429 during the check, while Cohere North Mini Code returned HTTP 200. The default tutor path already reached Cohere, but choosing an explicit model passed an empty fallback list and therefore dropped straight to the local deterministic guide whenever that selected free route was rate-limited.

Selected models now retain their priority while optionally trying the other configured free models before using the local diagnostic. This is enabled by default and can be disabled with the new AI-settings checkbox. Added `POST /api/openrouter/test` and a “Test guide connection” button; it sends only `Reply with exactly OK.`, does not store a chat, and reports requested model, served model, fallback use, and key source without returning a key. Also added a small response-token limit for this probe and a bounded tutor response limit.

Verified: 76 Python tests passed; frontend lint, typecheck, and production build passed. Rebuilt API/web; containers are healthy/running, API health is `{"ok":true}`, and web returns HTTP 200. The live synthetic connection test requested `google/gemma-4-31b-it:free` and succeeded via `cohere/north-mini-code:free` with `fallback_used=true` and `key_source=server`. No learner RTL was sent during the connection tests.

---

## 2026-09-20 — Diagnosed unavailable guide model and added key-specific model checks

The learner's latest stored tutor reply reported OpenRouter HTTP 404. Synthetic provider probes with the server key showed Nemotron 3 Ultra free had no endpoint matching the account's guardrails/data policy; Gemma free routes returned 429 at that moment. The key-filtered OpenRouter model list showed 11 permitted free models and excluded Nemotron. The learner-entered key is intentionally not stored, so its exact restrictions were not inspected.

Added a key-specific free-model check endpoint and AI-settings button, with a dynamic list of permitted models. The guide now reports safe actionable provider error categories and the selected model instead of only an HTTP code. Replaced the unavailable Nemotron default fallback with Cohere North Mini Code and Qwen3.8 27B. A synthetic North Mini Code tutor request returned `source=model` without learner files.

Verified: 74 Python tests pass; frontend lint/typecheck and Docker production build pass. Rebuilt API/web. Through the live web proxy, the server-key model check returned 11 allowed free models; an invalid synthetic browser key returned a sanitized 401, proving header forwarding. Headless Chromium confirmed the model-check button removed blocked Nemotron and allowed selecting Cohere. No learner source or entered key was sent during verification.

---

## 2026-09-20 — Repaired browser model selection

The learner reported that the native model dropdown flashed or disappeared and remained on the fallback selection. Replaced the native popup selector with persistent, accessible radio choices; the AI settings panel and top bar both show the selected model. The panel scrolls on short screens. Rebuilt the web service without touching the learner's key or RTL.

Verified frontend lint and typecheck, Docker production build, and healthy Compose services. A headless Chromium check against the live page clicked Gemma 26B and confirmed that the checked radio, selected-model heading, and top-bar label updated, then remained selected after closing and reopening AI settings.

---

## 2026-09-20 — Added per-tab OpenRouter key and model selection

Added an AI settings panel at the top of the lab page. A learner can enter an OpenRouter key and select Gemma 4 31B, Gemma 4 26B A4B, Nemotron 3 Ultra (all named free routes), or enter a custom model ID. The key lives only in React tab memory until refresh and is sent in `X-OpenRouter-Api-Key` for tutor requests only; it is not included in the tutor request body, response, or saved chat. An explicit model disables model-to-model fallbacks so the selected model is honored, while local evidence-based feedback remains if the provider fails. Custom models require the learner's key because they may incur charges.

Verified: 71 Python tests passed, including per-request key/model forwarding and key non-persistence; frontend lint, typecheck, and production build passed. Rebuilt API and web containers; API health `{"ok":true}`, web HTTP 200. Did not send the learner's code or key to OpenRouter during verification.

---

## 2026-09-20 — CACHE-05 zero-check timeout and tutor grounding

The learner's current controller uses active-low reset, but the public testbench holds reset low while exercising `read_miss`. The controller remains in its reset branch, and the testbench blocks waiting for `cpu_resp_valid`. The saved run had no named checks after 32 seconds but was marked `timed_out=false` because GNU `timeout --signal=KILL` exits 137.

Changed the sandbox to classify a near-deadline exit 137 as a timeout, and the runner to add a public simulation-timeout diagnostic. The CACHE-05 tutor now compares source and public testbench reset polarity for a zero-case stalled run, gives line-specific evidence, and rejects model replies that ignore or contradict this diagnosis. The CACHE-05 requirements now explicitly state that reset is active-high. The frontend labels 0/0 as incomplete. Replaced the random `openrouter/free` last-resort fallback with the named free Nemotron 3 Ultra route. Did not modify the learner's RTL.

Verified: 68 Python tests pass; frontend lint, typecheck, and build pass. Read-only evaluation of the learner source: `stage=simulation`, `timed_out=true`, `runtime_ms=31533`, `passed=0`, `failed=0`, with the explicit timeout diagnostic. Rebuilt API and web containers; API health returned `{"ok":true}` and web returned HTTP 200. The live tutor model call was not repeated, to avoid adding learner messages or sending their source externally during verification.

---

## 2026-09-20T14:44 — Corrected CACHE-05 response sampling and made tutor feedback evidence-aware.

**Artifacts:** `curriculum/cache_lab/tests/public/tb_controller.v`, `curriculum/cache_lab/tests/hidden/tb_controller_hidden.v`, `backend/app/verilog/waveform.py`, `backend/app/verilog/tutor.py`, `backend/app/api/labs.py`, `backend/app/llm.py`, `backend/app/config.py`, `.env.example`, `tests/test_verilog_tutor.py`.

**Verified:** Full suite: 64 passed. Read-only public run of current learner CACHE-05 workspace after checker correction: read_miss, read_hit, write_hit pass; write_through fails. API healthy and web running after API rebuild. Minimal OpenRouter request with free fallback models succeeded; the earlier real tutor request had received HTTP 429 and silently used a generic fallback.

**Next:** Learner should rerun CACHE-05 public tests in the UI, then examine why the write-through memory request carries zero write data. Do not edit the learner's solution on their behalf.

**Notes:** Prior public and hidden controller checkers sampled one-cycle response data after valid had dropped. Both now sample during the valid pulse. Tutor now sees the latest public run after reload, a bounded public VCD response summary, current public testbench, and whether code/checker changed since that run. Model replies identify the serving model; fallbacks disclose provider failure and give grounded timing/write-through feedback. No learner workspace or progress rows were modified.

---


## 2026-09-17T07:08 — Created and verified a cross-machine recovery prompt and parameterized Compose with PROJECT_ROOT.

**Artifacts:**
RECOVERY_PROMPT.md
docker-compose.yml
.env.example
HANDOFF.md
EXPERIMENT_LOG.md

**Verified:**
docker compose config --quiet -> success
docker compose up -d --force-recreate api web -> API healthy, web running
Disposable API compile through nested Docker sandbox -> done elaboration True
curl http://127.0.0.1:8000/api/health -> {"ok":true}
curl http://127.0.0.1:3000/ -> 200

**Next:**
Tomorrow, resume the learner session at CACHE-02, submit it, confirm CACHE-03 is immediately editable, and continue the remaining cache checkpoints.

**Notes:**
RECOVERY_PROMPT.md is a copy-paste handoff for another Linux machine. Transfer data/ to preserve SQLite sessions and learner workspaces, but do not transfer .env; create a fresh key. Set PROJECT_ROOT in .env to the new absolute repository path because nested Docker sandbox mounts require identical host/container absolute paths. Current learner state: CACHE-01 submitted; CACHE-02 implementation reportedly finished but not submitted. Browser localStorage key rtl-lab-session must be restored separately when moving machines. Existing local data and progress were not reset.

---


## 2026-09-15T11:49 — Expanded every cache checkpoint contract and fixed reflection, Verilog ligature, and post-submit editor-transition defects.

**Artifacts:**
curriculum/cache_lab/manifest.json
backend/app/verilog/schemas.py
web/src/lib/contracts.ts
web/src/app/page.tsx
web/src/app/globals.css
tests/test_verilog_manifest.py
HANDOFF.md
EXPERIMENT_LOG.md

**Verified:**
PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q -> 57 passed
npm run lint && npm run typecheck && npm run build -> successful
Live API submit transition -> CACHE-01 passed=True and CACHE-02 editable=True
Headless Firefox -> requirement list rendered and editor fontVariantLigatures=none
docker compose ps -> API healthy and web running

**Next:**
Continue from the learner current checkpoint; after one reload to obtain this deployment, verify submission advances to an editable next file without another refresh and review the expanded CACHE-05 FSM contract.

**Notes:**
Existing LabSession rows and learner workspaces were not recreated or modified; progress is preserved. Checkpoints now expose description and explicit requirements. CACHE-05 has eight behavioral requirements covering IDLE capture, hit/miss paths, stable memory handshakes, write policies, response state, and reset. The reflection button now sends its actual reflection prompt instead of invoking hint(). After each run, the frontend refreshes both session progress and file editability. Code/editor ligatures are disabled so <= remains two visible characters. One browser reload is needed to download the new frontend bundle.

---


## 2026-09-15T07:56 — Routed the tutor to OpenRouter free multimodal Gemma and relaunched the API with the new model.

**Artifacts:**
backend/app/config.py
.env
.env.example
backend/app/llm.py
backend/app/verilog/tutor.py
HANDOFF.md
EXPERIMENT_LOG.md

**Verified:**
docker compose exec -T api python -c "from app.config import settings; print(settings.tutor_model)" -> google/gemma-4-31b-it:free
curl http://127.0.0.1:8000/api/health -> {"ok":true}
PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q -> 57 passed

**Next:**
If image-based tutoring is required, add a bounded image-upload field to TutorRequest and include it as an OpenRouter image content part.

**Notes:**
Active tutor model is google/gemma-4-31b-it:free, confirmed from the current OpenRouter catalog as text+image+video to text with zero listed prompt/completion price. Current lab UI/API sends text, selected code, and structured run data only; selecting a multimodal model does not itself add image upload. OpenRouter free-tier availability and rate limits can change. Rotate the exposed OPENROUTER_API_KEY if needed.

---


## 2026-09-15T07:49 — Relaunched the Compose stack and confirmed the tutor uses OpenRouter with the configured non-free gpt-4o-mini route.

**Artifacts:**
backend/app/verilog/tutor.py
backend/app/llm.py
backend/app/config.py
docker-compose.yml
HANDOFF.md
EXPERIMENT_LOG.md

**Verified:**
docker compose up -d --force-recreate -> API healthy and web running
curl http://127.0.0.1:8000/api/health -> {"ok":true}
curl http://127.0.0.1:3000/ -> 200

**Next:**
Continue the remaining CACHE-02 experiments with the relaunched services.

**Notes:**
Tutor calls https://openrouter.ai/api/v1/chat/completions using TUTOR_MODEL=openai/gpt-4o-mini when OPENROUTER_API_KEY is set; this is not a :free model route. Missing key or provider failure returns the deterministic fallback tutor. The key was visible in a terminal search during this check, so rotate it if that output is considered exposed. No Ollama route is active.

---


## 2026-09-04T05:23 — Checkpointed the cache lab after the editor fix; learner has progressed to CACHE-02.

**Artifacts:**
web/src/components/editor/VerilogEditor.tsx
web/src/app/page.tsx
backend/app/verilog/runner.py
curriculum/cache_lab/manifest.json
HANDOFF.md
EXPERIMENT_LOG.md

**Verified:**
User confirmed the editor issue is fixed and reported moving to the second assignment checkpoint (CACHE-02).
PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q -> 57 passed
npm run lint && npm run typecheck && npm run build -> successful

**Next:**
Resume at CACHE-02 by inspecting the current tag-array editor state, then run its public tests and verify the submit/hidden-test flow before making further changes.

**Notes:**
Current learner progress is CACHE-02. The CodeMirror corruption fix is complete: CodeMirror owns local document state, file switches remount via key, and editability uses a Compartment. Docker Compose services were rebuilt and left running at http://127.0.0.1:3000. Do not expose the OpenRouter key in .env.

---


## 2026-09-04T04:47 — Fixed CodeMirror cursor corruption by removing per-keystroke document replacement and preserving editor instances per file.

**Artifacts:**
`web/src/components/editor/VerilogEditor.tsx`
`web/src/app/page.tsx`
`npm run lint && npm run typecheck && npm run build`
`docker compose build web` and `docker compose up -d web`

**Verified:**
`npm run lint && npm run typecheck && npm run build` -> lint clean, typecheck clean, production build successful
`PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q` -> `57 passed`
`curl http://127.0.0.1:3000/` -> `200`

**Next:**
Reload the lab in the browser and type `addr[7:4]` in the CACHE-01 code cell; verify the cursor stays in place, then test switching tabs and checkpoints.

**Notes:**
VerilogEditor now initializes from the file value once, lets CodeMirror own local typing state, remounts on selectedFile changes, and uses a Compartment for editable/read-only changes. The running web container was rebuilt.

---


## 2026-09-04T04:47 — Fixed CodeMirror cursor corruption by removing per-keystroke document replacement and preserving editor instances per file.

**Artifacts:**
`web/src/components/editor/VerilogEditor.tsx`
`web/src/app/page.tsx`
`npm run lint && npm run typecheck && npm run build`
`docker compose build web` and `docker compose up -d web`

**Verified:**
`npm run lint && npm run typecheck && npm run build` -> lint clean, typecheck clean, production build successful
`PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q` -> `57 passed`
`curl http://127.0.0.1:3000/` -> `200`

**Next:**
Reload the lab in the browser and type  in the CACHE-01 code cell; verify the cursor stays in place, then test switching tabs and checkpoints.

**Notes:**
VerilogEditor now initializes from the file value once, lets CodeMirror own local typing state, remounts on selectedFile changes, and uses a Compartment for editable/read-only changes. The running web container was rebuilt.

---


## 2026-09-03T11:06 — Completed and container-verified the direct-mapped cache Verilog lab stack.

**Artifacts:**
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

**Verified:**
`PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q` -> `57 passed in 14.46s`
`npm run lint && npm run typecheck && npm run build` -> successful
Live Compose submission -> `CACHE-01`: public `5` passed, hidden `256` passed, hidden cases redacted

**Next:**
Perform browser-level responsive QA against http://127.0.0.1:3000 and then address any UI defects found.

**Notes:**
Docker-in-Docker bind mounts require runner temp directories under the shared data_dir; the web image must bake BACKEND_INTERNAL_URL=http://api:8000. Hidden testbenches are copied individually into a read-only mount. Course slug is cache-lab while its directory is cache_lab. Local MVP intentionally has no authentication. Do not expose the OpenRouter key in .env.

---


## 2026-08-20T18:59 — Implemented the Data Engineering Tutor MVP (TASK 00-13): ingest/analyze/plan/compile/workspace/sandbox-eval/tutor/API/UI, all 37 tests passing, site served live.

**Artifacts:**
- `/home/ranga/opencode/tutor/backend/` (FastAPI app: ingest, analysis, planning, assignments, adapters, eval, tutor, api)
- `/home/ranga/opencode/tutor/sandbox/Dockerfile` + `entrypoint.sh` (de-tutor-sandbox:latest, pytest+pandas+duckdb)
- `/home/ranga/opencode/tutor/web/` (index/mentor/learner + app.js + styles.css)
- `/home/ranga/opencode/tutor/fixtures/python_etl` and `duckdb_pipeline`
- `/home/ranga/opencode/tutor/data/tutor.db` (alembic-migrated)

**Verified:**
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q  ->  37 passed in 6.89s

**Next:**
Live-run the full LLM pipeline with a real OPENROUTER_API_KEY: import a repo, generate plan, compile assignment, tutor a submission. Optional TASK 14 e2e once stable.

**Notes:**
Two subtle fixes landed: sandbox PATH needed python3 (not /usr/local/bin/python3) and .env SANDBOX_IMAGE corrected to de-tutor-sandbox. Adapter uses python3 -m pytest inside container. compile_assignment now upserts.窇handle_chat picks most-recent workspace. Do not modify IMPLEMENTATION_PLAN.md.

---


## 2026-08-20T18:17 — Wrote DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md as a locked, task-sliced runbook for a coding model.

**Artifacts:**
- `/home/ranga/opencode/tutor/DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md`

**Verified:**
test -f /home/ranga/opencode/tutor/DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md && wc -l /home/ranga/opencode/tutor/DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md

**Next:**
Feed a coding model: Read DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md and do ONLY TASK 00.

**Notes:**
Locked: FastAPI+SQLite+Docker+OpenRouter. Ingest local/git/zip. Partial-algorithm assignments. Python-comfortable learner. Adapters python_pytest then sql_duckdb. dbt/pyspark plan-only until TASK 14. Do not modify IMPLEMENTATION_PLAN.md (Verilog).

---

## 2026-08-16T09:21 — Wrote a locked, task-sliced IMPLEMENTATION_PLAN.md so a smaller model can implement the tutor one TASK at a time.

**Artifacts:**
- `/home/ranga/opencode/tutor/IMPLEMENTATION_PLAN.md`
- `/home/ranga/opencode/tutor/opensource_tutor_strategy.md`

**Verified:**
test -f /home/ranga/opencode/tutor/IMPLEMENTATION_PLAN.md && wc -l /home/ranga/opencode/tutor/IMPLEMENTATION_PLAN.md

**Next:**
Feed a small model: Read IMPLEMENTATION_PLAN.md and do ONLY TASK 00.

**Notes:**
Locked stack: FastAPI + Docker iverilog sandbox + OpenRouter. AutoGen/OpenHands/Next.js/Hermes deferred to TASK 10-12. Do not let the small model reopen framework choices.

---

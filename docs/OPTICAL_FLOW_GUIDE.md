# Optical-flow tutor

Open http://localhost:3000/?course=optical-flow or /labs/optical-flow.

Five blog-style theory chapters assume familiarity with gradients, filtering
and edges. Twelve bounded NumPy assignments lead to dense pyramidal Lucas–Kanade
flow and diagnostics, with exact shape/direction/border contracts, three hints,
worked examples, experiments and public checks. This is not a Jupyter notebook:
Python source is edited and saved through the existing tutor page.

Nine section-local demonstrations cover correspondence, patch equations,
flat/edge/corner ambiguity, bilinear weights, proposed lookup, refinement,
pyramid units, evaluation masks and forward/backward paths. The analytic x·y
patch connects the prose, tables and visuals. Scene motion and proposed flow
are separate controls; selected coordinates expose numerical values. Flat and
edge invariance is explained beside the controls. Motion and refinement have
play/pause, single-step and reset; navigation cleans up timers and state.
Reduced-motion preference disables playback while retaining manual steps.
Native controls support keyboard access. These are supplied demonstrations,
separate from learner output; no model requests come from controls.

## Assignment path

1. Floating spatial/temporal derivatives and motion-equation signs.
2. A patch as N equations for two unknowns.
3. Checked least squares, normalized eigenvalues and the aperture problem.
4. Dense one-step estimates with a separate validity mask.
5. Bilinear interpolation and the closed image domain.
6. Forward-flow pull-warping and invalid destinations.
7. Patchwise iterative translation refinement.
8. Reflected five-tap filtering before factor-two reduction.
9. Interpolating flow and doubling displacement units.
10. Coarse-to-fine dense Lucas–Kanade assembly.
11. Masked endpoint error and evaluation coverage.
12. Forward/backward consistency at displaced destinations.

In assignment 7, an entire patch uses its center's current translation. Do not
sample different neighbors using their independent dense vectors before fitting
one patch translation; that silently changes the stated local model. Keep the
reference gradients fixed and sample the original target image each round.

## Isolation and limitations

Uses the existing offline NumPy sandbox and OpenCode chat harness with an
optical-flow-specific prompt. The prompt includes coordinate, shape and validity
conventions and asks for direct multipart answers and evidence-based debugging.
No live provider quality or availability is promised; without a working model,
the page labels its authored fallback. Provider settings are shared as before.

Session key: optical-flow-lab-session. Reading key: optical-flow-theory-view-v1.
LDPC's ldpc-lab-session / ldpc-theory-view-v1 and cache's rtl-lab-session remain
separate. No old files, grades, chats or settings are reset.

All learner algorithm functions remain TODOs. Only image generation is provided.
The estimator is educational, not a production solver, benchmark result, robust
occlusion model or guarantee of accuracy. Color conversion, file/video upload,
learned flow, variational regularization and robust losses are not implemented.
Use small arrays first; the straightforward Python patch loops are for learning,
not a real-time performance claim.

## Maintenance

Verification on 18 October 2026: 81 selected backend regressions passed,
including independent worked-arithmetic checks, existing numerical contracts,
LDPC rendering/content, cache and session APIs. Two real-Docker smokes passed,
executing all 36 unchanged public cases and checking TODO failures,
submission/unlock and artifacts. Browser checks exercise every visual control,
playback/pause/reset, navigation cleanup, reduced motion, numerical changes,
intentional invariance, five mobile chapters and twelve mobile assignments.
They also verify saved code, course isolation and existing LDPC/cache pages,
with zero AI requests. Stream regression, lint, typecheck and production builds
pass. These tests do not measure live-model quality or general flow accuracy.

Source is curriculum/optical_flow/manifest.json and theory.json. Starters and
public checks are adjacent. The generic Python runner reads the requested course
ID from the trusted manifest instead of hard-coding LDPC. Existing LDPC revisions
remain separately loaded, unchanged. Optional TheorySection.visual identifiers
select section-local React diagrams; missing fields retain the legacy renderer.
All accompanying numerical explanation is section text and therefore travels
through the theory API into tutor context and the Markdown export.
Checkpoint.input_reference holds the callable contract and concrete invocation;
it appears immediately before the editor. Worked examples and implementation
instructions remain together in lesson prose; hints and experiments are folded.

Export readable prose with `node scripts/export_optical_flow.mjs` (stdout only).
docs/OPTICAL_FLOW_TUTORIAL.md is a checked-in teaching-text snapshot.
Tests in tests/test_optical_flow.py use independent author-only baselines.
tests/test_optical_flow_teaching.py independently verifies the worked arithmetic.
tests/test_optical_flow_live.py opt-in smokes must use a disposable DATA_DIR and
database, with FLOW_DOCKER_SMOKE=1. web/tests/optical-flow.smoke.cjs routes traffic
to a disposable API on port 8021 (frontend defaults to port 3021, overridden
with FLOW_WEB_URL; set LDPC_PLAYWRIGHT_MODULE to the installed Playwright path); its unlocked gallery changes only browser
response data, never persisted grades. No test calls a live AI model.

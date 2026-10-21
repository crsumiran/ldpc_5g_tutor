# Experiment log

## 2026-10-02

- Read `README.md`, `IMPLEMENTATION_STRATEGY.md`, `CODEX_START_PROMPT.md`, and
  `AGENTS.md`; inspected `assignment1.zip` without executing its content.
- Archive includes CS231n notebook worksheets (`two_layer_net.ipynb`,
  `FullyConnectedNets.ipynb`, and others) and modular NumPy TODOs.
- Local Python: 3.13.13; NumPy 1.26.4, safetensors 0.8.0,
  transformers 5.12.0; `nbformat`, PyTorch, JupyterLab, pytest absent from
  this interpreter. No containers or services started.
- Checked the official Qwen3.6-27B model card, config and safetensors index;
  confirmed hybrid 64-layer architecture and BF16 shard layout. No checkpoint
  weights are present in this workspace.

## 2026-10-03

- Created `qwen_numpy/` operator starter, public reference/checks, index-based
  Drive reader, and layerwise CPU text model. Created the generated notebook,
  original-model fixture script, and optional OpenCode guide server.
- Ran `python scripts/build_assignment.py`; output notebook has 35 cells, 35
  unique IDs, and no saved outputs. Python AST parsed all 17 code cells.
- Ran `python -m compileall -q qwen_numpy scripts`; passed.
- Ran `checks.run(reference)`; 16/16 public comparison cases passed. This
  checks the reference calculations, not the unfinished learner functions.
- Created a disposable four-layer synthetic safetensors checkpoint and called
  `TextModel.logits([1,2,3])` and `generate([1,2], 2)`; returned 16 finite
  logits and two token IDs. Tested BF16 row reading and blocked matmul with a
  separate disposable handcrafted tensor; both passed.
- Stubbed OpenCode child output to verify guide command/model/key routing and
  checked-answer path. The notebook's JSON Q&A route passed a socket-free
  handler check. Could not bind a localhost test socket in this sandbox;
  `ThreadingHTTPServer` raised `PermissionError: [Errno 1] Operation not
  permitted`. No live provider call was made.
- `nbformat` was not installed. An attempted temporary `pip install --target
  /tmp/qwen_nbformat_verify nbformat==5.10.4` found no available distribution
  through this sandbox's package index, so schema validation remains pending.
- No real Drive shard, PyTorch installation, or OpenRouter key available in
  this workspace. No parent Compose command or service was run.

## WSL access and editor setup

- Confirmed host kernel `6.6.87.2-microsoft-standard-WSL2`, VS Code `code`
  executable present through Windows installation, Windows drives `/mnt/c`
  and `/mnt/d` present, and no `/mnt/g` Drive mount or `rclone` executable.
- Added `ipykernel` to notebook dependencies and normalized notebook fixture
  paths through the editable package location, so VS Code kernel working
  directory does not change where token IDs and references are written.
- Documented Windows Google Drive for desktop/DrvFs and rclone alternatives
  in README. No external Drive account was connected and no mount attempted.

## Beginner lesson and visual checks

- Expanded all 11 operator sections with motivation, model impact, a concrete
  input/output example, a prediction, and a reflection. Added 11 diagrams
  rendered from `qwen_numpy/tutorial.py`, visible before learner code is run.
- Each task now has exactly two exercise cells: a small visible example and an
  extended deterministic comparison. `scripts/build_visuals.py` generated all
  11 PNGs; the attention and DeltaNet images were visually inspected.
- Regenerated notebook: 46 cells, 46 unique IDs, 28 syntactically valid code
  cells, 11 ordered task/small/extensive trios, all diagrams present, no saved
  code outputs. `nbformat` validation remains pending because it is not installed.
- Ran `checks.run(reference)` and `checks.run_all_extensive(reference)`:
  16 initial and 208 extended comparisons passed. The DeltaNet recurrence
  covers 78 of the extended comparisons, including varied heads, gate values,
  causality, decay-only state, and chunk continuation. These validate reference
  examples and public check wiring, not the unfinished learner implementation
  or real-checkpoint parity.
- Ran `python -m compileall -q qwen_numpy scripts`; passed.

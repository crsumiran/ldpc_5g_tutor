# Notebook tutor handoff

Status: standalone Qwen3.6-27B NumPy assignment authored (2026-10-03).

The request is for a CS231n-style, CPU-only notebook assignment using the official
`Qwen/Qwen3.6-27B` text checkpoint, weights kept on Google Drive, public operator
checks, a real-weight full-model comparison, and optional OpenRouter free-model
questions. This folder began as a planning package; no service is running.

The official checkpoint uses a Qwen3.5-compatible hybrid text architecture:
64 layers, three gated DeltaNet layers then one full-attention layer, BF16
safetensors, and a separate vision tower. The assignment targets **text only**.
The published safetensors index reports 55,562,855,904 bytes in the full
checkpoint. Sources: https://huggingface.co/Qwen/Qwen3.6-27B and
https://huggingface.co/Qwen/Qwen3.6-27B/blob/main/config.json .

## Working files

- `assignments/qwen36_27b/lesson.ipynb`: 46 cells, 11 explained operator
  tasks, each with a pre-rendered diagram, small visible test, and extended
  test; plus Drive setup, original-model fixture and NumPy inference cells,
  guide instructions and a Q&A cell. The starter deliberately has
  `NotImplementedError` TODOs and is not an already completed submission.
- `qwen_numpy/learner.py`: editable operators. `reference.py` and `checks.py`:
  public NumPy references, 16 initial comparisons, and 208 extended comparisons
  with invariants. `tutorial.py` runs the visible toy examples and plots them.
- `scripts/build_visuals.py`: renders 11 static diagrams with reference
  operators, so learners can see them before completing the TODOs.
- `qwen_numpy/weights.py`: index-directed safetensors memory mapping from a
  mounted Drive directory; BF16 conversion and bounded matrix row blocks.
- `qwen_numpy/model.py`: 64-layer text-path wiring, optional BF16 rounding,
  per-layer reference comparison, next-token logits, short greedy generation.
- `scripts/capture_original.py`: optional PyTorch/Transformers CPU oracle;
  saves exact input IDs, model metadata hashes, final logits, generated IDs,
  and optional last-token vectors after every decoder layer.
- `scripts/guide_server.py` and `guide_opencode.json`: optional localhost
  browser guide using installed OpenCode 1.18.31 with denied tools and
  `openrouter/free` or another `:free` model. Terminal-entered key is passed
  to a short-lived isolated child process. No live provider call made.

## Evidence and limits

- `python scripts/build_assignment.py`: regenerated notebook.
- `MPLCONFIGDIR=/tmp/qwen_mpl_config python scripts/build_visuals.py`:
  rendered 11 PNG diagrams. Attention and DeltaNet figures inspected visually.
- `python -m compileall -q qwen_numpy scripts`: passed.
- Notebook JSON parsed, 46 unique cell IDs, 28 code cells parsed with Python
  AST, 11 ordered task/small/extensive trios with existing PNGs, and zero saved
  outputs. `nbformat` package is unavailable here, so its schema validator has
  not run.
- `checks.run(reference)` and `checks.run_all_extensive(reference)`: all 16
  initial and 208 extended comparisons passed. Learner TODOs intentionally
  do not pass until implemented.
- BF16 safetensors row extraction and blocked matrix multiplication passed a
  disposable synthetic check.
- Four-layer synthetic checkpoint, with three DeltaNet and one full-attention
  layer, produced finite logits and two greedy token IDs. This checks wiring
  only; it is not evidence of Qwen3.6-27B parity.
- OpenCode bridge request assembly passed a stub response. Local HTTP socket
  smoke was blocked by the current sandbox (`PermissionError: Operation not
  permitted`). The JSON guide route passed a socket-free handler check. No
  OpenRouter key was supplied and no live Q&A verified.
- The official 55.6 GB checkpoint is absent, so **actual full-model output,
  per-layer parity, and original-model equality remain unverified**.
- No Compose services are running. No parent project file, service, data, or
  learner workspace was changed.
- VS Code WSL setup is documented in `README.md`. The notebook uses
  `ASSIGNMENT_DIR` derived from the editable package, so generated fixtures
  have stable paths in JupyterLab and VS Code. The notebook dependency extra
  now includes `ipykernel`. Neither a Drive mount nor VS Code kernel launch
  has been verified in this sandbox.

## Next milestone

Install notebook requirements in the intended Jupyter environment, validate
the notebook with `nbformat`, mount the user's exact safetensors checkpoint,
complete the learner TODOs, capture the original CPU reference, and run the
notebook comparison. If numeric parity fails, use the saved layer vectors to
locate the first divergence, then correct BF16 operation order or checkpoint
version assumptions before claiming matching output. The separate tutor app
and isolated grading service remain future milestones in
`IMPLEMENTATION_STRATEGY.md`.

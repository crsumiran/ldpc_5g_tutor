# Python + Chisel notebook tutor: implementation handoff

This folder started as a planning and Codex handoff package. It now also has a
standalone **Qwen3.6-27B NumPy notebook assignment**. It remains independent of
the working cache tutor in the parent directory. No Compose service or
integrated Jupyter tutor has been deployed.

## Qwen3.6-27B NumPy assignment

Open [the notebook](assignments/qwen36_27b/lesson.ipynb). It follows the
CS231n worksheet structure in the supplied `assignment1.zip`: explained
operator tasks, predictions, editable functions, public NumPy comparisons,
and a final model experiment. Fill the TODOs in
[learner.py](qwen_numpy/learner.py). The text path includes embedding,
projections, RMSNorm, activations, partial RoPE, grouped causal attention,
depthwise convolution, gated DeltaNet recurrence, gated norm, SwiGLU, all 64
decoder layers, and the output projection. Vision and MTP are outside this
text assignment.

Each of the 11 operator sections starts with a plain-language explanation,
the reason that operation matters to the model, a numeric input/output
example, and a diagram visible before the function is implemented. It then
has exactly two exercise cells: a small example that prints inputs and
compares outputs while drawing the result, followed by extended checks over
shapes, edge cases, and invariants. The public checks total 16 initial and
208 extended comparisons. To regenerate the notebook and its diagrams after
editing the authoring files, run `python scripts/build_assignment.py` and
`python scripts/build_visuals.py` from this folder.

From this directory, install the notebook dependencies in a fresh Python
environment and launch JupyterLab:

```bash
python -m pip install -e '.[notebook]'
jupyter lab
```

The small operator exercises need no model weights. For the final experiment,
place the **unmodified official Hugging Face safetensors checkpoint** in a
mounted Google Drive directory: `config.json`,
`model.safetensors.index.json`, tokenizer files, and the 15
`model-*.safetensors` shards. Set `WEIGHTS_DIR` in the notebook to that mount.
The reader maps only the tensors requested by the current layer and expands
BF16 weight rows in bounded blocks. Files remain on Drive. A mount may cache
data locally under its own policy; the notebook does not control that policy.

To compare against the original Transformers model on the **same token IDs**,
install `.[original]` in an environment with PyTorch and enough CPU RAM, then
run `scripts/capture_original.py` as shown in the notebook. The optional script
writes final-position logits and one vector per decoder layer. The original
model may require more than 60 GB RAM; a real parity result has not been
captured here because this workspace has no checkpoint files. The NumPy path
is deliberately slow, especially for more than one generated token. The
notebook prints a numerical comparison only when a fixture exists.

For optional questions, start `python scripts/guide_server.py` from a terminal,
enter an OpenRouter API key at the hidden prompt, and open the localhost URL
it prints. The default is OpenRouter's free-model router; pass
`--model provider/model:free` for a specific free model. The guide uses the
installed OpenCode CLI with denied tools. It is advisory; it never grades or
handles the Drive weights. No key belongs in notebook cells, files, or URLs.
A live provider answer has not been verified without a key.

The standalone assignment is **public checks only**. It does not yet provide
the isolated, snapshot-based grading service or the integrated JupyterLab
guide described in the strategy. See [HANDOFF.md](HANDOFF.md) and
[EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) for exact evidence and next work.

## Google Drive and VS Code in WSL

If Google Drive for desktop is already installed on Windows, select **Stream
files** and note its drive letter. For a `G:` drive, check `ls /mnt/g` in WSL.
If it is absent, try `sudo mkdir -p /mnt/g` followed by
`sudo mount -t drvfs G: /mnt/g`. A Google virtual drive may behave differently
from an ordinary Windows disk; if WSL cannot read it, use the rclone route
below. Once mounted, set the notebook path to the actual folder, for example
`WEIGHTS_DIR = Path('/mnt/g/My Drive/Qwen3.6-27B')`. Run the notebook's
one-row embedding check before attempting 64 layers. See [Google's streaming
guide](https://support.google.com/drive/answer/13401938) and [Microsoft's
DrvFs mount instructions](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk).

The direct WSL alternative is [rclone's Google Drive backend](https://rclone.org/drive/).
Install `rclone` and `fuse3`, create a **read-only** Google Drive remote with
`rclone config`, and follow its browser authorization. Rclone's shared Drive
client ID is being retired in 2026, so follow its guide to create your own
OAuth client ID before relying on that route. To expose a remote named
`gdrive` as files in WSL:

```bash
mkdir -p ~/gdrive
rclone mount gdrive: ~/gdrive --read-only --vfs-cache-mode full
```

Keep that terminal running during the notebook session, then point
`WEIGHTS_DIR` to the model folder under `~/gdrive`, for example
`WEIGHTS_DIR = Path.home() / 'gdrive' / 'Qwen3.6-27B'`. Full VFS caching makes
random reads work but can use substantial local disk as the 55.6 GB checkpoint
is read. Layerwise loading primarily reduces **RAM** use; it does not remove
the cost of transferring model bytes. See [rclone mount caching](https://rclone.org/commands/rclone_mount/).

To open the notebook in VS Code connected to WSL, install the **WSL**, **Python**,
and **Jupyter** VS Code extensions. In a WSL terminal:

```bash
cd /home/ranga/opencode/tutor/notebook_tutor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[notebook]'
code .
```

Open `assignments/qwen36_27b/lesson.ipynb` in the resulting **WSL** window
and choose the `.venv` Python environment from **Select Kernel** in the upper
right. VS Code runs the kernel in WSL, so `WEIGHTS_DIR` must be a **WSL path**.
You do not need to start JupyterLab separately for this workflow. The notebook
derives its fixture paths from the installed editable package, so it works
whether VS Code starts the kernel at the repository root or notebook folder.
See [VS Code's WSL guide](https://code.visualstudio.com/docs/remote/wsl) and
[kernel picker guide](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management).

Read these files in order:

1. `IMPLEMENTATION_STRATEGY.md` — complete product, architecture, contracts,
   notebook execution, Python/Chisel adapters, OpenCode integration, security,
   implementation milestones, and acceptance tests.
2. `CODEX_START_PROMPT.md` — copyable prompt for the implementing Codex instance.
3. `AGENTS.md` — boundaries for agents working in this folder.

Start the new Codex instance with this folder as its workspace:

```bash
cd /home/ranga/opencode/tutor/notebook_tutor
codex
```

Then paste the prompt in `CODEX_START_PROMPT.md`. If the `codex` executable is
not configured, open this folder in your coding-agent interface instead.

The strategy defaults to Python notebooks plus an integrated JupyterLab guide
panel backed by OpenCode. Chisel uses real Scala files and an offline compiler /
simulator runner, controlled from notebook cells. VS Code can edit the same
notebooks; it does not have to host the custom JupyterLab extension.

No existing learner database, cache assignment, service, credential, notebook,
or source file has been copied into this folder. The implementing agent must
build and verify the new system; the architecture described here is not a claim
that it already exists.

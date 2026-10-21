"""Generate the authored notebook with stable cell IDs and no saved outputs."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assignments' / 'qwen36_27b' / 'lesson.ipynb'
cells = []


def cell(kind, ident, source, tags=()):
    result = {'cell_type': kind, 'id': ident, 'metadata': {'tags': list(tags)},
              'source': source.splitlines(keepends=True)}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    cells.append(result)


cell('markdown', 'intro', r'''# Build the text path of Qwen3.6-27B with NumPy

This assignment follows the CS231n pattern in `assignment1.zip`: read a visual
explanation, predict a result, implement one reusable NumPy function, run a
small visible test, run broader tests, and reflect. Implement each TODO in
`qwen_numpy/learner.py`; the notebook imports those functions. The final stage
runs **the whole text decoder**, with all 64 published layers, on a CPU using
weights from a mounted Google Drive folder. It makes one next-token prediction
and compares logits to a separately captured original Transformers run.

Scope: text tokens only. The published checkpoint also has a vision encoder and
an MTP draft head. Those are outside this notebook. The official text decoder
uses 48 gated DeltaNet layers and 16 full-attention layers. The BF16 checkpoint
index reports 55.6 GB of weights. A short prompt can still take a long time on
CPU because the notebook intentionally favors readable NumPy over optimized
kernels. Use the small checks before trying real weights. The final comparison
requires your exact checkpoint files and an original-model reference fixture.

### The picture to keep in mind

```text
words -> tokenizer -> token IDs -> embedding vectors
                                 |
                                 v
                 64 decoder layers, each doing:
                 normalize -> mix information -> add old vector
                           -> normalize -> gated MLP -> add old vector
                                 |
                                 v
                   output logits -> next token ID -> word piece
```

A **token** is a piece of text represented by an integer ID. A **vector** is a
row of numbers that carries features for one token. **Weights** are the
checkpoint's learned numbers. **Inference** means applying these weights to an
input; this assignment does not train new weights. **Logits** are scores for
possible next tokens; the largest score gives the greedy next token. In each
checkpoint, the picture and tiny numeric example explain one box in this flow.
The figures use toy numbers, while the final experiment uses real weights.

**Sources:** [Qwen checkpoint](https://huggingface.co/Qwen/Qwen3.6-27B),
[official config](https://huggingface.co/Qwen/Qwen3.6-27B/blob/main/config.json),
[official weight index](https://huggingface.co/Qwen/Qwen3.6-27B/blob/main/model.safetensors.index.json),
[Transformers implementation](https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py).

### Before starting

From this repository root, install with `python -m pip install -e '.[notebook]'`.
Launch JupyterLab from this repository. Save edits to `learner.py` before each
check, then restart or reload the module after an edit. No GPU is required.
''')

cell('code', 'setup', '''import json
from pathlib import Path
import numpy as np
import importlib
import qwen_numpy
from qwen_numpy import learner, reference, checks, tutorial

PROJECT_ROOT = Path(qwen_numpy.__file__).resolve().parents[1]
ASSIGNMENT_DIR = PROJECT_ROOT / 'assignments' / 'qwen36_27b'

def refresh():
    importlib.reload(learner)
    return learner

print('NumPy', np.__version__)
''')

tasks = [
 ('embedding', 'Token embedding', r'''**What it does.** A tokenizer turns a piece
of text into an integer token ID. An embedding table maps that ID to a vector
of learned features. This is a row lookup, not multiplication.

```text
token IDs [2, 0, 2] -> select table rows 2, 0, 2 -> three feature vectors
```

For a toy table with rows `[0,1,2]`, `[3,4,5]`, `[6,7,8]`, `[9,10,11]`,
the output is `[[6,7,8], [0,1,2], [6,7,8]]`. The figure highlights the
selected rows. **Why the model needs it:** later layers operate on vectors,
not integer IDs. The embedding is the starting representation of each token;
looking up the wrong row changes everything downstream. The real checkpoint's
table is much larger, so the Drive reader fetches selected rows.

**Implement:** `embedding(ids, table)` without changing `table`.
**Predict:** for four IDs and a table shaped `[9, 5]`, what is the output shape?
**Reflect:** why must repeated IDs produce repeated rows?'''),
 ('linear', 'Matrix projection', r'''**What it does.** A learned matrix combines
input features into new features. Each row of the weight matrix is one output
feature's recipe. `weight` is stored as `[output_features, input_features]`.

```text
input [1, 2]  x  weight rows [[1, 0], [0, 2]]  ->  output [1, 4]
```

The first output selects the first input. The second doubles the second input.
The figure shows both recipes and the resulting bars. **Why the model needs
it:** the same operation makes queries, keys, values, gates, MLP features, and
final vocabulary scores. A transpose mistake therefore affects almost every
part of the model. For real weights, the loader supplies one block of output
rows at a time; your function is reused on every block.

**Implement:** `linear(x, weight)` as a NumPy projection on the last axis.
**Predict:** what shape follows `[3,5] @ [7,5].T`?
**Reflect:** which weight row computes output feature zero?'''),
 ('rms_norm', 'RMS normalization', r'''**What it does.** An RMS is a typical
magnitude of a vector: square its features, average, then take a square root.
RMSNorm divides by this magnitude and applies a learned per-feature scale.

```text
[3, 4] -> RMS = sqrt((9 + 16)/2) = 3.5355 -> [0.8485, 1.1314]
```

The figure shows before and after values. The vector keeps nearly the same
direction while its scale becomes controlled. **Why the model needs it:** each
layer adds new information to an old vector; without scale control, values can
grow or shrink across 64 layers and change attention or gates. Qwen3.6's main
norms multiply by `1 + weight`; a later gated norm multiplies by `weight`.
`eps` prevents division by zero. Compute the square mean in float32.

**Implement:** `rms_norm(x, weight, eps, zero_centered)` for both conventions.
**Predict:** what should happen to the all-zero vector?
**Reflect:** which axis should be normalized for `[tokens, features]`?'''),
 ('activations', 'Activation functions', r'''**What they do.** These three small
functions shape or gate a signal without changing its array shape:

| Function | Rule | Job in this model |
| --- | --- | --- |
| sigmoid | `1 / (1 + exp(-x))` | gate strength between 0 and 1 |
| SiLU | `x * sigmoid(x)` | smooth nonlinear MLP and convolution output |
| softplus | `log(1 + exp(x))` | positive time step for DeltaNet decay |

For input `[-2, 0, 2]`, sigmoid is about `[0.119, 0.5, 0.881]`, while SiLU
is about `[-0.238, 0, 1.762]`. The figure compares all three curves.
**Why the model needs them:** a gate controls how much information passes,
and a nonlinearity lets layers build features that a single matrix cannot.
Large inputs can overflow naive exponentials, so use stable formulas.

**Implement:** `sigmoid`, `silu`, and `softplus` in `learner.py`.
**Predict:** is SiLU of a negative number always zero?
**Reflect:** why must DeltaNet's time step be positive?'''),
 ('softmax', 'Stable softmax', r'''**What it does.** Softmax turns a row of raw
attention scores into nonnegative weights that add to one.

```text
scores [1, 2, 3] -> weights about [0.090, 0.245, 0.665]
```

The figure puts the scores beside the normalized weights. **Why the model
needs it:** attention uses these weights to blend information from visible
tokens. Using the wrong axis blends different heads or tokens together. A
large score such as 1000 can overflow `exp`, so subtract the row maximum
before exponentiating; this does not change the probabilities.

**Implement:** `softmax(x, axis)` with stable exponentiation.
**Predict:** what should `[1000, 1000]` become?
**Reflect:** which axis holds the source-token choices in attention?'''),
 ('rope', 'Partial rotary position embedding', r'''**What it does.** A word's
meaning depends on where it appears. RoPE rotates pairs of query and key
features by an angle determined by token position. Their later dot product
can then respond to order and distance.

```text
position 0: [1,0,0,0] -> [1,0,0,0]
position 1: [1,0,0,0] -> about [0.540,0,0.841,0]
```

The arrow plot shows the same vector at positions zero and one. Qwen3.6
rotates only the first quarter of each full-attention head. For plain text,
its temporal, height, and width positions are equal, so multimodal RoPE
reduces to this simpler rotation. **Why the model needs it:** without position
information, attention has much less evidence about word order; a wrong
rotation changes which earlier tokens appear related.

**Implement:** `rope(q, k, positions, theta, fraction)` for `[tokens, heads,
head_dim]`. Rotate the two halves of only the selected dimensions.
**Predict:** why is position zero unchanged?
**Reflect:** why rotate queries and keys together?'''),
 ('grouped_attention', 'Grouped causal attention', r'''**What it does.** A query
asks what this token needs; keys describe earlier tokens; values carry their
content. Dot products score query-key matches, softmax gives blending weights,
and a weighted sum mixes the values. A causal mask hides future tokens.

```text
values [1, 2, 4], equal scores
token 0 sees [1]       -> output 1
token 1 sees [1, 2]    -> output 1.5
token 2 sees [1, 2, 4] -> output 2.333...
```

The figure shows the triangular visibility mask and mixed outputs. Qwen3.6
has 24 query heads and four key/value heads, so each key/value head serves six
query heads. **Why the model needs it:** full attention retrieves relevant
earlier context. The causal mask prevents future text from influencing a
prediction, while grouping reduces key/value storage.

**Implement:** `grouped_attention(q, k, v)`, reusing your softmax and using
scaled dot products. **Predict:** can output zero change when only a future
value changes? **Reflect:** what would happen if the mask were removed?'''),
 ('depthwise_causal_conv', 'Depthwise causal convolution', r'''**What it does.**
A tiny filter looks at the current token and a few recent tokens within each
projected feature channel. Channels do not mix in this operation; each has
its own kernel.

```text
input [1, 2, 3, 4], kernel [previous=1, current=1]
output [1, 3, 5, 7]  (missing earlier values count as zero)
```

The line plot shows how local history changes each output. The real DeltaNet
uses a width-four kernel over projected queries, keys, and values, followed
by SiLU. **Why the model needs it:** this local context reaches the recurrent
memory update before the memory reads or writes it. A noncausal filter would
let future tokens leak backward.

**Implement:** `depthwise_causal_conv(x, kernel)` for `[tokens, channels]` and
`[channels, kernel_width]`. The last kernel coefficient touches the current
token. **Predict:** which input can affect output zero?
**Reflect:** what changes if the kernel width is one?'''),
 ('gated_delta', 'Gated delta recurrence', r'''**What it does.** DeltaNet keeps a
small state matrix for each value head. Think of a key as an address and a
value as the content stored there. At each token it:

```text
decays old state -> reads what key currently retrieves
                 -> writes beta * (new value - old retrieved value)
                 -> reads the updated state with the query
```

With one fixed key, new values `[2, 5]`, beta one, and no decay, the second
step replaces the first association. The plot shows both values and reads;
the read is scaled by the query dimension. **Why the model needs it:** 48 of
the 64 text layers use this recurrent mixer. It carries compressed context
without a full attention table at every layer. A wrong decay can erase context
too quickly; a wrong update can keep obsolete information.

**Implement:** `gated_delta(q, k, v, log_decay, beta, state)` and return both
outputs and final state. Normalize q/k and scale q by `1/sqrt(key_dim)`.
**Predict:** if beta is zero, can the current value be written?
**Reflect:** why does the update subtract the old retrieved value?'''),
 ('gated_rms_norm', 'Gated DeltaNet output norm', r'''**What it does.** After
DeltaNet reads its memory, it normalizes each value-head vector, multiplies by
a learned scale, and applies a SiLU gate from the current token.

```text
memory [3, 4], gate [1, 1], scale [1, 1]
-> normalized [0.8485, 1.1314] -> gated about [0.620, 0.827]
```

The bars show how the gate reduces or amplifies what the memory sends onward.
**Why the model needs it:** the memory read can have a variable magnitude;
normalization controls that magnitude while the gate decides how much of it
affects the current layer. Here the scale is `weight`, unlike the earlier
main RMSNorm that uses `1 + weight`.

**Implement:** `gated_rms_norm(x, gate, weight, eps)` using your SiLU.
**Predict:** what happens if the gate input is zero?
**Reflect:** why normalize before applying the gate?'''),
 ('swiglu', 'SwiGLU feed-forward network', r'''**What it does.** Each decoder
layer has a small feature-building network after its attention or DeltaNet
mixer. One projection makes candidate features; another makes gates. They
are multiplied, then projected back to the model's hidden width.

```text
x -> gate projection -> SiLU --*--> down projection -> output
 \-> up projection ----------/
```

With input `[1, 2]` and identity toy weights, the output is about
`[0.731, 3.523]`. The plot separates the up path, gate, and product.
**Why the model needs it:** attention moves information among tokens; the MLP
builds nonlinear features inside each token. Wrong gate or multiplication
changes every layer's residual update.

**Implement:** `swiglu(x, gate_weight, up_weight, down_weight)` by reusing
your `linear` and `silu` functions.
**Predict:** what happens when the up projection is all zero?
**Reflect:** why must the final projection return to the input hidden width?'''),
]

for index, (name, title, explanation) in enumerate(tasks, 1):
    cell('markdown', f'task-{index:02d}', f'''## {index}. {title}\n\n{explanation}\n\n![Visual explanation of {title}](assets/{name}.png)\n\nEdit `qwen_numpy/learner.py` and save it. The **first cell** prints the exact toy input, expected output, and your output, then draws the operation again with your result. The **second cell** checks more shapes, edge cases, and a model invariant. Run both before moving on.\n''', (f'checkpoint:QN-{index:02d}',))
    cell('code', f'small-{index:02d}',
         f"# Small representative test and visual explanation\nrefresh()\ntutorial.show_small('{name}', learner)\n",
         ('public-check', 'small-example'))
    cell('code', f'extensive-{index:02d}',
         f"# Broader deterministic cases and invariants\nrefresh()\nchecks.check_extensive('{name}', learner)\n",
         ('public-check', 'extensive'))

cell('markdown', 'all-checks', r'''## 12. Combine the operators

The decoder applies a norm, one token mixer (full attention or DeltaNet), a
residual addition, another norm, the SwiGLU MLP, and another residual addition.
`qwen_numpy/model.py` supplies the checkpoint-specific wiring and Drive access.
Read its `layer` method; trace which of your functions each branch calls. The
large embedding table is read by selected rows; the large SwiGLU weights are
projected in row blocks. Their component operators are reused while the
standalone `embedding` and `swiglu` functions are checked on small arrays.
The check below reruns the small numeric references and all extended cases.
For a fresh process, run `python -m qwen_numpy.checks` from a terminal.
A notebook kernel may keep an old imported module, so save your source and
use `refresh()` here.

**Reflection:** Why can a notebook cell run successfully even when a fresh
process later fails to import or execute the saved source?''')
cell('code', 'run-all', '''refresh()
checks.run(learner)
checks.run_all_extensive(learner)
''')

cell('markdown', 'drive-setup', r'''## 13. Read real weights from Google Drive

Place the official `config.json`, `model.safetensors.index.json`, tokenizer
files, and all 15 unmodified `model-*.safetensors` shards in one Drive folder.
Mount Drive using your notebook environment's normal method. In Colab, for
example, run `from google.colab import drive; drive.mount('/content/drive')`
manually, then point `WEIGHTS_DIR` below to the mounted folder. A local Jupyter
server can use a mounted Drive filesystem path. The reader opens the shard
named by the index for each tensor and maps just that tensor; matrix rows are
expanded from BF16 in blocks. Drive traffic and disk cache behavior depend on
your mount. The reader never needs the vision tower for the text path, though
the full original reference loader uses the entire checkpoint.

This stage checks file metadata only; it does not run the model yet.''')
cell('code', 'drive-path', '''from pathlib import Path
from qwen_numpy.weights import WeightStore

WEIGHTS_DIR = Path('/path/to/your/mounted/Drive/Qwen3.6-27B')
if not WEIGHTS_DIR.exists():
    print('Set WEIGHTS_DIR to your mounted Drive folder before continuing.')
else:
    store = WeightStore(WEIGHTS_DIR)
    print('Indexed tensors:', len(store.index))
    print('Embedding shard:', store.index['model.language_model.embed_tokens.weight'])
    print('One embedding row:', store.rows('model.language_model.embed_tokens.weight', [0]).shape)
''')

cell('markdown', 'prompt', r'''## 14. Fix the exact input tokens

The original model and your NumPy model must receive **identical token IDs**.
Use the official tokenizer and chat template from the same Drive checkpoint.
Choose a short text prompt for CPU work. This cell writes token IDs to a local
JSON file so the original reference script can use them too. Do not confuse a
different chat template or sampling setting with a numerical model error.''')
cell('code', 'tokenize', '''import json
from transformers import AutoTokenizer

PROMPT = 'What is 2 + 2?'
if WEIGHTS_DIR.exists():
    tokenizer = AutoTokenizer.from_pretrained(str(WEIGHTS_DIR), local_files_only=True,
                                               trust_remote_code=False)
    text = tokenizer.apply_chat_template(
        [{'role': 'user', 'content': PROMPT}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False)
    input_ids = tokenizer(text, add_special_tokens=False)['input_ids']
    assert 0 < len(input_ids) <= 128
    (ASSIGNMENT_DIR / 'qwen_input_ids.json').write_text(json.dumps({'input_ids': input_ids}))
    print('Input tokens:', len(input_ids), input_ids)
''')

cell('markdown', 'original', r'''## 15. Capture the original model's answer

In a **separate CPU process with enough RAM**, run the optional original-model
script from the repository root. It uses Transformers on the same local Drive
checkpoint and saves all final-position logits. It may need more than 60 GB of
RAM and substantial time. The NumPy stage does not need all weights in memory.

```bash
python scripts/capture_original.py --weights /your/mounted/Drive/Qwen3.6-27B \\
  --input assignments/qwen36_27b/qwen_input_ids.json \\
  --output assignments/qwen36_27b/original_logits.json \\
  --layers-output assignments/qwen36_27b/reference_layers.npz \\
  --max-new-tokens 1
```

If you already run the original model elsewhere, save its full final-position
logits and exact token IDs in that same JSON format. Free OpenRouter model
answers are **not** a reference for Qwen3.6-27B weights.''')

cell('markdown', 'full-run', r'''## 16. Run all 64 layers and compare

This cell reads each text-layer matrix from Drive when needed, uses your NumPy
operators, and returns one logit for each vocabulary token. It then compares
the top token, absolute logit errors, and top-ten overlap with the original
fixture. Matching argmax gives the same greedy next token for this exact input;
small numeric differences may remain because Transformers uses BF16 and other
execution orders. A matching one-token result is not evidence for long-form
generation parity. To compare longer greedy text, set both `--max-new-tokens`
in the original script and `MAX_NEW_TOKENS` below to the same value (up to 16).
This recomputes the full prefix for each token and can be very slow. Do not
claim a comparison when the fixture is absent.

**Reflection:** If the top token differs, which layer type or numerical
operation would you inspect first?''')
cell('code', 'full-model', '''from qwen_numpy.model import TextModel
from qwen_numpy.comparison import compare
import hashlib

fixture = ASSIGNMENT_DIR / 'original_logits.json'
layer_fixture = ASSIGNMENT_DIR / 'reference_layers.npz'
input_file = ASSIGNMENT_DIR / 'qwen_input_ids.json'
if WEIGHTS_DIR.exists() and input_file.exists():
    checks.run(refresh())  # all TODOs must pass before the expensive run
    checks.run_all_extensive(learner)
    input_ids = json.loads(input_file.read_text())['input_ids']
    recorded = json.loads(fixture.read_text()) if fixture.exists() else None
    if recorded is not None:
        assert recorded['input_ids'] == input_ids, 'Reference used different tokens'
        for file_name, field in [('config.json', 'config_sha256'),
                                 ('model.safetensors.index.json', 'index_sha256')]:
            expected = hashlib.sha256((WEIGHTS_DIR / file_name).read_bytes()).hexdigest()
            assert recorded[field] == expected, f'Reference used different {file_name}'
    model = TextModel(WEIGHTS_DIR, ops=refresh())
    logits = model.logits(input_ids, progress=lambda done, total: print(
        f'Layer {done}/{total}', end='\\r' if done < total else '\\n'),
        layer_reference=layer_fixture if recorded is not None and layer_fixture.exists() else None)
    next_id = int(np.argmax(logits))
    print('NumPy next token:', next_id, repr(tokenizer.decode([next_id])))
    if recorded is not None:
        print(compare(logits, fixture))
        MAX_NEW_TOKENS = 1
        if MAX_NEW_TOKENS > 1:
            numpy_ids = model.generate(input_ids, max_new_tokens=MAX_NEW_TOKENS)
            print('NumPy generated IDs:', numpy_ids)
            print('Original generated IDs:', recorded.get('generated_ids'))
            print('Same generated IDs:', numpy_ids == recorded.get('generated_ids'))
    else:
        print('No original_logits.json fixture yet; numerical parity unverified.')
else:
    print('Complete the Drive and token-ID setup cells first.')
''')

cell('markdown', 'guide', r'''## Ask the guide

The optional local guide runs outside the notebook. Start it in a separate
terminal with `python scripts/guide_server.py`, enter an OpenRouter key at the
terminal prompt, and open its printed localhost address. You can also ask from
the next notebook cell. The browser form and cell can answer conceptual
questions or explain a public failure using the free-model router. The key
stays in the guide process memory; no key goes in this notebook or its saved
outputs. The guide is advisory; only deterministic checks report pass/fail.
Free-model availability and limits are set by OpenRouter.

Good question: “My gated delta state test differs at token 3. What should I
inspect next?” Include the small public error and function name, not your Drive
path or private data. The guide should suggest a small debugging experiment,
not write the full assignment for you.''')

cell('code', 'ask-guide', '''# Run only when you want to send a question to the free-model guide.
import json
import urllib.request
import urllib.error

GUIDE_QUESTION = 'Why do we normalize q and k before the gated delta update?'
request = urllib.request.Request(
    'http://127.0.0.1:3010/api/ask',
    data=json.dumps({'question': GUIDE_QUESTION}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(request, timeout=190) as response:
        guide_result = json.load(response)
    print('Requested model:', guide_result['requested_model'])
    print(guide_result['answer'])
except urllib.error.URLError as exc:
    print('Guide unavailable. Start scripts/guide_server.py in a terminal.', exc)
''')

notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3',
            'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}},
            'nbformat': 4, 'nbformat_minor': 5}
try:
    import nbformat
except ImportError:
    pass  # The notebook extra installs nbformat for schema validation.
else:
    nbformat.validate(nbformat.from_dict(notebook))
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + '\n')
print(DEST)

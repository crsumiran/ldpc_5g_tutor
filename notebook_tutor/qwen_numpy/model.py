"""Layerwise CPU inference over the text backbone of Qwen3.6-27B.

This deliberately favors clarity over speed. It reads each matrix from a Drive
mount as needed, and does not load the vision tower or MTP draft head.
"""

import json
from pathlib import Path

import numpy as np

from . import learner
from .weights import WeightStore


def round_bf16(x):
    """Represent float32 values after round-to-nearest-even BF16 conversion."""
    value = np.asarray(x, dtype=np.float32)
    bits = np.array(value, copy=True).view(np.uint32)
    bits += np.uint32(0x7FFF) + ((bits >> np.uint32(16)) & np.uint32(1))
    bits &= np.uint32(0xFFFF0000)
    return bits.view(np.float32)


class TextModel:
    def __init__(self, checkpoint_dir, ops=learner, emulate_bf16=True):
        root = Path(checkpoint_dir).expanduser()
        cfg = json.loads((root / 'config.json').read_text())
        if cfg.get('model_type') != 'qwen3_5':
            raise ValueError('Expected official Qwen3.6/Qwen3.5 checkpoint config')
        self.cfg = cfg['text_config']
        self.weights = WeightStore(root)
        self.ops = ops
        self.emulate_bf16 = emulate_bf16
        if self.cfg['num_hidden_layers'] != len(self.cfg['layer_types']):
            raise ValueError('Layer count does not match layer_types')

    def _key(self, i, suffix):
        return f'model.language_model.layers.{i}.{suffix}'

    def _cast(self, x):
        return round_bf16(x) if self.emulate_bf16 else np.asarray(x, np.float32)

    def _linear(self, x, key):
        # The weight store handles large matrices in bounded row chunks. For a
        # toy checkpoint, the learner's linear operator can also be exercised.
        return self._cast(self.weights.matmul(x, key, linear=self.ops.linear))

    def _full_attention(self, x, i, positions):
        c, op = self.cfg, self.ops
        h, d, kv = c['num_attention_heads'], c['head_dim'], c['num_key_value_heads']
        p = lambda name: self._key(i, 'self_attn.' + name)
        qg = self._linear(x, p('q_proj.weight')).reshape(len(x), h, 2 * d)
        q, gate = qg[..., :d], qg[..., d:]
        k = self._linear(x, p('k_proj.weight')).reshape(len(x), kv, d)
        v = self._linear(x, p('v_proj.weight')).reshape(len(x), kv, d)
        q = self._cast(op.rms_norm(q, self.weights.array(p('q_norm.weight')), c['rms_norm_eps']))
        k = self._cast(op.rms_norm(k, self.weights.array(p('k_norm.weight')), c['rms_norm_eps']))
        q, k = op.rope(q, k, positions, c['rope_parameters']['rope_theta'], c['partial_rotary_factor'])
        out = self._cast(op.grouped_attention(self._cast(q), self._cast(k), v)).reshape(len(x), h * d)
        gated = self._cast(out * self._cast(op.sigmoid(gate.reshape(len(x), h * d))))
        return self._linear(gated, p('o_proj.weight'))

    def _linear_attention(self, x, i):
        c, op = self.cfg, self.ops
        kh, vh = c['linear_num_key_heads'], c['linear_num_value_heads']
        kd, vd = c['linear_key_head_dim'], c['linear_value_head_dim']
        ksize, vsize = kh * kd, vh * vd
        p = lambda name: self._key(i, 'linear_attn.' + name)
        mixed = self._linear(x, p('in_proj_qkv.weight'))
        kernel = self.weights.array(p('conv1d.weight')).reshape(-1, c['linear_conv_kernel_dim'])
        mixed = self._cast(op.silu(self._cast(op.depthwise_causal_conv(mixed, kernel))))
        q = mixed[:, :ksize].reshape(len(x), kh, kd)
        k = mixed[:, ksize:2 * ksize].reshape(len(x), kh, kd)
        v = mixed[:, 2 * ksize:].reshape(len(x), vh, vd)
        q = np.repeat(q, vh // kh, axis=1)
        k = np.repeat(k, vh // kh, axis=1)
        z = self._linear(x, p('in_proj_z.weight')).reshape(len(x), vh, vd)
        beta = self._cast(op.sigmoid(self._linear(x, p('in_proj_b.weight'))))
        a = self._linear(x, p('in_proj_a.weight'))
        log_decay = -np.exp(self.weights.array(p('A_log'))) * op.softplus(
            a + self.weights.array(p('dt_bias')))
        out, _ = op.gated_delta(q, k, v, log_decay, beta)
        out = self._cast(op.gated_rms_norm(self._cast(out), z,
                                          self.weights.array(p('norm.weight')), c['rms_norm_eps']))
        return self._linear(out.reshape(len(x), vsize), p('out_proj.weight'))

    def _mlp(self, x, i):
        p = lambda name: self._key(i, 'mlp.' + name)
        gate = self._linear(x, p('gate_proj.weight'))
        up = self._linear(x, p('up_proj.weight'))
        activated = self._cast(self.ops.silu(gate))
        return self._linear(self._cast(activated * up), p('down_proj.weight'))

    def layer(self, hidden, i, positions):
        c, op = self.cfg, self.ops
        x = self._cast(op.rms_norm(hidden, self.weights.array(self._key(i, 'input_layernorm.weight')),
                                   c['rms_norm_eps']))
        if c['layer_types'][i] == 'full_attention':
            hidden = self._cast(hidden + self._full_attention(x, i, positions))
        elif c['layer_types'][i] == 'linear_attention':
            hidden = self._cast(hidden + self._linear_attention(x, i))
        else:
            raise ValueError(f"Unknown layer type {c['layer_types'][i]}")
        x = self._cast(op.rms_norm(hidden, self.weights.array(self._key(i, 'post_attention_layernorm.weight')),
                                   c['rms_norm_eps']))
        return self._cast(hidden + self._mlp(x, i))

    def logits(self, token_ids, progress=None, layer_reference=None):
        ids = np.asarray(token_ids, dtype=np.int64)
        if ids.ndim != 1 or len(ids) == 0:
            raise ValueError('Pass a nonempty 1-D token sequence')
        if len(ids) > 128:
            raise ValueError('CPU teaching runner limits prompts to 128 tokens')
        hidden = self.weights.rows('model.language_model.embed_tokens.weight', ids)
        positions = np.arange(len(ids), dtype=np.int64)
        oracle = np.load(layer_reference) if layer_reference is not None else None
        try:
            if oracle is not None:
                if 'input_ids' not in oracle.files or not np.array_equal(oracle['input_ids'], ids):
                    raise ValueError('Layer reference used different token IDs')
                import hashlib
                for filename, field in [('config.json', 'config_sha256'),
                                        ('model.safetensors.index.json', 'index_sha256')]:
                    actual = hashlib.sha256((self.weights.root / filename).read_bytes()).hexdigest()
                    if field not in oracle.files or str(oracle[field]) != actual:
                        raise ValueError(f'Layer reference used different {filename}')
            for i in range(self.cfg['num_hidden_layers']):
                hidden = self.layer(hidden, i, positions)
                if oracle is not None:
                    original = oracle[f'layer_{i}']
                    error = float(np.max(np.abs(hidden[-1] - original)))
                    print(f'Layer {i + 1}: max last-token difference {error:.6g}')
                if progress:
                    progress(i + 1, self.cfg['num_hidden_layers'])
        finally:
            if oracle is not None:
                oracle.close()
        hidden = self._cast(self.ops.rms_norm(hidden[-1:],
                                              self.weights.array('model.language_model.norm.weight'),
                                              self.cfg['rms_norm_eps']))
        return self._cast(self.weights.matmul(hidden, 'lm_head.weight', linear=self.ops.linear))[0]

    def generate(self, token_ids, max_new_tokens=1, eos_ids=(248046, 248044)):
        """Greedy text generation; recomputes the prefix for clarity."""
        if not 1 <= max_new_tokens <= 16:
            raise ValueError('CPU teaching runner permits 1 to 16 new tokens')
        tokens = list(token_ids)
        generated = []
        for _ in range(max_new_tokens):
            token = int(np.argmax(self.logits(tokens)))
            tokens.append(token)
            generated.append(token)
            if token in eos_ids:
                break
        return generated

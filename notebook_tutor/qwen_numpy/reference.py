"""Small independent public reference functions used by the assignment checks.

These implement the mathematical text path, not image/video processing or MTP.
Arrays are float32 unless a check deliberately uses float64.
"""

import numpy as np


def embedding(ids, table):
    return np.asarray(table)[np.asarray(ids, dtype=np.int64)]


def linear(x, weight):
    return np.matmul(x, np.asarray(weight).T)


def rms_norm(x, weight, eps=1e-6, zero_centered=True):
    x = np.asarray(x, dtype=np.float32)
    scale = 1.0 + weight if zero_centered else weight
    return x / np.sqrt(np.mean(x * x, axis=-1, keepdims=True) + eps) * scale


def silu(x):
    x = np.asarray(x)
    return x / (1.0 + np.exp(-np.clip(x, -80, 80)))


def sigmoid(x):
    x = np.asarray(x)
    return 1.0 / (1.0 + np.exp(-np.clip(x, -80, 80)))


def softplus(x):
    x = np.asarray(x)
    return np.maximum(x, 0) + np.log1p(np.exp(-np.abs(x)))


def softmax(x, axis=-1):
    x = np.asarray(x, dtype=np.float32)
    e = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e / np.sum(e, axis=axis, keepdims=True)


def rope(q, k, positions, theta=10_000_000.0, fraction=0.25):
    """Text-only MRoPE: temporal, height, and width positions are equal."""
    d = int(q.shape[-1] * fraction)
    assert d % 2 == 0 and k.shape[-1] == q.shape[-1]
    freq = theta ** (-np.arange(0, d, 2, dtype=np.float32) / d)
    angles = np.outer(np.asarray(positions, dtype=np.float32), freq)
    cos = np.cos(np.concatenate([angles, angles], axis=-1))[:, None, :]
    sin = np.sin(np.concatenate([angles, angles], axis=-1))[:, None, :]

    def rotate(x):
        part = x[..., :d]
        half = d // 2
        turned = np.concatenate([-part[..., half:], part[..., :half]], axis=-1)
        return np.concatenate([part * cos + turned * sin, x[..., d:]], axis=-1)

    return rotate(q), rotate(k)


def grouped_attention(q, k, v):
    """Causal grouped-query attention, input shapes [T, heads, head_dim]."""
    t, h, d = q.shape
    assert k.shape[0] == v.shape[0] == t and h % k.shape[1] == 0
    kr = np.repeat(k, h // k.shape[1], axis=1)
    vr = np.repeat(v, h // v.shape[1], axis=1)
    scores = np.einsum('thd,shd->hts', q, kr) / np.sqrt(d)
    scores[:, np.triu_indices(t, 1)[0], np.triu_indices(t, 1)[1]] = -np.inf
    probs = softmax(scores)
    return np.einsum('hts,shd->thd', probs, vr)


def depthwise_causal_conv(x, kernel):
    """Input [T,C], kernel [C,K]; kernel[-1] multiplies current token."""
    t, c = x.shape
    assert kernel.shape[0] == c
    width = kernel.shape[1]
    padded = np.pad(x, ((width - 1, 0), (0, 0)))
    out = np.empty_like(x, dtype=np.float32)
    for i in range(t):
        out[i] = np.sum(padded[i:i + width].T * kernel, axis=1)
    return out


def gated_delta(q, k, v, log_decay, beta, state=None):
    """Recurrent DeltaNet rule, [T,H,K], [T,H,K], [T,H,V]."""
    t, h, kd = q.shape
    vd = v.shape[-1]
    s = np.zeros((h, kd, vd), np.float32) if state is None else state.astype(np.float32).copy()
    out = np.empty((t, h, vd), np.float32)
    q = q / np.sqrt(np.sum(q * q, axis=-1, keepdims=True) + 1e-6)
    k = k / np.sqrt(np.sum(k * k, axis=-1, keepdims=True) + 1e-6)
    q = q / np.sqrt(kd)
    for i in range(t):
        s *= np.exp(log_decay[i])[:, None, None]
        remembered = np.einsum('hkv,hk->hv', s, k[i])
        delta = (v[i] - remembered) * beta[i, :, None]
        s += np.einsum('hk,hv->hkv', k[i], delta)
        out[i] = np.einsum('hkv,hk->hv', s, q[i])
    return out, s


def gated_rms_norm(x, gate, weight, eps=1e-6):
    x = np.asarray(x, np.float32)
    normalized = x / np.sqrt(np.mean(x * x, axis=-1, keepdims=True) + eps)
    return normalized * weight * silu(gate)


def swiglu(x, gate_weight, up_weight, down_weight):
    return linear(silu(linear(x, gate_weight)) * linear(x, up_weight), down_weight)

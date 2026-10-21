"""Learner TODOs. Implement each function using NumPy; keep the signatures."""

import numpy as np


def embedding(ids, table):
    """Return rows of table selected by token ids; preserve input order."""
    raise NotImplementedError("TODO 1: embedding")


def linear(x, weight):
    """PyTorch-style linear: weight is [out, in], output is x @ weight.T."""
    raise NotImplementedError("TODO 2: linear")


def rms_norm(x, weight, eps=1e-6, zero_centered=True):
    """Normalize the last axis; Qwen3.6 uses 1 + weight on main norms."""
    raise NotImplementedError("TODO 3: RMSNorm")


def silu(x):
    """Compute x * sigmoid(x)."""
    raise NotImplementedError("TODO 4: SiLU")


def sigmoid(x):
    """Stable logistic function."""
    raise NotImplementedError("TODO 4: sigmoid")


def softplus(x):
    """Stable log(1 + exp(x))."""
    raise NotImplementedError("TODO 4: softplus")


def softmax(x, axis=-1):
    """Stable probability normalization along axis."""
    raise NotImplementedError("TODO 5: softmax")


def rope(q, k, positions, theta=10_000_000.0, fraction=0.25):
    """Apply text-only partial rotary embedding to [T,H,D] q and k."""
    raise NotImplementedError("TODO 6: RoPE")


def grouped_attention(q, k, v):
    """Causal GQA; q has more heads than k and v."""
    raise NotImplementedError("TODO 7: grouped attention")


def depthwise_causal_conv(x, kernel):
    """Convolve [T,C] with [C,K], using zero left padding."""
    raise NotImplementedError("TODO 8: causal convolution")


def gated_delta(q, k, v, log_decay, beta, state=None):
    """Return (outputs, final_state) of the recurrent gated delta rule."""
    raise NotImplementedError("TODO 9: gated delta recurrence")


def gated_rms_norm(x, gate, weight, eps=1e-6):
    """Standard RMSNorm then weight and SiLU(gate)."""
    raise NotImplementedError("TODO 10: gated RMSNorm")


def swiglu(x, gate_weight, up_weight, down_weight):
    """Reuse linear and silu to make the gated MLP."""
    raise NotImplementedError("TODO 11: SwiGLU")

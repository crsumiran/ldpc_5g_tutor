"""Small visible examples for the beginner notebook.

Each demo prints its exact inputs and outputs, checks the learner operator, and
draws one picture of the operation. The larger checks live in checks.py.
"""

import numpy as np

from . import reference


def _show_array(label, value):
    print(f'{label} (shape {np.shape(value)}):')
    print(np.array2string(np.asarray(value), precision=4, suppress_small=True))


def _compare(label, observed, expected):
    _show_array(f'{label} expected', expected)
    _show_array(f'{label} yours', observed)
    np.testing.assert_allclose(observed, expected, rtol=2e-5, atol=2e-5)
    print(f'PASS small example: {label}')


def show_small(name, op, save_path=None):
    """Run one transparent toy case and show what the operator does visually."""
    import matplotlib.pyplot as plt

    if name == 'embedding':
        table = np.arange(12, dtype=np.float32).reshape(4, 3)
        ids = np.array([2, 0, 2])
        _show_array('Token IDs', ids)
        _show_array('Embedding table', table)
        actual = op.embedding(ids, table)
        _compare(name, actual, table[ids])
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        axes[0].imshow(table, cmap='Blues', aspect='auto')
        axes[0].set(title='Lookup table', xlabel='feature', ylabel='row / token ID')
        axes[1].imshow(actual, cmap='Blues', aspect='auto')
        axes[1].set(title='Selected rows: 2, 0, 2', xlabel='feature', ylabel='token position')
    elif name == 'linear':
        x = np.array([[1., 2.]], np.float32)
        weight = np.array([[1., 0.], [0., 2.]], np.float32)
        _show_array('Input vector', x)
        _show_array('Weight rows', weight)
        actual = op.linear(x, weight)
        _compare(name, actual, np.array([[1., 4.]], np.float32))
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        axes[0].imshow(weight, cmap='Blues', aspect='auto')
        axes[0].set(title='Two learned output rules', xlabel='input feature', ylabel='output feature')
        axes[1].bar(['input 0', 'input 1', 'output 0', 'output 1'], [1, 2, *actual[0]])
        axes[1].set(title='Features before and after projection', ylabel='value')
    elif name == 'rms_norm':
        x = np.array([[3., 4.]], np.float32)
        weight = np.zeros(2, np.float32)
        _show_array('Input', x)
        actual = op.rms_norm(x, weight)
        _compare(name, actual, reference.rms_norm(x, weight))
        fig, ax = plt.subplots(figsize=(7, 3))
        positions = np.arange(2)
        ax.bar(positions - .18, x[0], width=.36, label='before')
        ax.bar(positions + .18, actual[0], width=.36, label='after')
        ax.set(xticks=positions, xticklabels=['feature 0', 'feature 1'],
               title='Same direction, controlled scale', ylabel='value')
        ax.legend()
    elif name == 'activations':
        x = np.array([-2., 0., 2.], np.float32)
        _show_array('Input', x)
        for method in ('silu', 'sigmoid', 'softplus'):
            _compare(method, getattr(op, method)(x), getattr(reference, method)(x))
        grid = np.linspace(-5, 5, 200, dtype=np.float32)
        fig, ax = plt.subplots(figsize=(7, 3))
        for method in ('silu', 'sigmoid', 'softplus'):
            ax.plot(grid, getattr(reference, method)(grid), label=method)
        ax.axhline(0, color='gray', linewidth=.7)
        ax.set(title='Three different ways to gate or shape a signal', xlabel='input', ylabel='output')
        ax.legend()
    elif name == 'softmax':
        scores = np.array([[1., 2., 3.]], np.float32)
        _show_array('Attention scores', scores)
        actual = op.softmax(scores)
        _compare(name, actual, reference.softmax(scores))
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        axes[0].bar(['token 0', 'token 1', 'token 2'], scores[0])
        axes[0].set(title='Raw scores', ylabel='logit')
        axes[1].bar(['token 0', 'token 1', 'token 2'], actual[0])
        axes[1].set(title='Attention weights (sum = 1)', ylabel='probability', ylim=(0, 1))
    elif name == 'rope':
        q = np.zeros((2, 1, 4), np.float32)
        q[:, 0, 0] = 1
        k = q.copy()
        positions = np.array([0, 1])
        _show_array('Query before rotation', q)
        actual_q, actual_k = op.rope(q, k, positions, theta=10000., fraction=1.)
        expected_q, expected_k = reference.rope(q, k, positions, theta=10000., fraction=1.)
        _compare('RoPE query', actual_q, expected_q)
        _compare('RoPE key', actual_k, expected_k)
        fig, ax = plt.subplots(figsize=(5, 4))
        for i, color in [(0, 'tab:blue'), (1, 'tab:orange')]:
            ax.arrow(0, 0, actual_q[i, 0, 0], actual_q[i, 0, 2],
                     head_width=.05, length_includes_head=True, color=color,
                     label=f'position {i}')
        ax.set(xlim=(-.1, 1.2), ylim=(-.1, 1.2), xlabel='rotary feature 0',
               ylabel='rotary feature 2', title='Position rotates a feature pair')
        ax.legend()
    elif name == 'grouped_attention':
        q = np.zeros((3, 2, 2), np.float32)
        k = np.zeros((3, 1, 2), np.float32)
        v = np.array([[[1., 0.]], [[2., 0.]], [[4., 0.]]], np.float32)
        _show_array('Values at three positions', v[:, 0, 0])
        actual = op.grouped_attention(q, k, v)
        _compare(name, actual, reference.grouped_attention(q, k, v))
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        visible = np.tri(3, 3)
        axes[0].imshow(visible, cmap='Blues', vmin=0, vmax=1)
        axes[0].set(title='Causal visibility: 1 means visible', xlabel='source token', ylabel='query token')
        axes[1].plot([0, 1, 2], v[:, 0, 0], 'o-', label='input value')
        axes[1].plot([0, 1, 2], actual[:, 0, 0], 'o-', label='mixed output')
        axes[1].set(title='Only past and current values contribute', xlabel='token position')
        axes[1].legend()
    elif name == 'depthwise_causal_conv':
        x = np.array([[1.], [2.], [3.], [4.]], np.float32)
        kernel = np.array([[1., 1.]], np.float32)
        _show_array('Input sequence', x[:, 0])
        _show_array('Kernel [previous, current]', kernel)
        actual = op.depthwise_causal_conv(x, kernel)
        _compare(name, actual, np.array([[1.], [3.], [5.], [7.]], np.float32))
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(np.arange(4), x[:, 0], 'o-', label='input')
        ax.plot(np.arange(4), actual[:, 0], 'o-', label='previous + current')
        ax.set(title='A local causal filter', xlabel='token position', ylabel='value')
        ax.legend()
    elif name == 'gated_delta':
        q = np.array([[[1., 0.]], [[1., 0.]]], np.float32)
        k = q.copy()
        v = np.array([[[2.]], [[5.]]], np.float32)
        decay = np.zeros((2, 1), np.float32)
        beta = np.ones((2, 1), np.float32)
        _show_array('New values', v[:, 0, 0])
        actual, state = op.gated_delta(q, k, v, decay, beta)
        expected, expected_state = reference.gated_delta(q, k, v, decay, beta)
        _compare('gated delta output', actual, expected)
        _compare('gated delta final state', state, expected_state)
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot([0, 1], v[:, 0, 0], 'o-', label='new value')
        ax.plot([0, 1], actual[:, 0, 0], 'o-', label='read from updated memory')
        ax.set(title='A writeable memory replaces an old association', xlabel='token position')
        ax.legend()
    elif name == 'gated_rms_norm':
        x = np.array([[3., 4.]], np.float32)
        gate = np.ones_like(x)
        weight = np.ones(2, np.float32)
        _show_array('Memory output', x)
        _show_array('Gate', gate)
        actual = op.gated_rms_norm(x, gate, weight)
        _compare(name, actual, reference.gated_rms_norm(x, gate, weight))
        fig, ax = plt.subplots(figsize=(7, 3))
        positions = np.arange(2)
        ax.bar(positions - .18, x[0], width=.36, label='memory')
        ax.bar(positions + .18, actual[0], width=.36, label='normalized and gated')
        ax.set(xticks=positions, xticklabels=['feature 0', 'feature 1'],
               title='Gate controls how much memory is passed on')
        ax.legend()
    elif name == 'swiglu':
        x = np.array([[1., 2.]], np.float32)
        identity = np.eye(2, dtype=np.float32)
        _show_array('Input', x)
        actual = op.swiglu(x, identity, identity, identity)
        _compare(name, actual, reference.swiglu(x, identity, identity, identity))
        gate = reference.silu(x[0])
        fig, ax = plt.subplots(figsize=(7, 3))
        positions = np.arange(2)
        ax.bar(positions - .25, x[0], width=.25, label='input / up')
        ax.bar(positions, gate, width=.25, label='SiLU gate')
        ax.bar(positions + .25, actual[0], width=.25, label='product / output')
        ax.set(xticks=positions, xticklabels=['feature 0', 'feature 1'],
               title='One learned pathway gates another')
        ax.legend()
    else:
        raise ValueError(f'Unknown demo: {name}')
    fig.tight_layout()
    if save_path is None:
        plt.show()
    else:
        fig.savefig(save_path, dpi=160, bbox_inches='tight')
        plt.close(fig)

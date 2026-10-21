"""Public deterministic operator comparisons, independent of real weights."""

import numpy as np

from . import learner, reference


def _close(name, observed, expected, atol=2e-5, rtol=2e-5):
    np.testing.assert_allclose(observed, expected, atol=atol, rtol=rtol,
                               err_msg=name)
    print(f'PASS {name}')


def run(op=learner):
    rng = np.random.default_rng(231)
    table = rng.standard_normal((9, 5)).astype(np.float32)
    ids = np.array([2, 0, 2, 8])
    _close('embedding', op.embedding(ids, table), reference.embedding(ids, table))
    x = rng.standard_normal((3, 5)).astype(np.float32)
    w = rng.standard_normal((7, 5)).astype(np.float32)
    _close('linear', op.linear(x, w), reference.linear(x, w))
    scale = rng.standard_normal(5).astype(np.float32) * 0.1
    _close('zero-centered RMSNorm', op.rms_norm(x, scale), reference.rms_norm(x, scale))
    _close('ordinary RMSNorm', op.rms_norm(x, scale, zero_centered=False),
           reference.rms_norm(x, scale, zero_centered=False))
    for name in ('silu', 'sigmoid', 'softplus'):
        _close(name, getattr(op, name)(x * 20), getattr(reference, name)(x * 20))
    _close('softmax', op.softmax(x * 100), reference.softmax(x * 100))
    q = rng.standard_normal((4, 6, 8)).astype(np.float32)
    k = rng.standard_normal((4, 2, 8)).astype(np.float32)
    v = rng.standard_normal((4, 2, 8)).astype(np.float32)
    oq, ok = op.rope(q, k, np.arange(4), fraction=0.5)
    rq, rk = reference.rope(q, k, np.arange(4), fraction=0.5)
    _close('RoPE q', oq, rq)
    _close('RoPE k', ok, rk)
    _close('grouped causal attention', op.grouped_attention(q, k, v),
           reference.grouped_attention(q, k, v))
    conv_x = rng.standard_normal((5, 6)).astype(np.float32)
    conv_w = rng.standard_normal((6, 4)).astype(np.float32)
    _close('causal depthwise conv', op.depthwise_causal_conv(conv_x, conv_w),
           reference.depthwise_causal_conv(conv_x, conv_w))
    gq = rng.standard_normal((4, 3, 4)).astype(np.float32)
    gk = rng.standard_normal((4, 3, 4)).astype(np.float32)
    gv = rng.standard_normal((4, 3, 5)).astype(np.float32)
    decay = -rng.uniform(0.01, 0.7, (4, 3)).astype(np.float32)
    beta = rng.uniform(0, 1, (4, 3)).astype(np.float32)
    out, state = op.gated_delta(gq, gk, gv, decay, beta)
    expected, expected_state = reference.gated_delta(gq, gk, gv, decay, beta)
    _close('gated delta output', out, expected)
    _close('gated delta final state', state, expected_state)
    gate = rng.standard_normal((4, 3, 5)).astype(np.float32)
    weight = rng.standard_normal(5).astype(np.float32)
    _close('gated RMSNorm', op.gated_rms_norm(expected, gate, weight),
           reference.gated_rms_norm(expected, gate, weight))
    gw = rng.standard_normal((7, 5)).astype(np.float32)
    uw = rng.standard_normal((7, 5)).astype(np.float32)
    dw = rng.standard_normal((5, 7)).astype(np.float32)
    _close('SwiGLU', op.swiglu(x, gw, uw, dw), reference.swiglu(x, gw, uw, dw))
    print('16 public comparisons passed')


def check_one(name):
    names = ('embedding', 'linear', 'rms_norm', 'silu', 'sigmoid', 'softplus',
             'softmax', 'rope', 'grouped_attention', 'depthwise_causal_conv',
             'gated_delta', 'gated_rms_norm', 'swiglu')
    if name not in names:
        raise ValueError(f'Unknown operator {name}')

    class OneLearnerOperator:
        def __getattr__(self, key):
            return getattr(learner if key == name else reference, key)

    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        run(OneLearnerOperator())
    print(f'PASS {name}')


TUTORIAL_TASKS = ('embedding', 'linear', 'rms_norm', 'activations', 'softmax',
                  'rope', 'grouped_attention', 'depthwise_causal_conv',
                  'gated_delta', 'gated_rms_norm', 'swiglu')


def check_extensive(name, op=learner):
    """Deterministic larger cases plus invariants that expose common mistakes."""
    if name not in TUTORIAL_TASKS:
        raise ValueError(f'Unknown task: {name}')
    rng = np.random.default_rng(231)
    count = 0

    def match(actual, expected, label, atol=3e-5):
        nonlocal count
        np.testing.assert_allclose(actual, expected, atol=atol, rtol=3e-5,
                                   err_msg=f'{name}: {label}')
        count += 1

    if name == 'embedding':
        for vocab in (2, 9):
            for width in (1, 3, 7):
                table = rng.standard_normal((vocab, width)).astype(np.float32)
                before = table.copy()
                for ids in (np.array([vocab - 1, 0, vocab - 1]),
                            np.array([], dtype=np.int64)):
                    match(op.embedding(ids, table), reference.embedding(ids, table),
                          f'vocab={vocab}, width={width}, IDs={ids.tolist()}')
                match(table, before, 'table unchanged')
    elif name == 'linear':
        for tokens in (1, 4):
            for inputs, outputs in ((1, 1), (3, 7), (8, 2)):
                x = rng.standard_normal((tokens, inputs)).astype(np.float32)
                w = rng.standard_normal((outputs, inputs)).astype(np.float32)
                before = x.copy()
                match(op.linear(x, w), reference.linear(x, w),
                      f'{tokens} tokens, {inputs}->{outputs}')
                match(x, before, 'input unchanged')
        x = rng.standard_normal((2, 3, 4)).astype(np.float32)
        w = rng.standard_normal((5, 4)).astype(np.float32)
        match(op.linear(x, w), reference.linear(x, w), 'extra batch dimension')
        match(op.linear(x, np.zeros_like(w)), np.zeros((2, 3, 5)), 'zero weights')
    elif name == 'rms_norm':
        for shape in ((1, 3), (4, 8), (2, 3, 5)):
            for value in (0., 1., 100.):
                x = rng.standard_normal(shape).astype(np.float32) * value
                w = rng.standard_normal(shape[-1]).astype(np.float32) * .2
                before = x.copy()
                for centered in (True, False):
                    result = op.rms_norm(x, w, eps=1e-6, zero_centered=centered)
                    match(result, reference.rms_norm(x, w, 1e-6, centered),
                          f'shape={shape}, scale={value}, centered={centered}')
                    assert np.isfinite(result).all(), 'RMSNorm must remain finite'
                match(x, before, 'input unchanged')
    elif name == 'activations':
        for x in (np.array([-100., -50., -2., 0., 2., 50., 100.], np.float32),
                  rng.standard_normal((4, 7)).astype(np.float32) * 20):
            for method in ('silu', 'sigmoid', 'softplus'):
                result = getattr(op, method)(x)
                match(result, getattr(reference, method)(x), f'{method}, shape={x.shape}')
                assert np.isfinite(result).all(), f'{method} overflowed'
            match(op.silu(x), x * op.sigmoid(x), 'SiLU = x * sigmoid(x)')
            assert ((op.sigmoid(x) >= 0) & (op.sigmoid(x) <= 1)).all()
            assert (op.softplus(x) >= 0).all()
    elif name == 'softmax':
        for shape, axis in (((2, 5), -1), ((4, 3), 0), ((2, 3, 4), -1)):
            x = rng.standard_normal(shape).astype(np.float32) * 25
            for offset in (0., 1000.):
                result = op.softmax(x + offset, axis=axis)
                match(result, reference.softmax(x + offset, axis=axis),
                      f'shape={shape}, axis={axis}, offset={offset}')
                match(result.sum(axis=axis), np.ones_like(result.sum(axis=axis)),
                      'probabilities sum to 1')
                assert np.isfinite(result).all() and (result >= 0).all()
            match(op.softmax(x, axis=axis), op.softmax(x + 1000., axis=axis),
                  'constant-shift invariance', atol=5e-5)
    elif name == 'rope':
        for dim, fraction in ((8, .25), (8, .5), (16, 1.)):
            q = rng.standard_normal((3, 4, dim)).astype(np.float32)
            k = rng.standard_normal((3, 2, dim)).astype(np.float32)
            q_before, k_before = q.copy(), k.copy()
            positions = np.array([0, 1, 7])
            result_q, result_k = op.rope(q, k, positions, theta=10000., fraction=fraction)
            expected_q, expected_k = reference.rope(q, k, positions, theta=10000., fraction=fraction)
            match(result_q, expected_q, f'q dim={dim}, fraction={fraction}')
            match(result_k, expected_k, f'k dim={dim}, fraction={fraction}')
            match(np.linalg.norm(result_q, axis=-1), np.linalg.norm(q, axis=-1),
                  'rotation preserves vector length')
            match(result_q[0], q[0], 'position zero is identity')
            match(q, q_before, 'q unchanged')
            match(k, k_before, 'k unchanged')
    elif name == 'grouped_attention':
        for tokens in (1, 2, 5):
            q = rng.standard_normal((tokens, 4, 3)).astype(np.float32)
            k = rng.standard_normal((tokens, 2, 3)).astype(np.float32)
            v = rng.standard_normal((tokens, 2, 3)).astype(np.float32)
            result = op.grouped_attention(q, k, v)
            match(result, reference.grouped_attention(q, k, v), f'{tokens} tokens')
            if tokens > 1:
                future = v.copy()
                future[1:] += 100
                match(op.grouped_attention(q, k, future)[0], result[0],
                      'future values cannot affect token zero')
                future_k = k.copy()
                future_k[1:] += 100
                match(op.grouped_attention(q, future_k, v)[0], result[0],
                      'future keys cannot affect token zero')
    elif name == 'depthwise_causal_conv':
        for tokens in (1, 2, 5):
            for width in (1, 2, 4):
                x = rng.standard_normal((tokens, 3)).astype(np.float32)
                kernel = rng.standard_normal((3, width)).astype(np.float32)
                result = op.depthwise_causal_conv(x, kernel)
                match(result, reference.depthwise_causal_conv(x, kernel),
                      f'{tokens} tokens, width={width}')
                if tokens > 1:
                    future = x.copy()
                    future[1:] += 100
                    match(op.depthwise_causal_conv(future, kernel)[0], result[0],
                          'future input cannot affect token zero')
    elif name == 'gated_delta':
        for tokens in (1, 2, 4):
            for heads, key_dim, value_dim in ((1, 1, 1), (2, 3, 2)):
                q = rng.standard_normal((tokens, heads, key_dim)).astype(np.float32)
                k = rng.standard_normal((tokens, heads, key_dim)).astype(np.float32)
                v = rng.standard_normal((tokens, heads, value_dim)).astype(np.float32)
                decay = -rng.uniform(.01, .7, (tokens, heads)).astype(np.float32)
                initial = rng.standard_normal((heads, key_dim, value_dim)).astype(np.float32) * .1
                for gate_mode in ('mixed', 'zero', 'full'):
                    beta = (rng.uniform(0, 1, (tokens, heads)).astype(np.float32)
                            if gate_mode == 'mixed' else
                            np.full((tokens, heads), 0. if gate_mode == 'zero' else 1., np.float32))
                    out, state = op.gated_delta(q, k, v, decay, beta, initial)
                    ref_out, ref_state = reference.gated_delta(q, k, v, decay, beta, initial)
                    label = f'{tokens} tokens, {heads} heads, gate={gate_mode}'
                    match(out, ref_out, label + ' output')
                    match(state, ref_state, label + ' state')
                    if gate_mode == 'zero':
                        expected_decay = initial * np.exp(decay.sum(axis=0))[:, None, None]
                        match(state, expected_decay, label + ' no new write')
                    if tokens > 1:
                        split = tokens // 2
                        first, middle = op.gated_delta(q[:split], k[:split], v[:split],
                                                       decay[:split], beta[:split], initial)
                        second, final = op.gated_delta(q[split:], k[split:], v[split:],
                                                       decay[split:], beta[split:], middle)
                        match(np.concatenate([first, second]), out, label + ' chunk output')
                        match(final, state, label + ' chunk final state')
                        future = v.copy()
                        future[1:] += 100
                        match(op.gated_delta(q, k, future, decay, beta, initial)[0][0], out[0],
                              label + ' future values cannot affect token zero')
    elif name == 'gated_rms_norm':
        for shape in ((1, 3), (4, 2, 5)):
            x = rng.standard_normal(shape).astype(np.float32)
            gate = rng.standard_normal(shape).astype(np.float32)
            w = rng.uniform(.5, 1.5, shape[-1]).astype(np.float32)
            match(op.gated_rms_norm(x, gate, w), reference.gated_rms_norm(x, gate, w),
                  f'shape={shape}')
            match(op.gated_rms_norm(x, np.zeros_like(gate), w),
                  np.zeros_like(x), 'zero gate blocks output')
    elif name == 'swiglu':
        for tokens in (1, 4):
            x = rng.standard_normal((tokens, 3)).astype(np.float32)
            gate = rng.standard_normal((5, 3)).astype(np.float32)
            up = rng.standard_normal((5, 3)).astype(np.float32)
            down = rng.standard_normal((4, 5)).astype(np.float32)
            match(op.swiglu(x, gate, up, down), reference.swiglu(x, gate, up, down),
                  f'{tokens} tokens')
            match(op.swiglu(x, gate, np.zeros_like(up), down),
                  np.zeros((tokens, 4)), 'zero up pathway blocks output')
    if count == 0:
        raise AssertionError('No checks collected')
    print(f'PASS {name}: {count} extended comparisons plus invariants')
    return count


def run_all_extensive(op=learner):
    total = sum(check_extensive(name, op) for name in TUTORIAL_TASKS)
    if total == 0:
        raise AssertionError('No checks collected')
    print(f'{total} extended comparisons passed across {len(TUTORIAL_TASKS)} tasks')


if __name__ == '__main__':
    run()
    run_all_extensive()

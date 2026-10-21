import numpy as np
from iteration import flooding_step
from syndrome import syndrome
from channel import hard_decisions


def decode_toy(h, channel, max_iterations):
    """Initialize v2c from channel at edges. Check initial syndrome. Run flooding steps until zero syndrome or the iteration cap. Return bits, iterations used, and syndrome weight history including initial state.

    Return dict: bits array (n,), iterations int, syndrome_weights list. max_iterations >=0. Toy code only.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement decoder")


import numpy as np
from gf2 import gf2_dot


def syndrome(bits, h):
    """Compute one parity result per row of H. A zero syndrome means the candidate is a valid codeword, not necessarily the original transmitted word.

    bits: length n binary array; h: binary shape (m,n); return binary shape (m,), preserve inputs.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement syndrome")


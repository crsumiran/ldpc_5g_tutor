import numpy as np


def expand_qc(base, z):
    """Replace -1 by zero block; nonnegative k by identity with columns rotated right k mod Z. Set block[i,(i+k) mod Z]=1.

    base: integer (r,c), entries >=-1; z positive int. Return binary array (r*z,c*z). Toy base only.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement qc")


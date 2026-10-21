import numpy as np


def check_messages_fast(q):
    """Summarize a finite 1-D float array q of degree >= 2 without mutation.

    Return dict: min1, min2 (two smallest magnitudes including duplicates),
    argmin (first minimum index), negative_parity (0 or 1), outgoing (float
    array, same shape as q). Zero has positive sign. Reconstruct each
    extrinsic Min-Sum output using the summary, not a rescan per destination.
    """
    # TODO: implement the checkpoint contract; keep the two-minimum invariant.
    raise NotImplementedError("Implement minima summary and reconstruction")

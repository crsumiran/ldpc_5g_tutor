import numpy as np
from sampling import bilinear_sample


def fb_consistency(forward, backward, forward_valid, backward_valid, threshold=0.5):
    """forward/backward finite float (H,W,2); validity bool (H,W); threshold>=0. Return consistent bool (H,W). At p sample B at p+F(p); require in-bounds, forward_valid[p], all contributing bilinear backward samples valid (sample float validity mask isclose(1)), and norm(F(p)+B(p+F(p)))<=threshold. Never compare F(p) with B(p) at the same coordinate unless F=0."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement fb_consistency")


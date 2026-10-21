import numpy as np
from sampling import bilinear_sample


def warp_frame(frame1, flow):
    """frame1: finite float (H,W). flow: finite float (H,W,2), [u,v] in pixels. Return (warped float (H,W), valid bool (H,W)) using bilinear_sample(frame1, x+u, y+v). Invalid samples zero. Do not wrap edges and do not negate forward flow."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement warp_frame")


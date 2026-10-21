import numpy as np


def bilinear_sample(image, x, y):
    """image: finite float (H,W), H,W>=1. x,y: same-shape finite float arrays of any shape. Return (values float, valid bool), same shape as x. Closed valid domain 0<=x<=W-1, 0<=y<=H-1. Interpolate four neighbors; collapse neighbor at last row/column. Invalid samples return 0 with valid=False. No wraparound or extrapolation."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement bilinear_sample")


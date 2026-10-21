import numpy as np


def patch_system(ix, iy, it, x, y, radius):
    """Inputs ix,iy,it: finite float arrays (H,W), same shape. Integer center (x,y), radius>=0; complete square patch must fit. Return A shape (N,2), b shape (N,), N=(2*radius+1)^2, row-major pixel order. Each row is [Ix,Iy]; b=-It. Raise ValueError if patch crosses border."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement patch_system")


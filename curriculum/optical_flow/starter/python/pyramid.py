import numpy as np


def reduce_half(image):
    """image: finite float 2-D array, H,W>=2. Return low-pass-filtered image sampled at [::2,::2], shape (ceil(H/2),ceil(W/2)). Separable kernel [1,4,6,4,1]/16, np.pad mode='reflect' on each axis. Return float, preserve input. No scipy/OpenCV resize."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement reduce_half")


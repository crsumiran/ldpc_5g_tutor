import numpy as np


def saturate_signed(values, width):
    """Clip integer values to two's-complement signed range [-2^(w-1),2^(w-1)-1]. Width >=2. Return int64 array.

    values: integer array representable in int64; width 2..32. Use wider intermediates, preserve input.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement fixed")


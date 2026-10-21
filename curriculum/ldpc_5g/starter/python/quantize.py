import numpy as np
from fixed import saturate_signed


def quantize_signed(values, width, fraction_bits):
    """Return stored integer codes: values * 2^fraction_bits, round ties to even, then signed saturation. fraction_bits >=0; inputs finite.

    Return int64 array. Real reconstructed value = code / 2^fraction_bits. Use saturate_signed helper.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement quantize")


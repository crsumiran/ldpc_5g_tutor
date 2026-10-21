import numpy as np
from sampling import bilinear_sample


def upsample_flow(flow, target_shape):
    """flow finite float (h,w,2), h,w>=1. target_shape=(H,W), each dimension either 2*coarse or 2*coarse-1. Return float (H,W,2). Sample each component at (min(x/2,w-1),min(y/2,h-1)) with bilinear interpolation; multiply BOTH components by 2. Border extension is deliberate here. No mutation."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement upsample_flow")


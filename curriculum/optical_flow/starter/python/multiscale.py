import numpy as np
from pyramid import reduce_half
from resize import upsample_flow
from refinement import refine_flow


def pyramidal_flow(frame0, frame1, levels=3, iterations=3, radius=1, min_eigenvalue=1e-6):
    """Frames finite same-shape 2-D, H,W>=2; levels>=1, iterations>=0. All requested levels must have min dimension>=2*radius+1 and >=2; otherwise ValueError. Return (flow float original (H,W,2), valid bool (H,W)). Build both pyramids with reduce_half; start zero at coarsest, refine_flow at each level from coarse to fine; upsample_flow between levels. Return final level's validity only. No OpenCV/SciPy flow solver."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement pyramidal_flow")


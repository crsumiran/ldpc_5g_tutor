import numpy as np


def endpoint_error(estimate, truth, mask):
    """estimate,truth finite float (H,W,2), mask bool (H,W). Return dict errors float (H,W), mean float, count Python int. errors is Euclidean vector difference at masked pixels and NaN elsewhere. mean is masked average; with no selected pixels mean=NaN and count=0. No mutation."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement endpoint_error")


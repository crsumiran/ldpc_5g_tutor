import numpy as np
from minsum import check_messages


def corrected_messages(q, alpha=1.0, beta=0.0):
    """Start from uncorrected check_messages. Preserve sign; output magnitude alpha * max(abs(r)-beta,0). alpha in (0,1], beta >=0. beta=0 is NMS; alpha=1 is OMS.

    Finite q length >=2; return array same shape. No mutation.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement corrected")


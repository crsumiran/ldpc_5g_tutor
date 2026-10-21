import numpy as np
from minsum import check_messages
from variable import variable_messages


def flooding_step(h, channel, v2c):
    """Compute all check messages from old v2c, then all posteriors and new v2c. Store zero at nonedges.

    h: binary (m,n) with every check degree >=2; channel: (n,); v2c: (m,n). Return (c2v, new_v2c, posterior).
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement iteration")


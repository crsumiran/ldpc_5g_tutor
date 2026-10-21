import numpy as np
from minsum import check_messages


def layer_update(posterior, old_messages, indices):
    """For this one check layer, q = posterior[indices] - old_messages; compute new check messages; replace those contributions in a copy of posterior.

    indices: unique ascending indices, degree >=2; old_messages: same length. Return (new_posterior, new_messages).
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement layered")

/bin/bash: /home/ranga/miniconda3/lib/libtinfo.so.6: no version information available (required by /bin/bash)

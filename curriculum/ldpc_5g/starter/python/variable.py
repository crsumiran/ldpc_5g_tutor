import numpy as np


def variable_messages(channel_llr, incoming):
    """Compute posterior = channel LLR + sum incoming. Outgoing edge j equals posterior minus incoming[j].

    channel_llr: scalar; incoming: finite 1-D floats; return tuple (posterior scalar, outgoing array).
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement variable")


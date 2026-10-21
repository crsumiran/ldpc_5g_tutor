import numpy as np


def lane_plan(z, lanes):
    """Partition z independent lifted positions into groups of at most lanes. Return groups count, valid count per group, utilization = z/(groups*lanes). Positive integers only.

    Return dict with groups:int, valid:list[int], utilization:float. This is a lane-issue model, not total decoder cycles.
    """
    # TODO: implement the checkpoint contract. Keep this operation small.
    raise NotImplementedError("Implement lanes")


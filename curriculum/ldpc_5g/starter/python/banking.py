import numpy as np


def bank_conflicts(addresses, banks):
    """Model one simultaneous read group on single-read-port memory banks.

    addresses: 1-D nonnegative integer array; banks: positive integer count.
    Bank mapping is address % banks (teaching implementation choice).
    Return dict: bank_ids array, counts array length banks, conflict boolean.
    A conflict means two reads need the same single-ported bank this cycle.
    Do not mutate addresses. This does not model full decoder scheduling.
    """
    # TODO: map each address, count requests, and detect overloaded banks.
    raise NotImplementedError("Implement banking")

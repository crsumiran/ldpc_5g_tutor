import numpy as np
from minima import check_messages_fast


def verify(q, m1, m2, index, parity, expected):
    source = np.array(q, dtype=float)
    original = source.copy()
    out = check_messages_fast(source)
    assert out['min1'] == m1 and out['min2'] == m2
    assert out['argmin'] == index and out['negative_parity'] == parity
    assert np.allclose(out['outgoing'], expected)
    assert np.array_equal(source, original), 'Input must not be mutated'


def test_unique_minimum():
    verify([7,-3,5,-9], 3,5,1,0, [3,-5,3,-3])


def test_repeated_minimum():
    verify([3,3,5,9], 3,3,0,0, [3,3,3,3])


def test_zero_minimum():
    verify([0,4,6], 0,4,0,0, [4,0,0])


def test_signed_tie():
    verify([-2,2,8], 2,2,0,1, [2,-2,-2])


def test_degree_two():
    verify([-7,4], 4,7,1,1, [4,-7])


def test_two_zeros():
    verify([0,0,-6], 0,0,0,1, [0,0,0])

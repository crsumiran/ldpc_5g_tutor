import numpy as np
from banking import bank_conflicts


def test_unique():
    out = bank_conflicts(np.array([0,1,2,3]),4)
    assert np.array_equal(out['bank_ids'],[0,1,2,3])
    assert np.array_equal(out['counts'],[1,1,1,1]) and not out['conflict']


def test_collision():
    out = bank_conflicts(np.array([0,4,1]),4)
    assert np.array_equal(out['bank_ids'],[0,0,1])
    assert np.array_equal(out['counts'],[2,1,0,0]) and out['conflict']


def test_empty():
    out = bank_conflicts(np.array([],dtype=int),4)
    assert np.array_equal(out['counts'],[0,0,0,0]) and not out['conflict']

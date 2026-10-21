import numpy as np
from minsum import check_messages

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_manual():
    assert np.allclose(check_messages(np.array([7.,-3.,5.,-9.])), [3,-5,3,-3])
def test_ties():
    assert np.allclose(check_messages(np.array([3.,3.,5.,9.])), [3,3,3,3])
def test_zero():
    assert np.allclose(check_messages(np.array([0.,4.,6.])), [4,0,0])

def test_signed_tie():
    assert np.allclose(check_messages(np.array([-2.,2.,8.])), [2,-2,-2])

import numpy as np
from syndrome import syndrome

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_valid():
    assert np.array_equal(syndrome(np.array([1,0,1,1,1,0]), H), [0,0,0])
def test_flip():
    assert np.array_equal(syndrome(np.array([1,1,1,1,1,0]), H), [1,1,0])
def test_zero():
    assert np.array_equal(syndrome(np.zeros(6,dtype=int), H), [0,0,0])


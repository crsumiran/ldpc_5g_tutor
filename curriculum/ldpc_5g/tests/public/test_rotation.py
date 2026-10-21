import numpy as np
from rotation import qc_rotate

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_right():
    assert np.array_equal(qc_rotate(np.arange(8),3),[5,6,7,0,1,2,3,4])
def test_modulo():
    assert np.array_equal(qc_rotate(np.arange(8),11),[5,6,7,0,1,2,3,4])
def test_negative():
    assert np.array_equal(qc_rotate(np.arange(4),-1),[1,2,3,0])
def test_empty():
    import pytest
    with pytest.raises(ValueError): qc_rotate(np.array([]),0)


import numpy as np
from corrected import corrected_messages

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_oms():
    assert np.allclose(corrected_messages(np.array([7.,-3.,5.,-9.]),beta=1),[2,-4,2,-2])
def test_nms():
    assert np.allclose(corrected_messages(np.array([7.,-3.,5.,-9.]),alpha=.5),[1.5,-2.5,1.5,-1.5])
def test_clip():
    assert np.allclose(corrected_messages(np.array([.5,2.]),beta=1),[1,0])


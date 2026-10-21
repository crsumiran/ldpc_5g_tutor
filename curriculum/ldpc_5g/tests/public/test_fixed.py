import numpy as np
from fixed import saturate_signed

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_limits():
    assert np.array_equal(saturate_signed(np.array([-12,-8,-1,0,7,11]),4),[-8,-8,-1,0,7,7])
def test_six():
    assert np.array_equal(saturate_signed(np.array([-33,33]),6),[-32,31])


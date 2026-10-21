import numpy as np
from quantize import quantize_signed

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_codes():
    assert np.array_equal(quantize_signed(np.array([1.25,1.75,-1.25,10.]),4,1),[2,4,-2,7])
def test_integral():
    assert np.array_equal(quantize_signed(np.array([.2,-.8,100.]),6,0),[0,-1,31])

def test_decision_changes_at_zero():
    values=np.array([-.1,1.25]); codes=quantize_signed(values,4,1)
    assert np.array_equal(codes,[0,2])
    assert np.array_equal(values<0,[True,False])
    assert np.array_equal(codes<0,[False,False])

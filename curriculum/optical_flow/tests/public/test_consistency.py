import numpy as np
from consistency import fb_consistency

def test_constant_inverse_and_border():
    f=np.zeros((4,6,2));f[...,0]=1;b=-f;valid=np.ones((4,6),bool);out=fb_consistency(f,b,valid,valid)
    assert out[:,:-1].all() and not out[:,-1].any()
def test_destination_not_same_index():
    f=np.zeros((3,5,2));f[1,1]=[1,0];b=np.zeros_like(f);b[1,2]=[-1,0];valid=np.ones((3,5),bool)
    out=fb_consistency(f,b,valid,valid,threshold=.01)
    assert out[1,1] and not out[1,2]
def test_invalid_reverse_and_fractional():
    f=np.zeros((3,5,2));f[...,0]=.5;b=-f;fv=np.ones((3,5),bool);bv=fv.copy();bv[1,2]=False
    out=fb_consistency(f,b,fv,bv,threshold=.01)
    assert not out[1,1] and not out[1,2] and out[0,1] and not out[:,-1].any()


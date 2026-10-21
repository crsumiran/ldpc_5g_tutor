import numpy as np
from gradients import gradients

def test_ramp():
    y,x=np.mgrid[:4,:5];a=x+2*y;ix,iy,it=gradients(a,a-.5)
    assert np.allclose(ix,1) and np.allclose(iy,2) and np.allclose(it,-.5)
def test_unsigned_and_shape():
    a=np.full((3,4),2,dtype=np.uint8);b=np.zeros_like(a)
    ix,iy,it=gradients(a,b)
    assert ix.shape==iy.shape==it.shape==(3,4) and np.issubdtype(it.dtype,np.floating)
    assert np.allclose(it,-2) and not ix.any() and not iy.any()
def test_preserve_and_stencil():
    a=np.array([[0.,1.,4.],[0.,1.,4.]]) ;before=a.copy(); ix,iy,it=gradients(a,a)
    assert np.allclose(ix,[[1,2,3],[1,2,3]]) and not iy.any() and not it.any()
    assert np.array_equal(a,before)


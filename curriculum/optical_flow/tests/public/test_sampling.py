import numpy as np
from sampling import bilinear_sample

def test_fractional():
    image=np.array([[0.,10],[20,30]]);out,valid=bilinear_sample(image,np.array([.25]),np.array([.5]))
    assert out.shape==valid.shape==(1,) and np.allclose(out,[12.5]) and valid[0]
def test_closed_border_and_outside():
    image=np.array([[0.,10],[20,30]]);v,m=bilinear_sample(image,np.array([1.,1.01,-.01,0]),np.array([1.,1,0,0]))
    assert np.array_equal(m,[True,False,False,True]) and np.allclose(v,[30,0,0,0])
def test_constant_and_single_pixel():
    image=np.array([[7.]]) ;before=image.copy();v,m=bilinear_sample(image,np.array([[0.,.1]]),np.array([[0.,0.]]))
    assert np.array_equal(m,[[True,False]]) and np.allclose(v,[[7,0]]) and np.array_equal(image,before)


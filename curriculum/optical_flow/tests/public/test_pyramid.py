import numpy as np
from pyramid import reduce_half

def test_constant_shape():
    a=np.full((5,7),3.);before=a.copy();out=reduce_half(a)
    assert out.shape==(3,4) and np.allclose(out,3) and np.array_equal(a,before)
def test_filter_before_decimate():
    a=np.tile(np.array([0.,1.,0.,1.,0.,1.,0.,1.]),(8,1));out=reduce_half(a)
    assert np.allclose(out,.5), 'Alternating stripes must be filtered before decimation'
def test_reflect_phase():
    a=np.tile(np.arange(5.),(5,1));out=reduce_half(a)
    assert np.allclose(out,np.tile([.75,2.,3.25],(3,1)))


import numpy as np
from resize import upsample_flow

def test_constant_even_odd():
    f=np.empty((2,3,2));f[...,0]=1;f[...,1]=-.5;before=f.copy()
    for shape in [(4,6),(3,5)]:
        out=upsample_flow(f,shape)
        assert out.shape==(*shape,2) and np.allclose(out,[2,-1])
    assert np.array_equal(f,before)
def test_interpolation_and_endpoint_extension():
    f=np.zeros((2,2,2));f[...,0]=[[0,2],[0,2]];out=upsample_flow(f,(4,4))
    assert np.allclose(out[...,0],np.tile([0,2,4,4],(4,1))) and not out[...,1].any()
def test_vertical_and_single_cell():
    f=np.array([[[.25,2.]]]);out=upsample_flow(f,(2,2))
    assert out.shape==(2,2,2) and np.allclose(out,[.5,4])


import numpy as np
from warping import warp_frame

def test_direction():
    image=np.tile(np.array([9.,0,1,2]),(3,1));f=np.zeros((3,4,2));f[...,0]=1
    v,m=warp_frame(image,f)
    assert np.allclose(v[:,:3],np.tile([0,1,2],(3,1))) and m[:,:3].all() and not m[:,-1].any()
def test_component_order():
    image=np.arange(12.).reshape(3,4);f=np.zeros((3,4,2));f[...,1]=1
    v,m=warp_frame(image,f)
    assert np.array_equal(v[:2],image[1:]) and m[:2].all() and not m[-1].any()
def test_fractional_and_preserve():
    image=np.tile(np.arange(4.),(3,1));f=np.zeros((3,4,2));f[...,0]=.5;before=f.copy();v,m=warp_frame(image,f)
    assert np.allclose(v[:,:3],np.tile([.5,1.5,2.5],(3,1))) and np.array_equal(f,before)


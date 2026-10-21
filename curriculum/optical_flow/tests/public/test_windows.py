import numpy as np
from windows import patch_system

def test_one_pixel():
    a,b=patch_system(np.full((3,4),2.),np.full((3,4),-1.),np.full((3,4),-3.),2,1,0)
    assert a.shape==(1,2) and b.shape==(1,) and np.array_equal(a,[[2,-1]]) and np.array_equal(b,[3])
def test_row_order():
    ix=np.arange(25.).reshape(5,5);iy=ix+100;it=ix-50
    a,b=patch_system(ix,iy,it,2,2,1)
    assert a.shape==(9,2) and np.array_equal(a[:,0],[6,7,8,11,12,13,16,17,18])
    assert np.array_equal(a[:,1],a[:,0]+100) and np.array_equal(b,50-a[:,0])
def test_border_rejection():
    z=np.zeros((3,4));before=z.copy()
    try:patch_system(z,z,z,0,0,1)
    except ValueError:pass
    else:raise AssertionError('Incomplete patch must raise ValueError, not wrap or clip')
    assert np.array_equal(z,before)


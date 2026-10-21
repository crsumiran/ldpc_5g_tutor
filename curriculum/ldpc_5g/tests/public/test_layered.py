import numpy as np
from layered import layer_update

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_layer():
    p,r=layer_update(np.array([5.,1.,4.]),np.array([2.,-1.]),np.array([0,1]))
    assert np.allclose(p,[5,5,4]) and np.allclose(r,[2,3])
def test_preserve():
    x=np.array([5.,1.,4.]); old=x.copy(); layer_update(x,np.array([2.,-1.]),np.array([0,1])); assert np.array_equal(x,old)

def test_two_layers():
    a,r0=layer_update(np.array([3.,-1.,-1.]),np.zeros(2),np.array([0,1]))
    assert np.allclose(a,[2,2,-1]) and np.allclose(r0,[-1,3])
    a,r1=layer_update(a,np.zeros(2),np.array([1,2]))
    assert np.allclose(a,[2,1,1]) and np.allclose(r1,[-1,2])

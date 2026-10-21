import numpy as np
from iteration import flooding_step

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_trace():
    h=np.array([[1,1,0],[0,1,1]]); c=np.array([3.,-1.,2.]); q=h*c
    r,n,p=flooding_step(h,c,q)
    assert np.allclose(r,[[-1,3,0],[0,2,-1]])
    assert np.allclose(n,[[3,1,0],[0,2,2]]) and np.allclose(p,[2,4,1])
def test_no_mutation():
    h=np.array([[1,1,0],[0,1,1]]); c=np.array([3.,-1.,2.]); q=h*c; before=q.copy()
    flooding_step(h,c,q); assert np.array_equal(q,before)

def test_two_round_state():
    h=np.array([[1,1,0],[0,1,1]]); channel=np.array([3.,-1.,-1.])
    r,q,a=flooding_step(h,channel,h*channel)
    assert np.allclose(r,[[-1,3,0],[0,-1,-1]])
    assert np.allclose(q,[[3,-2,0],[0,2,-1]]) and np.allclose(a,[2,1,-2])
    r,q,a=flooding_step(h,channel,q)
    assert np.allclose(r,[[-2,3,0],[0,-1,2]])
    assert np.allclose(q,[[3,-2,0],[0,2,-1]]) and np.allclose(a,[1,1,1])

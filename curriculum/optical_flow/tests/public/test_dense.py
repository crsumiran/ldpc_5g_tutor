import numpy as np
from dense import dense_lk

def test_manufactured_motion():
    y,x=np.mgrid[:7,:9].astype(float);a=x*y;b=a-.1*y+.2*x
    flow,valid=dense_lk(a,b,radius=1)
    assert flow.shape==(7,9,2) and valid.shape==(7,9) and valid.dtype==bool
    assert valid[1:-1,1:-1].all() and np.allclose(flow[valid],[.1,-.2])
def test_invalid_border_and_flat():
    a=np.zeros((5,6));flow,valid=dense_lk(a,a)
    assert not valid.any() and not flow.any()
    y,x=np.mgrid[:5,:6];flow,valid=dense_lk(x*y,x*y)
    assert not valid[[0,-1],:].any() and not valid[:,[0,-1]].any()
def test_stationary_and_preservation():
    y,x=np.mgrid[:5,:6].astype(float);a=x*y;before=a.copy();flow,valid=dense_lk(a,a)
    assert valid[2,2] and np.allclose(flow[valid],0) and np.array_equal(a,before)


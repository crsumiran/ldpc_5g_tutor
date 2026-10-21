import numpy as np
from channel import hard_decisions

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_signs():
    assert np.array_equal(hard_decisions(np.array([1.3,.15,-.2,-2.1,0])), [0,0,1,1,0])
def test_shape():
    x=np.array([2.,-3.]); before=x.copy(); out=hard_decisions(x)
    assert out.shape == x.shape and np.array_equal(x,before)


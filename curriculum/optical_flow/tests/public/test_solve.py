import numpy as np
from solve import solve_window

def test_constrained():
    a=np.array([[1.,0],[0,1],[1,1]]);b=np.array([2.,-1,1]);out=solve_window(a,b)
    assert out['valid'] is True and np.allclose(out['uv'],[2,-1])
    assert np.isclose(out['min_eigenvalue'],1/3)
def test_aperture_and_flat():
    for a in [np.array([[1.,0],[2,0]]),np.zeros((4,2))]:
        out=solve_window(a,np.ones(len(a)))
        assert out['valid'] is False and np.array_equal(out['uv'],[0,0])
def test_normalization_and_stationary():
    a=np.array([[1.,0],[0,1]]);before=a.copy()
    first=solve_window(a,np.zeros(2));repeated=solve_window(np.tile(a,(3,1)),np.zeros(6))
    assert first['valid'] is True and np.array_equal(first['uv'],[0,0])
    assert np.isclose(first['min_eigenvalue'],repeated['min_eigenvalue']) and np.array_equal(a,before)


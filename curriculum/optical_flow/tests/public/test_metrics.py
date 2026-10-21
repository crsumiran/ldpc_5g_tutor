import numpy as np
from metrics import endpoint_error

def test_masked_mean():
    estimate=np.zeros((2,3,2));estimate[0,0]=[3,4];truth=np.zeros_like(estimate);mask=np.zeros((2,3),bool);mask[0,:2]=True
    out=endpoint_error(estimate,truth,mask)
    assert out['count']==2 and np.isclose(out['mean'],2.5)
    assert np.allclose(out['errors'][mask],[5,0]) and np.isnan(out['errors'][~mask]).all()
def test_empty_is_not_perfect():
    a=np.zeros((2,3,2));out=endpoint_error(a,a,np.zeros((2,3),bool))
    assert out['count']==0 and np.isnan(out['mean']) and np.isnan(out['errors']).all()
def test_axes_and_preservation():
    a=np.zeros((2,2,2));b=np.ones_like(a);mask=np.ones((2,2),bool);before=a.copy();out=endpoint_error(a,b,mask)
    assert out['errors'].shape==(2,2) and np.isclose(out['mean'],np.sqrt(2)) and np.array_equal(a,before)


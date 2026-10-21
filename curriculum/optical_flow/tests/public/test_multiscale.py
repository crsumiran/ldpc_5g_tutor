import numpy as np
from multiscale import pyramidal_flow
from provided.scene import image_pair

def test_identity():
    a,_,_=image_pair((20,24));f,m=pyramidal_flow(a,a,levels=2,iterations=2)
    assert f.shape==(20,24,2) and m.shape==(20,24) and m[4:-4,4:-4].all() and np.allclose(f[m],0)
def test_translation():
    a,b,truth=image_pair((24,28),(1.,-.5));before=a.copy();f,m=pyramidal_flow(a,b,levels=2,iterations=4)
    core=np.zeros(m.shape,dtype=bool);core[6:-6,6:-6]=True
    assert m[core].all() and np.mean(np.linalg.norm(f[core]-truth[core],axis=1))<.3
    assert np.array_equal(a,before)
def test_flat_and_level_validation():
    a=np.zeros((8,10));f,m=pyramidal_flow(a,a,levels=1)
    assert not m.any() and np.allclose(f,0)
    try:pyramidal_flow(a,a,levels=5)
    except ValueError:pass
    else:raise AssertionError('Requested pyramid must leave room for a full patch at every level')


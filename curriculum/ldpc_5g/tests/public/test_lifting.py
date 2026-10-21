import numpy as np
from lifting import lifting_set_index

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_sets():
    assert lifting_set_index(8)==0 and lifting_set_index(96)==1 and lifting_set_index(384)==1
def test_invalid():
    import pytest
    with pytest.raises(ValueError): lifting_set_index(97)
def test_all():
    from provided.nr_sets import LIFTING_SETS
    assert sum(len(s) for s in LIFTING_SETS)==51
    for i,s in enumerate(LIFTING_SETS):
        for z in s: assert lifting_set_index(z)==i


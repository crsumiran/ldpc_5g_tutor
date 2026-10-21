import numpy as np
from refinement import refine_flow
from provided.scene import image_pair

def test_stationary():
    a,_,_=image_pair((12,14));initial=np.zeros((12,14,2));f,m=refine_flow(a,a,initial,iterations=2)
    assert m[2:-2,2:-2].all() and np.allclose(f[m],0)
def test_zero_rounds_and_preserve():
    a,_,_=image_pair((8,10));initial=np.full((8,10,2),.2);before=initial.copy();f,m=refine_flow(a,a,initial,iterations=0)
    assert np.array_equal(f,initial) and not m.any() and np.array_equal(initial,before) and not np.shares_memory(f,initial)
def test_small_translation_and_support():
    a,b,truth=image_pair((18,20),(.2,-.15));initial=np.zeros_like(truth);f,m=refine_flow(a,b,initial,iterations=3)
    core=np.zeros(m.shape,dtype=bool);core[4:-4,4:-4]=True
    assert m[core].all() and np.mean(np.linalg.norm(f[core]-truth[core],axis=1))<.12
    bad=np.full_like(truth,100);f,m=refine_flow(a,b,bad,iterations=1)
    assert not m.any() and np.array_equal(f,bad)


import numpy as np
from qc import expand_qc

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_blocks():
    out=expand_qc(np.array([[0,1,-1],[2,-1,0]]),4)
    assert out.shape==(8,12) and out.sum()==16
    assert np.array_equal(out[:4,:4],np.eye(4,dtype=int))
    assert np.array_equal(out[:4,4:8],np.roll(np.eye(4,dtype=int),1,axis=1))
    assert not out[:4,8:].any()
def test_modulo():
    assert np.array_equal(expand_qc(np.array([[5]]),4),np.roll(np.eye(4,dtype=int),1,axis=1))

def test_complete_matrix():
    expected=np.zeros((8,12),dtype=int)
    # Independent, explicit row/column coordinates: all blocks, not only one.
    pairs=[(0,0),(0,5),(1,1),(1,6),(2,2),(2,7),(3,3),(3,4),
           (4,2),(4,8),(5,3),(5,9),(6,0),(6,10),(7,1),(7,11)]
    for row,col in pairs: expected[row,col]=1
    assert np.array_equal(expand_qc(np.array([[0,1,-1],[2,-1,0]]),4),expected)

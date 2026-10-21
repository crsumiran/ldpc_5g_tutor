import numpy as np
from gf2 import gf2_dot

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_even():
    assert gf2_dot(np.array([1,1,1]), np.array([1,0,1])) == 0
def test_odd():
    assert gf2_dot(np.array([1,0,1]), np.array([1,1,0])) == 1
def test_empty():
    assert gf2_dot(np.array([],dtype=int), np.array([],dtype=int)) == 0


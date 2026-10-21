import numpy as np
from variable import variable_messages

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_values():
    p,q=variable_messages(2.,np.array([3.,-1.])); assert p == 4 and np.allclose(q,[1,5])
def test_no_neighbors():
    p,q=variable_messages(-2.,np.array([])); assert p == -2 and len(q)==0


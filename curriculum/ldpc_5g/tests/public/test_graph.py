import numpy as np
from graph import check_neighbors

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_neighbors():
    assert check_neighbors(H) == [[0,1,3],[1,2,4],[0,2,5]]
def test_empty_row():
    assert check_neighbors(np.array([[0,0],[1,0]])) == [[],[0]]


import numpy as np
from decoder import decode_toy

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_already_valid():
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([3.,3.,3.]),5)
    assert np.array_equal(out['bits'],[0,0,0]) and out['iterations']==0 and out['syndrome_weights']==[0]
def test_repair():
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([-.2,3.,3.]),5)
    assert np.array_equal(out['bits'],[0,0,0]) and out['iterations']==1 and out['syndrome_weights']==[1,0]
def test_bounded():
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([-.2,3.,3.]),0)
    assert np.array_equal(out['bits'],[1,0,0]) and out['iterations']==0

def test_two_rounds():
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([3.,-1.,-1.]),2)
    assert np.array_equal(out['bits'],[0,0,0]) and out['iterations']==2
    assert out['syndrome_weights']==[1,1,0]

def test_wrong_but_valid():
    # Simulation sent 000. The decoder cannot see this truth: 111 is also legal.
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([-3.,-3.,-3.]),5)
    assert np.array_equal(out['bits'],[1,1,1]) and out['iterations']==0
    assert out['syndrome_weights']==[0]

def test_cap_before_valid():
    out=decode_toy(np.array([[1,1,0],[0,1,1]]),np.array([3.,-1.,-1.]),1)
    assert np.array_equal(out['bits'],[0,0,1]) and out['iterations']==1
    assert out['syndrome_weights']==[1,1]

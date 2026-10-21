import numpy as np
from lanes import lane_plan

H=np.array([[1,1,0,1,0,0],[0,1,1,0,1,0],[1,0,1,0,0,1]])

def test_full():
    p=lane_plan(384,32); assert p['groups']==12 and p['valid']==[32]*12 and p['utilization']==1
def test_partial():
    p=lane_plan(104,32); assert p['groups']==4 and p['valid']==[32,32,32,8] and p['utilization']==.8125
def test_one():
    p=lane_plan(2,32); assert p['groups']==1 and p['valid']==[2]


"""Independent author-only sanity checks. Never copied into learner assets."""
import importlib.util
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch

import numpy as np
import pytest

from app.verilog.manifest import load_course
from app.ldpc.theory import load_theory
from app.ldpc.tutor import get_python_tutor_reply


def baselines():
    def gradients(frame0,frame1):
        a=np.asarray(frame0,dtype=float);b=np.asarray(frame1,dtype=float)
        iy,ix=np.gradient(a)
        return ix,iy,b-a
    def patch_system(ix,iy,it,x,y,radius):
        h,w=ix.shape
        if x-radius<0 or y-radius<0 or x+radius>=w or y+radius>=h:raise ValueError('border')
        coords=[(yy,xx) for yy in range(y-radius,y+radius+1) for xx in range(x-radius,x+radius+1)]
        return np.array([[ix[yy,xx],iy[yy,xx]] for yy,xx in coords]),np.array([-it[yy,xx] for yy,xx in coords])
    def solve_window(a,b,min_eigenvalue=1e-6):
        low=float(np.linalg.eigvalsh(a.T@a/len(a))[0]);ok=low>=min_eigenvalue
        return dict(uv=np.linalg.lstsq(a,b,rcond=None)[0] if ok else np.zeros(2),valid=bool(ok),min_eigenvalue=low)
    def dense_lk(frame0,frame1,radius=1,min_eigenvalue=1e-6):
        ix,iy,it=gradients(frame0,frame1);h,w=frame0.shape;flow=np.zeros((h,w,2));valid=np.zeros((h,w),bool)
        for y in range(radius,h-radius):
            for x in range(radius,w-radius):
                a,b=patch_system(ix,iy,it,x,y,radius);fit=solve_window(a,b,min_eigenvalue)
                flow[y,x]=fit['uv'];valid[y,x]=fit['valid']
        return flow,valid
    def bilinear_sample(image,x,y):
        h,w=image.shape;out=np.zeros(x.shape);mask=np.zeros(x.shape,bool)
        for index in np.ndindex(x.shape):
            xx=float(x[index]);yy=float(y[index])
            if not (0<=xx<=w-1 and 0<=yy<=h-1):continue
            x0=int(np.floor(xx));y0=int(np.floor(yy));a=xx-x0;b=yy-y0
            for dx,wx in [(0,1-a),(1,a)]:
                for dy,wy in [(0,1-b),(1,b)]:out[index]+=wx*wy*image[min(y0+dy,h-1),min(x0+dx,w-1)]
            mask[index]=True
        return out,mask
    def warp_frame(frame1,flow):
        y,x=np.mgrid[:frame1.shape[0],:frame1.shape[1]]
        return bilinear_sample(frame1,x+flow[...,0],y+flow[...,1])
    def refine_flow(frame0,frame1,initial_flow,iterations=3,radius=1,min_eigenvalue=1e-6):
        flow=initial_flow.copy();valid=np.zeros(frame0.shape,bool);h,w=frame0.shape
        ix,iy,_=gradients(frame0,frame1)
        for _ in range(iterations):
            valid=np.zeros(frame0.shape,bool)
            for y in range(radius,h-radius):
                for x in range(radius,w-radius):
                    yy,xx=np.mgrid[y-radius:y+radius+1,x-radius:x+radius+1]
                    sampled,support=bilinear_sample(frame1,xx+flow[y,x,0],yy+flow[y,x,1])
                    if not support.all():continue
                    a=np.stack([ix[yy,xx].ravel(),iy[yy,xx].ravel()],axis=1)
                    rhs=(frame0[yy,xx]-sampled).ravel();fit=solve_window(a,rhs,min_eigenvalue)
                    valid[y,x]=fit['valid']
                    if fit['valid']:flow[y,x]+=fit['uv']
        return flow,valid
    def reduce_half(image):
        kernel=np.array([1.,4,6,4,1])/16
        # Independent 2-D convolution oracle, rather than separable learner implementation.
        padded=np.pad(np.asarray(image,float),2,mode='reflect');h,w=image.shape
        return np.array([[sum(kernel[dy]*kernel[dx]*padded[y+dy,x+dx] for dy in range(5) for dx in range(5)) for x in range(0,w,2)] for y in range(0,h,2)])
    def upsample_flow(flow,target_shape):
        h,w=target_shape;y,x=np.mgrid[:h,:w]
        coords=(np.minimum(x/2,flow.shape[1]-1),np.minimum(y/2,flow.shape[0]-1))
        return np.stack([2*bilinear_sample(flow[...,c],*coords)[0] for c in range(2)],axis=-1)
    def pyramidal_flow(frame0,frame1,levels=3,iterations=3,radius=1,min_eigenvalue=1e-6):
        p0=[frame0];p1=[frame1]
        for _ in range(levels-1):p0.append(reduce_half(p0[-1]));p1.append(reduce_half(p1[-1]))
        if any(min(a.shape)<max(2,2*radius+1) for a in p0):raise ValueError('too many levels')
        flow=np.zeros((*p0[-1].shape,2));valid=None
        for level in reversed(range(levels)):
            if level<levels-1:flow=upsample_flow(flow,p0[level].shape)
            flow,valid=refine_flow(p0[level],p1[level],flow,iterations,radius,min_eigenvalue)
        return flow,valid
    def endpoint_error(estimate,truth,mask):
        errors=np.full(mask.shape,np.nan);errors[mask]=np.sqrt(np.sum((estimate[mask]-truth[mask])**2,axis=-1))
        return dict(errors=errors,mean=float(np.mean(errors[mask])) if mask.any() else float('nan'),count=int(mask.sum()))
    def fb_consistency(forward,backward,forward_valid,backward_valid,threshold=.5):
        y,x=np.mgrid[:forward.shape[0],:forward.shape[1]];xx=x+forward[...,0];yy=y+forward[...,1]
        bx,in_bounds=bilinear_sample(backward[...,0],xx,yy);by,_=bilinear_sample(backward[...,1],xx,yy)
        reverse_valid,_=bilinear_sample(backward_valid.astype(float),xx,yy)
        distance=np.hypot(forward[...,0]+bx,forward[...,1]+by)
        return forward_valid & in_bounds & np.isclose(reverse_valid,1) & (distance<=threshold)
    return locals()


def test_course_contracts_and_theory():
    manifest,root=load_course('optical-flow')
    assert manifest.toolchain=='python' and len(manifest.checkpoints)==12
    pages=load_theory(root)
    assert len(pages)==5
    assert {c.id for c in manifest.checkpoints}=={c.id for p in pages for c in p.connections}
    for c in manifest.checkpoints:
        assert len(c.hints)==3 and c.lesson and c.experiment and c.fixture
        assert 'NotImplementedError' in (root/'starter'/c.editable_files[0]).read_text()
        assert 'What changes and what stays fixed' not in c.lesson
        assert all(len(r)==len(v['columns']) for v in c.fixture['views'] for r in v['rows'])
    assert sum(c.expected_public_checks for c in manifest.checkpoints)==36
    assert not list((root/'starter').rglob('*reference*'))


@pytest.mark.parametrize('index',range(12))
def test_public_cases_against_author_baselines(index,monkeypatch):
    manifest,root=load_course('optical-flow');functions=baselines()
    for cp in manifest.checkpoints:
        module=types.ModuleType(cp.module)
        fn=next(v for k,v in functions.items() if callable(v) and ('def '+k+'(') in (root/'starter'/cp.editable_files[0]).read_text())
        setattr(module,fn.__name__,fn);monkeypatch.setitem(sys.modules,cp.module,module)
    provided=types.ModuleType('provided');provided.__path__=[str(root/'python/provided')]
    monkeypatch.setitem(sys.modules,'provided',provided)
    monkeypatch.delitem(sys.modules,'provided.scene',raising=False)
    c=manifest.checkpoints[index];spec=importlib.util.spec_from_file_location('public_flow_suite',root/c.public_testbench)
    suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
    cases=[v for k,v in vars(suite).items() if k.startswith('test_')]
    assert len(cases)==c.expected_public_checks
    for case in cases:case()


def test_guide_is_optical_and_includes_shapes_and_evidence():
    manifest,_=load_course('optical-flow');cp=manifest.checkpoints[1]
    with patch('app.ldpc.tutor.complete',return_value={'content':'A has N rows and two columns; b has N values, one per selected pixel.'}) as model:
        reply,_=get_python_tutor_reply(cp,{},'What are the exact input and output sizes?',api_key_override='synthetic')
    system=model.call_args.args[0][0]['content'];context=json.loads(model.call_args.args[0][1]['content'])
    assert system.startswith('You teach optical flow') and 'including every part' in system
    assert context['checkpoint']['requirements']==cp.requirements
    assert context['checkpoint']['fixture']==cp.fixture and model.call_count==1 and reply.source=='model'


def test_runner_selects_manifest_course_not_ldpc(tmp_path):
    from app.ldpc.runner import run_python_checkpoint
    manifest,root=load_course('optical-flow');workspace=tmp_path/'workspace';(workspace/'python').mkdir(parents=True)
    (workspace/'python/gradients.py').write_text((root/'starter/python/gradients.py').read_text())
    with patch('app.ldpc.runner.run_sandbox',return_value=(0,'','',False)) as sandbox:
        result=run_python_checkpoint(root,workspace,'FLOW-01','compile')
    assert result.compile.ok and sandbox.call_count==1


def test_optical_theory_and_assignment_chat_api():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    assert any(c['id']=='optical-flow' for c in client.get('/api/courses').json())
    session=client.post('/api/courses/optical-flow/sessions',json={}).json()
    endpoint=f"/api/lab-sessions/{session['id']}/tutor"
    with patch('app.ldpc.tutor.complete',return_value={'content':'Forward flow maps a first-frame point to its destination, so pull-warping reads the second frame at x+u and y+v.','_served_model':'synthetic-flow'}) as model:
        response=client.post(endpoint,headers={'X-OpenRouter-Api-Key':'synthetic-only'},json={
            'checkpoint_id':'FLOW-01','theory_page_id':'alignment','message':'Why is the warp direction positive?'})
        assert response.status_code==200 and response.json()['reply']['source']=='model'
        context=json.loads(model.call_args.args[0][1]['content'])
        assert context['theory_page']['id']=='alignment' and 'files' not in context and 'run' not in context
        response=client.post(endpoint,headers={'X-OpenRouter-Api-Key':'synthetic-only'},json={
            'checkpoint_id':'FLOW-01','message':'What are the input and output shapes?'})
        assert response.status_code==200
        context=json.loads(model.call_args.args[0][1]['content'])
        assert context['checkpoint']['id']=='FLOW-01' and 'python/gradients.py' in context['files']
        assert model.call_count==2
    unchanged=client.get(f"/api/lab-sessions/{session['id']}").json()
    assert unchanged['passed_checkpoint_ids']==[]

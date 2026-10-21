"""Opt-in offline Docker checks; author baselines stay in disposable storage."""
import importlib.util
import inspect
import os
from pathlib import Path
import textwrap

import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.verilog.manifest import load_course
from app.ldpc.runner import run_python_checkpoint

pytestmark=pytest.mark.skipif(os.environ.get('FLOW_DOCKER_SMOKE')!='1',reason='Opt-in Docker smoke')


def test_course_api_todo_run_and_unlock():
    assert '/tmp/' in settings.data_dir, 'Never use learner data for this test'
    client=TestClient(app)
    course=client.get('/api/courses/optical-flow')
    assert course.status_code==200 and len(course.json()['theory_pages'])==5
    session=client.post('/api/courses/optical-flow/sessions',json={}).json();sid=session['id']
    workspace=Path(settings.data_dir)/'labs'/sid/'workspace'
    assert 'NotImplementedError' in (workspace/'python/gradients.py').read_text()
    assert client.post(f'/api/lab-sessions/{sid}/runs',json={'checkpoint_id':'FLOW-02','mode':'test'}).status_code==403
    run_id=client.post(f'/api/lab-sessions/{sid}/runs',json={'checkpoint_id':'FLOW-01','mode':'test'}).json()['run_id']
    run=client.get('/api/lab-runs/'+run_id).json()
    assert run['result']['tests']['failed']==3 and not run['result']['passed']
    # This solution is created only in the disposable test session.
    source='import numpy as np\ndef gradients(frame0, frame1):\n    a=np.asarray(frame0,float); b=np.asarray(frame1,float)\n    iy,ix=np.gradient(a)\n    return ix,iy,b-a\n'
    assert client.put(f'/api/lab-sessions/{sid}/files/python/gradients.py',json={'content':source}).status_code==200
    run_id=client.post(f'/api/lab-sessions/{sid}/runs',json={'checkpoint_id':'FLOW-01','mode':'submit'}).json()['run_id']
    run=client.get('/api/lab-runs/'+run_id).json()
    assert run['result']['passed'] and run['result']['tests']['passed']==3
    assert client.get(f'/api/lab-sessions/{sid}').json()['checkpoints'][1]['status']=='available'
    assert client.get(f'/api/lab-runs/{run_id}/artifacts/public-report.json').status_code==200


def test_all_36_public_cases_in_real_sandbox(tmp_path):
    assert '/tmp/' in settings.data_dir
    manifest,root=load_course('optical-flow')
    spec=importlib.util.spec_from_file_location('flow_author',Path(__file__).with_name('test_optical_flow.py'))
    author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    functions=author.baselines();work=tmp_path/'work';(work/'python').mkdir(parents=True)
    for cp in manifest.checkpoints:
        starter=(root/'starter'/cp.editable_files[0]).read_text()
        fn=next(v for k,v in functions.items() if callable(v) and 'def '+k+'(' in starter)
        imports='\n'.join(line for line in starter.splitlines() if line.startswith(('import ','from ')))
        (work/cp.editable_files[0]).write_text(imports+'\n\n'+textwrap.dedent(inspect.getsource(fn)))
    total=0
    for cp in manifest.checkpoints:
        result=run_python_checkpoint(root,work,cp.id,'test',tmp_path/cp.id)
        assert result.passed,(cp.id,result.output)
        total+=result.tests.passed
    assert total==36

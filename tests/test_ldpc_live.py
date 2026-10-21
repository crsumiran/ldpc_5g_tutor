"""Opt-in real Docker/API smoke, always use a disposable DATA_DIR and database."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.ldpc.runner import run_python_checkpoint
from app.verilog.manifest import load_course


@pytest.mark.skipif(os.environ.get("LDPC_DOCKER_SMOKE") != "1",reason="Opt-in Docker smoke")
def test_python_api_fail_pass_unlock_artifact_and_syntax(tmp_path):
    assert "/tmp/" in settings.data_dir, "Use disposable storage, never learner data"
    client=TestClient(app)
    assert client.get("/api/courses/ldpc-5g").status_code==200
    session=client.post("/api/courses/ldpc-5g/sessions",json={}).json()
    sid=session['id']; workspace=Path(settings.data_dir)/"labs"/sid/"workspace"
    assert client.post(f"/api/lab-sessions/{sid}/runs",json={"checkpoint_id":"LDPC-02","mode":"test"}).status_code==403
    failed=client.post(f"/api/lab-sessions/{sid}/runs",json={"checkpoint_id":"LDPC-01","mode":"test"})
    run=client.get("/api/lab-runs/"+failed.json()['run_id']).json()
    assert run['status']=="done",run
    assert not run['result']['passed'] and run['result']['tests']['failed']==3,run
    assert 'INPUT:' in run['result']['output'] and 'EXPECTED OUTPUT:' in run['result']['output']
    assert 'NotImplementedError' in run['result']['output']
    source="def gf2_dot(a,b):\n    return sum(int(x)*int(y) for x,y in zip(a,b))%2\n"
    assert client.put(f"/api/lab-sessions/{sid}/files/python/gf2.py",json={"content":source}).status_code==200
    submitted=client.post(f"/api/lab-sessions/{sid}/runs",json={"checkpoint_id":"LDPC-01","mode":"submit"})
    run_id=submitted.json()['run_id'];run=client.get("/api/lab-runs/"+run_id).json()
    assert run['result']['passed'] and run['result']['tests']['passed']==3,run
    assert run['result']['output'].count('EXPECTED OUTPUT:')==3
    assert run['result']['output'].count('ACTUAL OUTPUT:')==3
    assert run['result']['hidden'] is None
    assert client.get(f"/api/lab-runs/{run_id}/artifacts/public-report.json").status_code==200
    assert client.get(f"/api/lab-runs/{run_id}/artifacts/source").status_code==404
    assert client.get(f"/api/lab-sessions/{sid}").json()['checkpoints'][1]['status']=="available"
    assert (workspace/"python/gf2.py").read_text()==source
    snapshot=Path(settings.data_dir)/"labs/runs"/run_id/"source/python/gf2.py"
    assert snapshot.read_text()==source
    client.put(f"/api/lab-sessions/{sid}/files/python/gf2.py",json={"content":"def broken(:\n"})
    assert snapshot.read_text()==source
    syntax=client.post(f"/api/lab-sessions/{sid}/runs",json={"checkpoint_id":"LDPC-01","mode":"compile"}).json()
    result=client.get("/api/lab-runs/"+syntax['run_id']).json()['result']
    assert not result['compile']['ok'] and result['stage']=="compile"


@pytest.mark.skipif(os.environ.get("LDPC_DOCKER_SMOKE") != "1",reason="Opt-in Docker smoke")
def test_numpy_and_provided_assets_in_offline_sandbox(tmp_path):
    assert "/tmp/" in settings.data_dir
    manifest,root=load_course("ldpc-5g")
    work=tmp_path/"work"; (work/"python").mkdir(parents=True)
    # The runner must use the trusted provided lifting sets, without networking.
    import shutil
    for cp in manifest.checkpoints[:13]:
        for name in cp.editable_files:
            shutil.copy2(root/"starter"/name,work/name)
    (work/"python/lifting.py").write_text("from provided.nr_sets import LIFTING_SETS\ndef lifting_set_index(z):\n    for i,s in enumerate(LIFTING_SETS):\n        if z in s:return i\n    raise ValueError()\n")
    result=run_python_checkpoint(root,work,"LDPC-13","test",tmp_path/"artifacts")
    assert result.passed and result.tests.passed==3,result.output
    assert 'EXPECTED OUTPUT:' in result.output and 'ValueError' in result.output


@pytest.mark.skipif(os.environ.get("LDPC_DOCKER_SMOKE") != "1",reason="Opt-in Docker smoke")
def test_minima_todo_reports_all_six_checks(tmp_path):
    import shutil
    manifest,root=load_course("ldpc-5g")
    work=tmp_path/"work";(work/"python").mkdir(parents=True)
    shutil.copy2(root/"starter/python/minima.py",work/"python/minima.py")
    result=run_python_checkpoint(root,work,"LDPC-18","test",tmp_path/"artifacts")
    assert not result.passed and result.tests.failed==6 and result.tests.errors==0,result.output
    assert len(result.tests.cases)==6
    assert result.output.count('EXPECTED OUTPUT:')==6

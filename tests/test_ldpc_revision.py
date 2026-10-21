import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.verilog.manifest import load_course
from app.verilog.workspace import ensure_lab_workspace_assets, allowed_editable_files
from app.ldpc.theory import load_theory
from app.ldpc.tutor import get_python_tutor_reply


def test_revision_contract_and_shared_examples():
    manifest,root=load_course('ldpc-5g')
    fixtures=json.loads((root/'fixtures.json').read_text())
    for c in manifest.checkpoints:
        assert c.fixture and c.experiment and c.takeaway and c.completion
        assert c.optional_math and c.optional_hardware and c.misconception
        assert c.fixture['views'] and c.fixture['visual_spec']['text_fallback']
        assert 'NotImplementedError' in (root/'starter'/c.editable_files[0]).read_text()
    assert manifest.checkpoints[-1].prerequisites==['LDPC-05']
    assert load_theory(root)[3].fixture==fixtures['toy-edges']
    assert load_theory(root)[4].fixture==fixtures['flooding-chain']
    edges=fixtures['toy-edges']['edges']
    assert [(e['check'],e['bit']) for e in edges]==[(0,0),(0,1),(0,3),(1,1),(1,2),(1,4),(2,0),(2,2),(2,5)]
    assert np.array(fixtures['qc-full']['expanded']).shape==(8,12)
    assert np.array(fixtures['qc-full']['expanded']).sum()==16


def test_assignments_explain_locally_without_revision_boilerplate():
    manifest,_=load_course('ldpc-5g')
    for checkpoint in manifest.checkpoints:
        assert '## Your task' in checkpoint.lesson
        assert not checkpoint.lesson.startswith('##')
        for phrase in ['What changes and what stays fixed','Recap before coding',
                       'Your bounded task','What the result can establish',
                       'Existing IDs and prerequisites are unchanged','SAME equality chain']:
            assert phrase not in checkpoint.lesson
    first=manifest.checkpoints[0].lesson
    for phrase in ['even number of ones','mask entry of 1','equal values XOR',
                   'a bit AND 1','GF(2)','empty','equal lengths']:
        assert phrase in first
    assert first.index('even number of ones') < first.index('GF(2)')
    assert 'H=[[1,1,0,1,0,0]' in manifest.checkpoints[1].lesson
    assert 'confidence score' in manifest.checkpoints[3].lesson


def test_additive_migration_preserves_edits_and_is_idempotent(tmp_path):
    manifest,root=load_course('ldpc-5g')
    workspace=tmp_path/'workspace';(workspace/'python').mkdir(parents=True)
    original=workspace/'python/gf2.py'; original.write_text('# MY COMPLETED ASSIGNMENT\n')
    ensure_lab_workspace_assets(root,manifest,workspace)
    new=workspace/'python/minima.py'
    assert 'NotImplementedError' in new.read_text()
    new.write_text('# MY NEW WORK\n')
    ensure_lab_workspace_assets(root,manifest,workspace)
    assert original.read_text()=='# MY COMPLETED ASSIGNMENT\n'
    assert new.read_text()=='# MY NEW WORK\n'
    assert 'python/minima.py' in allowed_editable_files(manifest,{'LDPC-05'},'LDPC-06')
    assert 'python/minima.py' not in allowed_editable_files(manifest,set(),'LDPC-01')


def test_migration_rejects_symlink(tmp_path):
    manifest,root=load_course('ldpc-5g')
    workspace=tmp_path/'workspace'; workspace.mkdir()
    outside=tmp_path/'outside';outside.mkdir()
    (workspace/'python').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError):ensure_lab_workspace_assets(root,manifest,workspace)
    assert not list(outside.iterdir())


def test_guide_receives_exact_worked_state_without_extra_calls():
    manifest,_=load_course('ldpc-5g');checkpoint=manifest.checkpoints[6]
    with patch('app.ldpc.tutor.complete',return_value={'content':'Checks read old q before forming new q.'}) as model:
        get_python_tutor_reply(checkpoint,{},'Why does round two change?',api_key_override='synthetic')
    context=json.loads(model.call_args.args[0][1]['content'])
    assert context['checkpoint']['fixture']==checkpoint.fixture
    assert model.call_count==1


def test_worked_numeric_tables_against_independent_baseline():
    # Fixtures are NOT the oracle: recompute their arithmetic independently.
    import importlib.util
    spec=importlib.util.spec_from_file_location('author_baseline',Path(__file__).with_name('test_ldpc_course.py'))
    author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
    _,root=load_course('ldpc-5g');f=json.loads((root/'fixtures.json').read_text())
    b=author.baseline_modules(); array=lambda value: np.array(json.loads(value))
    for fixture in f.values():
        for view in fixture['views']+[v for option in fixture.get('variants',[]) for v in option['views']]:
            assert all(len(row)==len(view['columns']) for row in view['rows'])
    for bit,value,mask,contribution in f['gf2-mask']['views'][0]['rows']:
        assert contribution==(value&mask)
    for a,c,out in f['gf2-mask']['views'][1]['rows']:assert out==(a^c)
    h=np.array(f['toy-edges']['matrix'])
    for word,payload,s in f['toy-encode']['views'][3]['rows']:
        assert np.array_equal(b['syndrome'](array(word),h),array(s))
        assert np.array_equal(array(word)[:3],array(payload))
    for candidate,s,weight in f['toy-encode']['views'][2]['rows']:
        measured=b['syndrome'](array(candidate),h)
        assert np.array_equal(measured,array(s)) and sum(measured)==weight
    for view in f['awgn-llr']['views']+[v for option in f['awgn-llr']['variants'] for v in option['views']]:
        for y,variance,llr,bit in view['rows']:
            assert llr==pytest.approx(2*y/variance) and bit==int(llr<0)
    for dest,excluded,others,r in f['check-exclusion']['views'][0]['rows']:
        inputs=array(others);sign=np.prod(np.where(inputs<0,-1,1))
        assert r==sign*np.min(np.abs(inputs))
    for dest,channel,others,r,posterior in f['check-exclusion']['views'][1]['rows']:
        inputs=array(others);assert r==np.prod(np.where(inputs<0,-1,1))*np.min(np.abs(inputs))
        assert posterior==pytest.approx(channel+r)
    rows=f['variable-contributions']['views'][0]['rows'];values=[row[-1] for row in rows]
    a,q=b['variable_messages'](values[0],np.array(values[1:3]))
    assert a==values[3] and np.array_equal(q,values[4:])
    chain=np.array([[1,1,0],[0,1,1]]);channel=np.array([3.,-1.,-1.]);q=chain*channel
    arrays=f['flooding-chain']['views'][3]['rows'];stages=f['flooding-chain']['views'][2]['rows']
    for round_index in [0,1]:
        assert np.array_equal(q,array(arrays[0][round_index+1]))
        r,q,a=b['flooding_step'](chain,channel,q)
        assert np.array_equal(r,array(arrays[1][round_index+1]))
        assert np.array_equal(q,array(arrays[2][round_index+1]))
        _,expected_a,bits,s,weight=stages[round_index+1]
        assert np.array_equal(a,array(expected_a)) and np.array_equal(b['hard_decisions'](a),array(bits))
        assert np.array_equal(b['syndrome'](array(bits),chain),array(s)) and sum(array(s))==weight
    outcomes=f['decoder-outcomes']['views'][1]['rows']
    for row,(llr,cap) in zip(outcomes,[(channel,2),(np.array([-3.,-3.,-3.]),5),(channel,1)]):
        out=b['decode_toy'](chain,llr,cap)
        assert np.array_equal(out['bits'],array(row[1])) and out['iterations']==row[2]
        assert out['syndrome_weights']==json.loads(row[3])
    for row,(alpha,beta) in zip(f['correction-modes']['views'][0]['rows'],[(1,0),(1,1),(.5,0)]):
        assert np.allclose(b['corrected_messages'](np.array([7.,-3.,5.,-9.]),alpha,beta),array(row[-1]))
    a=channel.copy()
    for row in f['layered-chain']['views'][0]['rows'][1:]:
        indices=array(row[1]);a,r=b['layer_update'](a,np.zeros(2),indices)
        assert np.array_equal(r,array(row[3])) and np.array_equal(a,array(row[4]))
    assert np.array_equal(b['qc_rotate'](np.arange(8),3),array(f['rotation-directions']['views'][1]['rows'][0][1]))
    expanded=b['expand_qc'](np.array([[0,1,-1],[2,-1,0]]),4)
    assert np.array_equal(expanded,f['qc-full']['expanded'])
    rendered=np.array([[int(x) for group in row[1:] for x in group.split()] for row in f['qc-full']['views'][0]['rows']])
    assert np.array_equal(rendered,expanded)
    for value,lo,hi,out in f['saturation-boundaries']['views'][0]['rows']:
        assert (lo,hi)==(-8,7) and out==b['saturate_signed']([value],4)[0]
    for real,scaled,rounded,code,reconstructed in f['quantize-pipeline']['views'][0]['rows']:
        assert scaled==real*2 and rounded==np.rint(scaled)
        assert code==b['quantize_signed'](np.array([real]),4,1)[0] and reconstructed==code/2
    for z,groups,valid,utilization in f['lane-schedule']['views'][0]['rows']:
        plan=b['lane_plan'](z,32);assert plan['groups']==groups and plan['utilization']==utilization
    cycles=f['lane-schedule']['views'][2]['rows']
    assert len(cycles)==24 and [r[0] for r in cycles]==list(range(1,25))
    assert [r[4] for r in cycles]==[32,32,32,8]*6
    for addr,bank,within in f['bank-service']['views'][0]['rows']:
        assert bank==addr%4 and within==addr//4
    for edge,i,addr,bank,within in f['bank-service']['views'][2]['rows']:
        assert addr==i if edge=='B[0,0]=0' else addr==4+(i+1)%4
        assert bank==addr%4 and within==addr//4
    for q,m1,m2,index,parity,outgoing in f['minima-summary']['views'][0]['rows']:
        result=b['check_messages_fast'](array(q))
        assert (m1,m2,index,parity)==(result['min1'],result['min2'],result['argmin'],result['negative_parity'])
        assert np.array_equal(result['outgoing'],array(outgoing))

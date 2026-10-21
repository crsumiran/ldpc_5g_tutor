import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from app.verilog.manifest import load_course
from app.ldpc.tutor import get_python_tutor_reply


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('index',range(18))
def test_every_public_case_prints_inputs_expected_and_actual(index,tmp_path,capsys):
    manifest,root=load_course('ldpc-5g');checkpoint=manifest.checkpoints[index]
    repo=root.parents[1]
    baseline=load_module('trace_author',repo/'tests/test_ldpc_course.py').baseline_modules()
    with patch.dict(sys.modules):
        for cp in manifest.checkpoints:
            module=types.ModuleType(cp.module)
            function=next(fn for name,fn in baseline.items() if callable(fn) and f'def {name}(' in (root/'starter'/cp.editable_files[0]).read_text())
            setattr(module,function.__name__,function);sys.modules[cp.module]=module
        provided=types.ModuleType('provided');provided.__path__=[str(root/'python/provided')];sys.modules['provided']=provided
        suite=load_module('public_trace_suite',root/checkpoint.public_testbench)
        plugin=load_module('public_trace_plugin',root/'tests/teaching_conftest.py')
        teaching=json.loads((root/'public_cases.json').read_text())[checkpoint.id]
        (tmp_path/'teaching_case.json').write_text(json.dumps(teaching))
        plugin.__file__=str(tmp_path/'conftest.py')
        cases={name:fn for name,fn in vars(suite).items() if name.startswith('test_')}
        assert set(cases)==set(teaching['cases'])
        assert len(cases)==checkpoint.expected_public_checks
        for name,case in cases.items():
            request=types.SimpleNamespace(module=suite,node=types.SimpleNamespace(originalname=name,name=name))
            with pytest.MonkeyPatch.context() as mp:
                fixture=plugin.print_public_case.__wrapped__(request,mp)
                next(fixture)
                case() # Assertions remain exactly those of the public suite.
                with pytest.raises(StopIteration):next(fixture)
            output=capsys.readouterr().out
            count=len(teaching['cases'][name])
            assert count>0
            assert output.count('INPUT: ')==count
            assert output.count('EXPECTED OUTPUT: ')==count
            assert output.count('ACTUAL OUTPUT: ')==count
            assert output.index('INPUT: ')<output.index('EXPECTED OUTPUT: ')<output.index('ACTUAL OUTPUT: ')
            # Expected values are static author data, not copied from the
            # learner result. Recheck every printed expectation independently.
            actuals=[json.loads(line.removeprefix('ACTUAL OUTPUT: ')) for line in output.splitlines() if line.startswith('ACTUAL OUTPUT: ')]
            def without_dtype(value):
                if isinstance(value,dict):return {k:without_dtype(v) for k,v in value.items() if k!='dtype'}
                if isinstance(value,list):return [without_dtype(v) for v in value]
                return value
            for expected,actual in zip(teaching['cases'][name],actuals):
                if 'raises' in expected:assert actual['raises']==expected['raises']
                else:assert without_dtype(actual)==expected['result']


def test_trace_prints_expectation_before_learner_exception(tmp_path,capsys,monkeypatch):
    _,root=load_course('ldpc-5g');plugin=load_module('trace_exception_plugin',root/'tests/teaching_conftest.py')
    plugin.__file__=str(tmp_path/'conftest.py')
    (tmp_path/'teaching_case.json').write_text(json.dumps({'function':'example','cases':{'test_example':[{'result':[1,0]}]}}))
    def example(q):raise NotImplementedError('learner TODO')
    module=types.SimpleNamespace(example=example)
    request=types.SimpleNamespace(module=module,node=types.SimpleNamespace(originalname='test_example',name='test_example'))
    fixture=plugin.print_public_case.__wrapped__(request,monkeypatch);next(fixture)
    with pytest.raises(NotImplementedError):module.example([1,2])
    with pytest.raises(StopIteration):next(fixture)
    output=capsys.readouterr().out
    assert 'EXPECTED OUTPUT: {"result": [1, 0]}' in output
    assert 'NotImplementedError' in output


def test_model_explanation_survives_appended_solution_function():
    manifest,_=load_course('ldpc-5g')
    prose='Your diagonal assignment modifies a temporary copy. Every row therefore keeps the same minimum, producing [-3,-3,-3,-3] instead of [3,-5,3,-3]. Also combine the signs of all other inputs, rather than copying the sign of the minimum.'
    answer=prose+'\n\n```python\ndef check_messages(q):\n    return q * 0\n```'
    with patch('app.ldpc.tutor.complete',return_value={'content':answer,'_served_model':'synthetic'}) as model:
        reply,text=get_python_tutor_reply(manifest.checkpoints[4],{},'can you explain what is failing',api_key_override='synthetic')
    assert reply.source=='model' and prose in text
    assert 'def check_messages' not in text and 'Complete function omitted' in text
    assert 'Guide model unavailable' not in text and model.call_count==1


@pytest.mark.parametrize('snippet',['`def syndrome(bits, h):`','```python\ndef syndrome(bits, h):\n    pass\n```'])
def test_interface_description_is_not_mistaken_for_a_full_solution(snippet):
    manifest,_=load_course('ldpc-5g')
    answer='The interface is '+snippet+'\nInput bits has shape (n,), H has shape (m,n), and the result has shape (m,).'
    with patch('app.ldpc.tutor.complete',return_value={'content':answer}):
        reply,text=get_python_tutor_reply(manifest.checkpoints[1],{},'What input format?',api_key_override='synthetic')
    assert reply.source=='model' and '(m,n)' in text


def test_function_only_answer_still_has_an_honest_fallback():
    manifest,_=load_course('ldpc-5g')
    with patch('app.ldpc.tutor.complete',return_value={'content':'```python\ndef check_messages(q):\n    return q * 0\n```'}):
        reply,text=get_python_tutor_reply(manifest.checkpoints[4],{},'Why?',api_key_override='synthetic')
    assert reply.source=='fallback' and 'without a useful explanation' in text
    assert 'return q * 0' not in text

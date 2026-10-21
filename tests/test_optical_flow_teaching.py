"""Independent arithmetic and content wiring checks; not learner grading tests."""
import json
from pathlib import Path
import numpy as np
from app.ldpc.theory import load_theory
from app.verilog.manifest import load_course
from app.verilog.schemas import TheorySection

ROOT=Path(__file__).resolve().parents[1]


def test_nine_equations_and_candidate_errors():
    y,x=np.mgrid[1:4,1:4].astype(float)
    a=np.column_stack((y.ravel(),x.ravel()))
    b=(.5*y-.25*x).ravel()
    np.testing.assert_allclose(b,[.25,0,-.25,.75,.5,.25,1.25,1,.75])
    np.testing.assert_allclose(a.T@a,[[42,36],[36,42]])
    np.testing.assert_allclose(a.T@b,[12,7.5])
    np.testing.assert_allclose(np.linalg.eigvalsh(a.T@a/9),[2/3,26/3])
    np.testing.assert_allclose([np.sum((a@q-b)**2) for q in [[0,0],[.5,0],[.5,-.25]]],[4.125,2.625,0])
    np.testing.assert_allclose(np.linalg.lstsq(a,b,rcond=None)[0],[.5,-.25])
    # Dense assignment uses a distinct manufactured linear measurement.
    np.testing.assert_allclose(a.T@(.1*y-.2*x).ravel(),[-3,-4.8])


def test_bilinear_contributions_and_actual_refinement():
    weights=np.array([.75*.5,.25*.5,.75*.5,.25*.5])
    np.testing.assert_allclose(weights,[.375,.125,.375,.125])
    np.testing.assert_allclose(weights*np.array([0,10,20,30]),[0,1.25,7.5,3.75])
    assert weights.sum()==1 and weights@np.array([0,10,20,30])==12.5
    y,x=np.mgrid[:5,:5].astype(float)
    first=x*y;second=(x-.5)*y
    # Explicit neighbor interpolation, independent of the prose's analytic substitution.
    yy,xx=np.mgrid[1:4,1:4]
    sampled=.75*second[yy,xx]+.25*second[yy,xx+1]
    np.testing.assert_allclose(sampled,[[.75,1.75,2.75],[1.5,3.5,5.5],[2.25,5.25,8.25]])
    a=np.column_stack((yy.ravel(),xx.ravel()))
    rhs=(first[yy,xx]-sampled).ravel()
    np.testing.assert_allclose(a.T@rhs,[10.5,9])
    correction=np.linalg.lstsq(a,rhs,rcond=None)[0]
    np.testing.assert_allclose(correction,[.25,0],atol=1e-14)
    np.testing.assert_allclose(.5*second[yy,xx]+.5*second[yy,xx+1],first[yy,xx])
    # Full destination patch support for the FLOW-07 example, not just its center.
    valid=np.zeros((5,5),bool)
    for cy in range(1,4):
        for cx in range(1,4):valid[cy,cx]=cx+1+.25<=4
    assert valid.sum()==6 and valid[1:4,1:3].all()


def test_filter_scaling_metrics_and_round_trip():
    k=np.array([1,4,6,4,1])/16
    assert k@[0,1,0,1,0]==k@[1,0,1,0,1]==.5
    smooth=np.convolve(np.pad(np.arange(5.),2,mode='reflect'),k,mode='valid')
    np.testing.assert_allclose(smooth[::2],[.75,2,3.25])
    shapes=[(17,21)]
    for _ in range(2):shapes.append(tuple((n+1)//2 for n in shapes[-1]))
    assert shapes==[(17,21),(9,11),(5,6)]
    np.testing.assert_allclose(np.array([8,-4])/4,[2,-1])
    np.testing.assert_allclose(2*np.interp(np.minimum(np.arange(4)/2,1),[0,1],[0,2]),[0,2,4,4])
    assert np.linalg.norm(np.array([1,1])-np.array([2,-1]))==np.sqrt(5)
    assert np.mean([np.linalg.norm([3,4]),0])==2.5
    backward=.5*np.array([-.25,0])+.5*np.array([-.75,0])
    np.testing.assert_allclose(np.array([.5,0])+backward,[0,0])
    assert .5*True+.5*False==.5


def test_optional_section_visuals_and_complete_assignment_interfaces():
    manifest,root=load_course('optical-flow')
    pages=load_theory(root)
    assert {s.visual for p in pages for s in p.sections if s.visual}=={
        'correspondence','patch','ambiguity','sampling','alignment','refinement','pyramid','evaluation','consistency'}
    assert TheorySection(title='Legacy section',text='Existing LDPC prose').visual is None
    ldpc_root=ROOT/'curriculum/ldpc_5g'
    assert all(s.visual is None for p in load_theory(ldpc_root) for s in p.sections)
    for cp in manifest.checkpoints:
        assert 'Concrete invocation' in cp.input_reference
        assert 'What the public checks reveal' in cp.lesson
        assert cp.editable_files[0] in cp.input_reference
        assert cp.optional_math=='' and cp.optional_hardware==''
    # Export and model context carry the numerical explanation, not only a visual ID.
    page=next(p for p in pages if p.id=='alignment').model_dump()
    refinement=next(s for s in page['sections'] if s['visual']=='refinement')
    assert '[10.5,9]' in refinement['text']
    export=(ROOT/'docs/OPTICAL_FLOW_TUTORIAL.md').read_text()
    assert refinement['text'] in export
    assert all(cp.input_reference in export for cp in manifest.checkpoints)

    # Verify the actual tutor request preserves section metadata and its arithmetic.
    from unittest.mock import patch
    from app.ldpc.tutor import get_python_tutor_reply
    with patch('app.ldpc.tutor.complete',return_value={'content':'Fit the reference-minus-sampled residual using the center translation.'}) as model:
        get_python_tutor_reply(manifest.checkpoints[6],{},'Explain the correction',api_key_override='synthetic',theory_page=page)
    context=json.loads(model.call_args.args[0][1]['content'])
    assert context['theory_page']==page
    assert 'files' not in context and 'run' not in context

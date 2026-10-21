"""Course contracts, reporting, and private author sanity checks.

These independent baselines are test infrastructure, never learner assets.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.verilog.manifest import load_course
from app.ldpc.runner import parse_report
from app.ldpc.tutor import get_python_tutor_reply
from app.ldpc.theory import load_theory


def test_ldpc_course_and_cache_coexist():
    m, _ = load_course("ldpc-5g")
    assert m.toolchain == "python" and len(m.checkpoints) == 18
    assert all(c.lesson and c.visual and c.prediction and c.reflection for c in m.checkpoints)
    assert all(not c.hidden_testbench for c in m.checkpoints)
    cache, _ = load_course("cache-lab")
    assert cache.toolchain == "iverilog" and len(cache.checkpoints) == 6


def test_intro_pages_cover_each_assignment_and_define_basics():
    manifest, root = load_course("ldpc-5g")
    pages = load_theory(root)
    assert len(pages) == 6 and len({p.id for p in pages}) == 6
    assert {link.id for p in pages for link in p.connections} == {c.id for c in manifest.checkpoints}
    assert all(p.sections and p.question and p.answer for p in pages)
    prose = " ".join(s.text for p in pages for s in p.sections)
    for word in ["payload", "codeword", "XOR", "syndrome", "Tanner", "LLR", "Low density"]:
        assert word in prose


def test_decoding_walkthrough_numbers_and_beginner_sequence():
    _, root = load_course("ldpc-5g")
    page = load_theory(root)[4]
    assert page.id == "decoding" and len(page.sections) == 5
    assert "LLR" not in page.sections[0].text
    assert "does not name the guilty bit" in page.sections[2].text
    assert "not another signal sent by the transmitter" in page.sections[2].text
    channel = np.array([4., -.2, 3.])
    h = np.array([[1, 1, 1]])
    r, _, posterior = baseline_modules()["flooding_step"](h, channel, h * channel)
    assert np.allclose(r, [[-.2, 3, -.2]])
    assert np.allclose(posterior, [3.8, 2.8, 2.8])
    assert np.array_equal(posterior < 0, [0, 0, 0])
    assert "[+3.8, +2.8, +2.8]" in page.sections[3].text
    assert "[3,-1,-1]" not in " ".join(s.text for s in page.sections)
    assert any(s.title == "A second round can matter" for s in page.optional_sections)


def test_theory_model_receives_page_not_assignment_diagnostics():
    manifest, root = load_course("ldpc-5g")
    page = load_theory(root)[0].model_dump()
    with patch("app.ldpc.tutor.complete", return_value={"content":"The encoder adds protection bits so the receiver has constraints to check after noise changes its observations.", "_served_model":"synthetic"}) as model:
        reply, _ = get_python_tutor_reply(manifest.checkpoints[0], {"python/gf2.py":"# learner"},
            "Why add bits?", api_key_override="synthetic", theory_page=page)
    context = json.loads(model.call_args.args[0][1]["content"])
    assert context["question"] == "Why add bits?"
    assert context["theory_page"]["id"] == "why-coding"
    assert "run" not in context and "files" not in context and "checkpoint" not in context
    assert reply.source == "model"


def test_plain_model_answer_has_no_fallback_quiz_or_instructions():
    manifest, root = load_course("ldpc-5g")
    page = load_theory(root)[2].model_dump()
    question = "Does GF(2) expect parity 0 or anything, and is this information shared with the original signal?"
    answer = "GF(2) is arithmetic allowing 0 and 1; the LDPC code requires each check to be zero. Both ends already know the check rules. The encoder adds parity bits to the transmitted codeword, while the receiver computes the syndrome locally.\n\nToy: payload [1,0] -> encoded [1,0,1]; the known rule is a XOR b XOR p = 0."
    with patch("app.ldpc.tutor.complete", return_value={"content":answer, "_served_model":"synthetic"}) as model:
        reply, text = get_python_tutor_reply(manifest.checkpoints[0], {}, question,
            theory_page=page, api_key_override="synthetic", allow_model_fallbacks=False)
    assert model.call_count == 1  # No extra model calls for a quality-review loop.
    assert text == "Guide model: OpenCode · synthetic\n\n" + answer
    assert reply.next_step == reply.question == reply.concept == ""
    assert reply.evidence == []
    assert page["question"] not in text
    assert "configure the guide model" not in text
    prompt = model.call_args.args[0][0]["content"]
    for instruction in ["answer both explicitly", "not from GF(2)", "Both ends know", "not JSON", "Do not automatically", "Check the arithmetic"]:
        assert instruction in prompt


def test_partial_model_json_does_not_inherit_fallback_metadata():
    manifest, root = load_course("ldpc-5g")
    with patch("app.ldpc.tutor.complete", return_value={"content":json.dumps({"summary":"The transmitter and receiver know the code rules before transmission.", "next_step":"Compare a clean and corrupted codeword."})}):
        reply, text = get_python_tutor_reply(manifest.checkpoints[0], {}, "Who knows the rules?",
            theory_page=load_theory(root)[2].model_dump(), api_key_override="synthetic")
    assert "Compare a clean and corrupted codeword." in text
    assert "**Think about**" not in text and "**Basis**" not in text
    assert "configure the guide model" not in text
    assert reply.source == "model"


def test_prose_can_include_math_braces_without_becoming_fallback():
    manifest, _ = load_course("ldpc-5g")
    with patch("app.ldpc.tutor.complete", return_value={"content":"The set {0, 1} describes the two arithmetic values, not which parity a code requires. The coding rule supplies that requirement."}):
        reply, text = get_python_tutor_reply(manifest.checkpoints[0], {}, "What are the values?", api_key_override="synthetic")
    assert reply.source == "model" and "{0, 1}" in text


def test_malformed_model_json_stays_explicit_fallback():
    manifest, root = load_course("ldpc-5g")
    with patch("app.ldpc.tutor.complete", return_value={"content":'{"summary": "unfinished JSON that should not masquerade as a model answer'}):
        reply, text = get_python_tutor_reply(manifest.checkpoints[0], {}, "Explain coding",
            theory_page=load_theory(root)[0].model_dump(), api_key_override="synthetic")
    assert reply.source == "fallback" and "not a tailored answer" in text


def test_theory_fallback_is_explicit_authored_background():
    manifest, root = load_course("ldpc-5g")
    with patch("app.ldpc.tutor.settings") as settings:
        settings.openrouter_api_key = ""
        reply, text = get_python_tutor_reply(manifest.checkpoints[0], {}, "What is a channel?", theory_page=load_theory(root)[0].model_dump())
    assert reply.source == "fallback"
    assert "not a tailored answer" in text and "physical signal" in text
    assert "run the compiler" not in text


def test_zero_and_malformed_reports_never_pass(tmp_path):
    report = tmp_path / "report.xml"
    assert parse_report(report, 3).errors
    report.write_text("<testsuites/>")
    assert parse_report(report, 3).errors
    report.write_text("broken")
    assert parse_report(report, 3).errors


def test_report_failure_values_and_count(tmp_path):
    p = tmp_path / "r.xml"
    p.write_text('<testsuite><testcase name="parity"/><testcase name="flip"><failure>expected 1 observed 0</failure></testcase></testsuite>')
    r = parse_report(p,2)
    assert (r.passed,r.failed,r.errors)==(1,1,0)
    assert "observed 0" in r.cases[1].message
    assert parse_report(p,3).errors == 1


def test_report_symlink_is_rejected(tmp_path):
    private=tmp_path/"private.xml";private.write_text('<testsuite><testcase name="private"/></testsuite>')
    report=tmp_path/"report.xml";report.symlink_to(private)
    assert parse_report(report,1).errors == 1


def test_model_context_is_python_scoped_and_backup_disabled():
    m,_=load_course("ldpc-5g")
    with patch("app.ldpc.tutor.complete",return_value={"content":"A zero syndrome verifies parity, not the original payload. Two valid codewords can both satisfy the matrix checks.","_served_model":"synthetic"}) as model:
        reply, text=get_python_tutor_reply(m.checkpoints[1],{"python/syndrome.py":"# learner"},"Why?",api_key_override="synthetic-key",allow_model_fallbacks=False)
    assert model.call_args.args[3] == []
    assert "hidden_testbench" not in model.call_args.args[0][1]["content"]
    assert "synthetic-key" not in text
    assert reply.source == "model" and reply.engine == "opencode"


def baseline_modules():
    def gf2_dot(a,b): return sum(int(x)*int(y) for x,y in zip(a,b))%2
    def syndrome(bits,h): return np.array([gf2_dot(bits,r) for r in h])
    def check_neighbors(h): return [[i for i,x in enumerate(r) if x] for r in h]
    def hard_decisions(x): return np.array([int(v<0) for v in x])
    def check_messages(q):
        out=[]
        for j in range(len(q)):
            other=[v for i,v in enumerate(q) if i!=j]
            sign=1
            for v in other: sign*= -1 if v<0 else 1
            out.append(sign*min(abs(v) for v in other))
        return np.array(out)
    def check_messages_fast(q):
        magnitudes=sorted(abs(float(v)) for v in q)
        return dict(min1=magnitudes[0],min2=magnitudes[1],argmin=int(np.argmin(np.abs(q))),negative_parity=int(sum(v<0 for v in q)%2),outgoing=check_messages(q))
    def variable_messages(ch,r):
        p=ch+sum(r)
        return p,np.array([p-v for v in r])
    def flooding_step(h,ch,q):
        r=np.zeros(h.shape);new=np.zeros(h.shape);p=np.array(ch,copy=True)
        for i,js in enumerate(check_neighbors(h)): r[i,js]=check_messages(q[i,js])
        for j in range(len(ch)):
            rows=[i for i in range(len(h)) if h[i,j]]
            p[j], new[rows,j]=variable_messages(ch[j],r[rows,j])
        return r,new,p
    def decode_toy(h,ch,maximum):
        q=h*ch;bits=hard_decisions(ch);hist=[int(sum(syndrome(bits,h)))];used=0
        while hist[-1] and used<maximum:
            _,q,p=flooding_step(h,ch,q);bits=hard_decisions(p);used+=1;hist.append(int(sum(syndrome(bits,h))))
        return dict(bits=bits,iterations=used,syndrome_weights=hist)
    def corrected_messages(q,alpha=1.,beta=0.):
        r=check_messages(q)
        return np.array([(1 if v>=0 else -1)*alpha*max(abs(v)-beta,0) for v in r])
    def layer_update(p,old,indices):
        q=p[indices]-old;r=check_messages(q);n=p.copy();n[indices]=q+r;return n,r
    def qc_rotate(x,shift):
        if not len(x): raise ValueError()
        return np.array([x[(i-shift)%len(x)] for i in range(len(x))])
    def expand_qc(base,z):
        out=np.zeros((len(base)*z,len(base[0])*z),dtype=int)
        for i,row in enumerate(base):
            for j,k in enumerate(row):
                if k>=0:
                    for r in range(z):out[i*z+r,j*z+(r+k)%z]=1
        return out
    def lifting_set_index(z):
        from provided.nr_sets import LIFTING_SETS
        for i,s in enumerate(LIFTING_SETS):
            if z in s:return i
        raise ValueError()
    def saturate_signed(x,width):return np.array([min(2**(width-1)-1,max(-2**(width-1),int(v))) for v in x],dtype=np.int64)
    def quantize_signed(x,width,fraction_bits):return saturate_signed(np.rint(x*2**fraction_bits),width)
    def lane_plan(z,lanes):
        g=(z+lanes-1)//lanes
        return dict(groups=g,valid=[min(lanes,z-i*lanes) for i in range(g)],utilization=z/(g*lanes))
    def bank_conflicts(addresses,banks):
        ids=np.array([a%banks for a in addresses]); counts=np.array([sum(ids==i) for i in range(banks)])
        return dict(bank_ids=ids,counts=counts,conflict=bool(any(counts>1)))
    return locals()


@pytest.mark.parametrize("index",range(18))
def test_all_public_fixtures_against_independent_baseline(index,monkeypatch):
    manifest,root=load_course("ldpc-5g");c=manifest.checkpoints[index]
    functions=baseline_modules()
    # Restore every temporary module entry after this author-only check.
    for cp in manifest.checkpoints:
        module=types.ModuleType(cp.module)
        function=next(v for k,v in functions.items() if callable(v) and ("def "+k+"(") in (root/"starter"/cp.editable_files[0]).read_text())
        setattr(module,function.__name__,function);monkeypatch.setitem(sys.modules,cp.module,module)
    provided=types.ModuleType("provided");provided.__path__=[str(root/"python"/"provided")]
    monkeypatch.setitem(sys.modules,"provided",provided)
    spec=importlib.util.spec_from_file_location("public_suite",root/c.public_testbench)
    suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
    cases=[v for k,v in vars(suite).items() if k.startswith("test_")]
    assert len(cases)==c.expected_public_checks
    for case in cases:case()

import json
from unittest.mock import patch

import httpx
import pytest

from app import opencode
from app.verilog.manifest import load_course
from app.verilog.tutor import get_tutor_reply


def harness_mock(error=None):
    calls = []
    reads = 0

    def handle(request):
        nonlocal reads
        calls.append((request.method, request.url.path, json.loads(request.content) if request.content else None))
        if request.url.path == "/session" and request.method == "POST":
            return httpx.Response(200, json={"id": "ses_mock"})
        if request.url.path == "/session/ses_mock/message":
            reads += 1
            if reads == 1:
                return httpx.Response(200, json=[])
            info = {"id": "msg_answer", "role": "assistant", "modelID": "cohere/north-mini-code:free", "time": {}}
            if error:
                info["error"] = error
            elif reads > 2:
                info["time"]["completed"] = 100
            return httpx.Response(200, json=[{"info": info, "parts": [{"type": "text", "text": "A helpful model answer."}]}])
        if request.url.path == "/session/status":
            return httpx.Response(200, json={"ses_mock": {"type": "retry", "attempt": 2}})
        return httpx.Response(200, json=True)

    return httpx.MockTransport(handle), calls


def test_harness_async_model_selection_progress_and_key_cleanup():
    transport, calls = harness_mock()
    client = httpx.Client(base_url="http://harness", transport=transport)
    progress = []
    with patch("app.opencode.httpx.Client", return_value=client), patch("app.opencode.time.sleep"):
        result = opencode.complete(
            [{"role": "system", "content": "Tutor rules"}, {"role": "user", "content": "Synthetic question"}],
            model="cohere/north-mini-code:free", api_key="test-secret", on_status=progress.append,
        )
    prompt = next(body for method, path, body in calls if path.endswith("prompt_async"))
    assert prompt["model"] == {"providerID": "openrouter", "modelID": "cohere/north-mini-code:free"}
    assert prompt["system"] == "Tutor rules"
    assert prompt["agent"] == "tutor"
    create = next(body for method, path, body in calls if method == "POST" and path == "/session")
    assert create["permission"] == [{"permission": "*", "pattern": "*", "action": "deny"}]
    assert result["_engine"] == "opencode"
    assert result["content"] == "A helpful model answer."
    assert any("retrying" in text for text in progress)
    assert ("DELETE", "/auth/openrouter", None) in calls
    assert ("DELETE", "/session/ses_mock", None) in calls
    assert "test-secret" not in json.dumps(result) + json.dumps(progress)


def test_harness_error_sanitizes_provider_body_and_cleans_key():
    transport, calls = harness_mock({"name": "APIError", "data": {"statusCode": 429, "responseBody": "test-secret private prompt"}})
    client = httpx.Client(base_url="http://harness", transport=transport)
    with patch("app.opencode.httpx.Client", return_value=client):
        with pytest.raises(opencode.OpenCodeError, match="HTTP 429") as exc:
            opencode.complete([{"role": "user", "content": "Question"}], model="test/model:free", api_key="test-secret")
    assert "test-secret" not in str(exc.value)
    assert ("POST", "/session/ses_mock/abort", None) in calls
    assert ("DELETE", "/auth/openrouter", None) in calls


def test_harness_cancellation_aborts_and_removes_key():
    transport, calls = harness_mock()
    client = httpx.Client(base_url="http://harness", transport=transport)

    def status(text):
        if "Guide is" in text or "retrying" in text:
            raise opencode.OpenCodeCancelled()

    with patch("app.opencode.httpx.Client", return_value=client), patch("app.opencode.time.sleep"):
        with pytest.raises(opencode.OpenCodeCancelled):
            opencode.complete([{"role": "user", "content": "Question"}], model="test/model:free", api_key="test-secret", on_status=status)
    assert ("POST", "/session/ses_mock/abort", None) in calls
    assert ("DELETE", "/auth/openrouter", None) in calls


def test_sessions_are_reused_only_for_same_learner_checkpoint_and_key():
    calls = []

    original_client = httpx.Client

    def factory(**kwargs):
        transport, recorded = harness_mock()
        calls.append(recorded)
        return original_client(base_url="http://harness", transport=transport)

    with patch("app.opencode.httpx.Client", side_effect=factory), patch("app.opencode.time.sleep"):
        for scope, key in [("test-learner:CACHE-01", "key-one"), ("test-learner:CACHE-01", "key-one"),
                           ("test-learner:CACHE-01", "key-two"), ("test-learner:CACHE-02", "key-one")]:
            opencode.complete([{"role": "user", "content": "Question"}], model="test/model:free", api_key=key, session_scope=scope)
    counts = [sum(method == "POST" and path == "/session" for method, path, body in request) for request in calls]
    assert counts == [1, 0, 1, 1]


def test_tutor_uses_harness_and_keeps_reference_material_out_of_prompt():
    manifest, _ = load_course("cache-lab")
    answer = {"content": json.dumps({
        "summary": "mem_req_ready accepts a write; wait for mem_resp_valid before the CPU response.",
        "evidence": ["CACHE-05 requires request acceptance and a later memory response."],
    }), "_served_model": "nvidia/nemotron-3-ultra-550b-a55b:free"}
    with patch("app.verilog.tutor.settings.tutor_engine", "opencode"), patch(
        "app.verilog.tutor.opencode_complete", return_value=answer
    ) as mocked:
        reply, content = get_tutor_reply(
            manifest.checkpoints[4], {}, "Should I wait for the write before IDLE?",
            api_key_override="test-secret", reference_files={"rtl/cache_controller.v": "PRIVATE REFERENCE CONTENT"},
            session_scope="learner:CACHE-05", model_override=answer["_served_model"],
        )
    assert reply.source == "model" and reply.engine == "opencode"
    assert "OpenCode" in content
    assert mocked.call_args.kwargs["session_scope"] == "learner:CACHE-05"
    assert "PRIVATE REFERENCE CONTENT" not in json.dumps(mocked.call_args.args)

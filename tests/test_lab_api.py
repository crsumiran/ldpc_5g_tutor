from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.verilog.schemas import TutorReply


client = TestClient(app)


def test_course_listing_uses_manifest_ids():
    response = client.get("/api/courses")
    assert response.status_code == 200
    assert any(course["id"] == "cache-lab" for course in response.json())


def test_ldpc_theory_api_is_read_only_and_chat_uses_authored_page():
    course = client.get("/api/courses/ldpc-5g").json()
    assert len(course["theory_pages"]) == 6
    assert client.get("/api/courses/cache-lab").json()["theory_pages"] == []
    session = client.post("/api/courses/ldpc-5g/sessions", json={}).json()
    endpoint = f"/api/lab-sessions/{session['id']}/tutor"
    reply = TutorReply(summary="Radio noise can change observations.", error_category="none",
        concept="channel", next_step="Read the example", question="What was sent?", hint_level=0)
    with patch("app.ldpc.tutor.get_python_tutor_reply", return_value=(reply, reply.summary)) as guide:
        response = client.post(endpoint, json={"checkpoint_id":"LDPC-01", "theory_page_id":"why-coding", "message":"Why does data change?"})
        assert response.status_code == 200
        assert guide.call_args.kwargs["theory_page"]["id"] == "why-coding"
        assert guide.call_args.args[3] is None
        assert guide.call_args.kwargs["conversation_history"] == []
        guide.reset_mock()
        invalid = client.post(endpoint, json={"checkpoint_id":"LDPC-01", "theory_page_id":"../../private", "message":"Read it"})
        assert invalid.status_code == 400
        guide.assert_not_called()
    unchanged = client.get(f"/api/lab-sessions/{session['id']}").json()
    assert unchanged["passed_checkpoint_ids"] == session["passed_checkpoint_ids"]
    assert unchanged["checkpoints"] == session["checkpoints"]


def test_lab_session_api_is_learner_safe():
    course = client.get("/api/courses/cache-lab")
    assert course.status_code == 200
    assert len(course.json()["manifest"]["checkpoints"]) == 6

    session = client.post("/api/courses/cache-lab/sessions", json={})
    assert session.status_code == 200
    session_id = session.json()["id"]

    files = client.get(f"/api/lab-sessions/{session_id}/files")
    assert files.status_code == 200
    assert any(item["path"] == "rtl/cache_address_decode.v" and item["editable"] for item in files.json())

    hidden = client.get(f"/api/lab-sessions/{session_id}/files/tests/hidden/tb_address_decode_hidden.v")
    assert hidden.status_code == 404


def test_locked_checkpoint_cannot_run():
    session = client.post("/api/courses/cache-lab/sessions", json={}).json()
    response = client.post(f"/api/lab-sessions/{session['id']}/runs", json={"checkpoint_id": "CACHE-06", "mode": "test"})
    assert response.status_code == 403


def test_tutor_accepts_per_request_key_and_model_without_storing_key():
    session = client.post("/api/courses/cache-lab/sessions", json={}).json()
    session_id = session["id"]
    reply = TutorReply(
        summary="Check the address fields.", error_category="none", evidence=[],
        concept="address decoding", next_step="Mark the bit boundaries.",
        question="Which bits select a line?", hint_level=0,
        source="model", model="google/gemma-4-31b-it:free",
    )
    with patch("app.api.labs.get_tutor_reply", return_value=(reply, "Check the address fields.")) as mocked:
        response = client.post(
            f"/api/lab-sessions/{session_id}/tutor",
            json={"checkpoint_id": "CACHE-01", "message": "How are bits split?", "model": "google/gemma-4-31b-it:free"},
            headers={"X-OpenRouter-Api-Key": "sk-or-v1-test-only"},
        )
    assert response.status_code == 200
    assert mocked.call_args.kwargs["model_override"] == "google/gemma-4-31b-it:free"
    assert mocked.call_args.kwargs["api_key_override"] == "sk-or-v1-test-only"
    assert mocked.call_args.kwargs["allow_model_fallbacks"] is True
    assert "sk-or-v1-test-only" not in response.text
    messages = client.get(f"/api/lab-sessions/{session_id}/messages")
    assert messages.status_code == 200
    assert "sk-or-v1-test-only" not in messages.text


def test_stream_tutor_returns_progress_and_checked_result():
    session = client.post("/api/courses/cache-lab/sessions", json={}).json()
    reply = TutorReply(summary="Checked answer", error_category="none", concept="address bits",
                       next_step="Mark the fields", question="Which bits select a line?", hint_level=0)

    def answer(*args, **kwargs):
        kwargs["on_status"]("Guide is thinking…")
        return reply, "Checked answer"

    with patch("app.api.labs.get_tutor_reply", side_effect=answer):
        response = client.post(f"/api/lab-sessions/{session['id']}/tutor/stream", json={
            "checkpoint_id": "CACHE-01", "message": "Explain address bits",
        }, headers={"X-OpenRouter-Api-Key": "synthetic-key"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: status" in response.text and "event: result" in response.text
    assert "Checked answer" in response.text
    assert "synthetic-key" not in response.text


def test_stream_tutor_reports_locked_checkpoint_without_calling_model():
    session = client.post("/api/courses/cache-lab/sessions", json={}).json()
    with patch("app.api.labs.get_tutor_reply") as model:
        response = client.post(f"/api/lab-sessions/{session['id']}/tutor/stream", json={
            "checkpoint_id": "CACHE-06", "message": "Explain integration",
        })
    assert "event: error" in response.text and "Checkpoint is locked" in response.text
    model.assert_not_called()


def test_available_models_uses_entered_key_without_returning_it():
    with patch("app.api.labs.list_available_free_models", return_value=[{"id": "qwen/qwen3.8-27b:free", "name": "Qwen free"}]) as mocked:
        response = client.get("/api/openrouter/models", headers={"X-OpenRouter-Api-Key": "sk-or-v1-test-only"})
    assert response.status_code == 200
    assert mocked.call_args.args == ("sk-or-v1-test-only",)
    assert response.json()["models"] == [{"id": "qwen/qwen3.8-27b:free", "name": "Qwen free"}]
    assert "sk-or-v1-test-only" not in response.text


def test_openrouter_connection_test_uses_synthetic_prompt_and_reports_served_model():
    with patch("app.api.labs.complete", return_value={"content": "OK", "_served_model": "cohere/north-mini-code:free"}) as mocked:
        response = client.post(
            "/api/openrouter/test",
            json={"model": "google/gemma-4-31b-it:free", "allow_model_fallbacks": True},
            headers={"X-OpenRouter-Api-Key": "sk-or-v1-test-only"},
        )
    assert response.status_code == 200
    assert response.json()["fallback_used"] is True
    assert response.json()["served_model"] == "cohere/north-mini-code:free"
    assert mocked.call_args.kwargs["messages"] == [{"role": "user", "content": "Reply with exactly OK."}]
    assert mocked.call_args.kwargs["api_key"] == "sk-or-v1-test-only"
    assert "sk-or-v1-test-only" not in response.text

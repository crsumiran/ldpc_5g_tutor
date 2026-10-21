from unittest.mock import patch

import httpx

from app.llm import complete, list_available_free_models, openrouter_error_status


def test_complete_uses_per_request_key_and_only_selected_model():
    with patch("app.llm.httpx.Client") as client_type:
        client = client_type.return_value.__enter__.return_value
        client.post.return_value.json.return_value = {
            "model": "google/gemma-4-31b-it:free",
            "choices": [{"message": {"content": "ok"}}],
        }
        reply = complete(
            messages=[{"role": "user", "content": "hello"}],
            model="google/gemma-4-31b-it:free", fallback_models=[],
            api_key="sk-or-v1-test-only", include_model=True, max_tokens=123,
            plugins=[{"id": "response-healing"}],
        )
    sent = client.post.call_args.kwargs
    assert sent["headers"]["Authorization"] == "Bearer sk-or-v1-test-only"
    assert sent["json"]["model"] == "google/gemma-4-31b-it:free"
    assert "models" not in sent["json"]
    assert sent["json"]["max_tokens"] == 123
    assert sent["json"]["plugins"] == [{"id": "response-healing"}]
    assert reply["_served_model"] == "google/gemma-4-31b-it:free"


def test_user_model_list_filters_free_routes_and_does_not_return_key():
    with patch("app.llm.httpx.Client") as client_type:
        client = client_type.return_value.__enter__.return_value
        client.get.return_value.json.return_value = {"data": [
            {"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B"},
            {"id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "Nemotron paid"},
        ]}
        models = list_available_free_models("sk-or-v1-test-only")
    assert models == [{"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B"}]
    assert client.get.call_args.kwargs["headers"]["Authorization"] == "Bearer sk-or-v1-test-only"
    assert "sk-or-v1-test-only" not in str(models)


def test_404_guardrail_error_is_actionable_without_echoing_provider_body():
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = httpx.Response(404, json={"error": {"message": "0 endpoints match your guardrail restrictions and data policy; sk-or-v1-secret"}}, request=request)
    error = httpx.HTTPStatusError("not found", request=request, response=response)
    status = openrouter_error_status(error, "nvidia/nemotron-3-ultra-550b-a55b:free")
    assert "guardrails/data policy" in status
    assert "nvidia/nemotron-3-ultra-550b-a55b:free" in status
    assert "sk-or-v1-secret" not in status

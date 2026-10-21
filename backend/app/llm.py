import json
import hashlib
import threading
import time
from typing import Any
import httpx
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_USER_MODELS_URL = "https://openrouter.ai/api/v1/models/user"

_request_lock_guard = threading.Lock()
_request_state_guard = threading.Lock()
_request_locks: dict[str, threading.Lock] = {}
_next_request_at: dict[str, float] = {}


def _pace_openrouter_request(api_key: str) -> None:
    """Keep this app below OpenRouter's free-tier burst limit per API key."""
    key_id = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    with _request_lock_guard:
        request_lock = _request_locks.setdefault(key_id, threading.Lock())

    with request_lock:
        with _request_state_guard:
            now = time.monotonic()
            wait_seconds = max(0.0, _next_request_at.get(key_id, now) - now)
        if wait_seconds:
            time.sleep(wait_seconds)
        with _request_state_guard:
            _next_request_at[key_id] = time.monotonic() + max(0.0, settings.tutor_openrouter_min_interval_seconds)


def openrouter_error_status(exc: Exception, model: str | None = None) -> str:
    if not isinstance(exc, httpx.HTTPStatusError):
        return type(exc).__name__
    code = exc.response.status_code
    try:
        message = str(exc.response.json().get("error", {}).get("message", "")).lower()
    except (ValueError, AttributeError, TypeError):
        message = ""
    target = f" for {model}" if model else ""
    if code == 404 and ("guardrail" in message or "data policy" in message):
        reason = ": no provider endpoint matches this key's guardrails/data policy; choose a model available to this key or review OpenRouter privacy settings"
    elif code == 404:
        reason = ": no matching provider endpoint or model; check model availability for this key"
    elif code == 429:
        reason = ": provider or account rate limit; try another available model or wait"
        retry_after = exc.response.headers.get("Retry-After")
        if retry_after:
            try:
                seconds = max(1, int(float(retry_after)))
                reason += f" (provider suggests retrying in about {seconds} seconds)"
            except ValueError:
                pass
    elif code == 401:
        reason = ": API key rejected; check the key in AI settings"
    elif code == 402:
        reason = ": account credit or spending limit reached"
    else:
        reason = ""
    return f"OpenRouter HTTP {code}{target}{reason}"


def list_available_free_models(api_key: str) -> list[dict[str, str]]:
    with httpx.Client(timeout=20.0) as client:
        response = client.get(OPENROUTER_USER_MODELS_URL, headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()
        data = response.json().get("data", [])
    if not isinstance(data, list):
        raise ValueError("Unexpected OpenRouter model-list response")
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.endswith(":free"):
            result.append({"id": model_id, "name": str(item.get("name") or model_id)})
    return sorted(result, key=lambda item: item["name"].lower())


def complete(
    messages: list[dict[str, Any]],
    model: str | None = None,
    fallback_models: list[str] | None = None,
    include_model: bool = False,
    response_format: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    plugins: list[dict[str, Any]] | None = None,
    temperature: float = 0.2,
    api_key: str | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key or settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model or settings.tutor_model,
        "messages": messages,
        "temperature": temperature,
    }
    if fallback_models:
        payload["models"] = fallback_models
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format:
        payload["response_format"] = response_format
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    if plugins:
        payload["plugins"] = plugins

    with httpx.Client(timeout=90.0) as client:
        _pace_openrouter_request(headers["Authorization"].removeprefix("Bearer "))
        r = client.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        message = data["choices"][0]["message"]
        if include_model:
            message = {**message, "_served_model": data.get("model")}
        return message


def complete_json(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    msg = complete(
        messages=messages,
        model=model,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    content = msg.get("content") or "{}"
    return json.loads(content)

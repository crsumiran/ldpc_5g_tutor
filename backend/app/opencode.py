"""Tutor bridge to the isolated OpenCode HTTP server.

OpenCode owns provider streaming/retries. The bridge polls its async session API
so no long HTTP model response is buffered by our transport. Runtime credentials
are scoped under a lock and removed after use; the service stores files on tmpfs.
"""
import hashlib
import json
import threading
import time
from collections.abc import Callable
from typing import Any

import httpx

from app.config import settings

_runtime_lock = threading.Lock()
_sessions: dict[tuple[str, str, str], str] = {}


class OpenCodeError(RuntimeError):
    pass


class OpenCodeCancelled(RuntimeError):
    pass


def _error_status(error: dict) -> str:
    data = error.get("data") or {}
    code = data.get("statusCode")
    reasons = {401: "key rejected", 402: "account spending limit", 404: "model/provider unavailable", 429: "provider or account rate limit"}
    if code:
        return f"OpenCode/OpenRouter HTTP {code}: {reasons.get(code, 'provider request failed')}"
    return f"OpenCode {error.get('name', 'provider error')}"


def complete(
    messages: list[dict[str, Any]], model: str, api_key: str,
    fallback_models: list[str] | None = None, session_scope: str | None = None,
    on_status: Callable[[str], None] | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    def status(text: str):
        if on_status:
            on_status(text)

    status("Waiting for the guide…")
    # auth.set is provider-wide, so different entered keys must never overlap.
    with _runtime_lock, httpx.Client(base_url=settings.opencode_url, timeout=15) as client:
        deadline = time.monotonic() + settings.opencode_timeout_seconds
        fingerprint = hashlib.sha256(api_key.encode()).hexdigest()
        active_session = None
        probe_sessions = []
        try:
            client.put("/auth/openrouter", json={"type": "api", "key": api_key}).raise_for_status()
            # Discard provider instances cached with a previous request's key.
            client.post("/instance/dispose").raise_for_status()
            models = list(dict.fromkeys([model, *(fallback_models or [])]))[:2]
            for index, selected in enumerate(models):
                status(f"Guide model: {selected}" if index == 0 else f"Trying backup model: {selected}")
                scope = (session_scope or "probe", selected, fingerprint)
                created = False
                active_session = _sessions.get(scope) if session_scope else None
                if active_session and client.get(f"/session/{active_session}").status_code == 404:
                    active_session = None
                if not active_session:
                    created = True
                    response = client.post("/session", json={
                        "title": "Learning guide", "agent": "tutor",
                        "permission": [{"permission": "*", "pattern": "*", "action": "deny"}],
                    })
                    response.raise_for_status()
                    active_session = response.json()["id"]
                    if session_scope:
                        _sessions[scope] = active_session
                    else:
                        probe_sessions.append(active_session)
                response = client.get(f"/session/{active_session}/message")
                response.raise_for_status()
                previous = {entry["info"]["id"] for entry in response.json()}
                system = "\n\n".join(str(m["content"]) for m in messages if m["role"] == "system")
                prompt = "\n\n".join(str(m["content"]) for m in messages if m["role"] != "system")
                if created and history:
                    prompt = "Recent conversation for context:\n" + json.dumps(history) + "\n\nCurrent checkpoint and question:\n" + prompt
                client.post(f"/session/{active_session}/prompt_async", json={
                    "agent": "tutor", "model": {"providerID": "openrouter", "modelID": selected},
                    "system": system, "parts": [{"type": "text", "text": prompt}],
                }).raise_for_status()
                attempt_deadline = min(deadline, time.monotonic() + (120 if len(models) > 1 else settings.opencode_timeout_seconds))
                failure = "OpenCode model response timed out"
                while time.monotonic() < attempt_deadline:
                    response = client.get(f"/session/{active_session}/message")
                    response.raise_for_status()
                    fresh = [e for e in response.json() if e["info"]["id"] not in previous and e["info"]["role"] == "assistant"]
                    for entry in reversed(fresh):
                        info = entry["info"]
                        if info.get("error"):
                            failure = _error_status(info["error"])
                            break
                        if info.get("time", {}).get("completed"):
                            content = "\n".join(p.get("text", "") for p in entry["parts"] if p.get("type") == "text")
                            if content.strip():
                                return {"content": content, "_served_model": info.get("modelID", selected), "_engine": "opencode"}
                            failure = "OpenCode returned an empty answer"
                            break
                    else:
                        response = client.get("/session/status")
                        response.raise_for_status()
                        state = response.json().get(active_session, {})
                        current = (f"Provider is busy; OpenCode is retrying (attempt {state.get('attempt', 1)})…"
                                   if state.get("type") == "retry" else "Guide is thinking…")
                        status(current)
                        time.sleep(0.75)
                        continue
                    break
                client.post(f"/session/{active_session}/abort").raise_for_status()
                if index + 1 == len(models) or time.monotonic() >= deadline:
                    raise OpenCodeError(failure)
            raise OpenCodeError("OpenCode produced no answer")
        except httpx.HTTPError as exc:
            if active_session:
                try:
                    client.post(f"/session/{active_session}/abort")
                except httpx.HTTPError:
                    pass
            code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            raise OpenCodeError(f"OpenCode service HTTP {code}" if code else "OpenCode service unavailable") from None
        except Exception:
            if active_session:
                try:
                    client.post(f"/session/{active_session}/abort")
                except httpx.HTTPError:
                    pass
            raise
        finally:
            for probe in probe_sessions:
                try:
                    client.delete(f"/session/{probe}")
                except httpx.HTTPError:
                    pass
            try:
                client.delete("/auth/openrouter").raise_for_status()
                client.post("/instance/dispose").raise_for_status()
            except httpx.HTTPError:
                # Fail visibly if request credentials could not be cleared.
                raise OpenCodeError("OpenCode credential cleanup failed; restart the guide service") from None

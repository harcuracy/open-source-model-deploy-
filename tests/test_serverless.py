from __future__ import annotations

import asyncio
from app.config import get_settings, get_settings_obj
from app.health import check_health
from app.llama_client import LlamaClient


def test_default_settings_load():
    settings = get_settings_obj()
    assert settings.model_name == "Qwen3.8-27B-GGUF"
    assert settings.max_context_tokens == 200000
    assert settings.server_url.endswith("/v1")
    assert not settings.server_base_url.endswith("/v1")


def test_health_check_mock(monkeypatch):
    monkeypatch.setenv("LLAMA_BACKEND_MODE", "mock")
    get_settings.cache_clear()
    result = check_health()
    assert result["status"] == "ok"
    assert result["mode"] == "mock"
    assert result["service"] == "llama.cpp"


def test_health_check_ok_real(monkeypatch):
    monkeypatch.setenv("LLAMA_BACKEND_MODE", "real")
    get_settings.cache_clear()

    class DummyResponse:
        def __init__(self):
            self.status_code = 200
            self.text = "{}"

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"id": "Qwen3.8-27B-GGUF"}]}

    def fake_get(url, timeout, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("app.health.httpx.get", fake_get)
    result = check_health()
    assert result["status"] == "ok"
    assert result["service"] == "llama.cpp"


def test_llama_client_mock():
    client = LlamaClient()
    assert client.is_mock or not client.is_mock


def test_serverless_chat_handler_mock(monkeypatch):
    monkeypatch.setenv("LLAMA_BACKEND_MODE", "mock")
    get_settings.cache_clear()
    from app.serverless_handler import handler

    async def _run():
        job = {
            "id": "job-test-1",
            "input": {
                "messages": [{"role": "user", "content": "Hello serverless Qwen"}],
                "max_tokens": 32,
            },
        }
        outputs = []
        async for item in handler(job):
            outputs.append(item)
        return outputs

    results = asyncio.run(_run())
    assert len(results) == 1
    assert "choices" in results[0]
    assert len(results[0]["choices"]) > 0
    assert "content" in results[0]["choices"][0]["message"]


def test_serverless_completion_handler_mock(monkeypatch):
    monkeypatch.setenv("LLAMA_BACKEND_MODE", "mock")
    get_settings.cache_clear()
    from app.serverless_handler import handler

    async def _run():
        job = {
            "id": "job-test-2",
            "input": {
                "prompt": "Write a poem",
                "max_tokens": 32,
            },
        }
        outputs = []
        async for item in handler(job):
            outputs.append(item)
        return outputs

    results = asyncio.run(_run())
    assert len(results) == 1
    assert "choices" in results[0]
    assert len(results[0]["choices"]) > 0
    assert "text" in results[0]["choices"][0]


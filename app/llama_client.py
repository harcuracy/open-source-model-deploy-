from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings_obj


class LlamaClient:
    def __init__(self) -> None:
        self.settings = get_settings_obj()

    @property
    def is_mock(self) -> bool:
        return self.settings.backend_mode == "mock"

    def _auth_headers(self) -> dict[str, str]:
        if self.settings.api_key:
            return {"Authorization": f"Bearer {self.settings.api_key}"}
        return {}

    def _health_url(self) -> str:
        return f"{self.settings.server_base_url}/health"

    async def health_check(self) -> dict[str, Any]:
        if self.is_mock:
            return {
                "status": "ok",
                "service": "llama.cpp",
                "mode": "mock",
                "model": self.settings.model_name,
                "health": {"status": "ok"},
            }

        url = self._health_url()
        headers = self._auth_headers()
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                payload = response.json()
                return {
                    "status": payload.get("status", "ok"),
                    "service": "llama.cpp",
                    "mode": self.settings.backend_mode,
                    "model": self.settings.model_name,
                    "health": payload,
                }
        except Exception as exc:  # pragma: no cover - runtime integration path
            return {
                "status": "degraded",
                "service": "llama.cpp",
                "mode": self.settings.backend_mode,
                "model": self.settings.model_name,
                "error": str(exc),
            }

    async def list_models(self) -> dict[str, Any]:
        if self.is_mock:
            return {
                "object": "list",
                "data": [
                    {
                        "id": self.settings.model_name,
                        "object": "model",
                        "created": 1700000000,
                        "owned_by": "llama.cpp",
                    }
                ],
            }

        url = f"{self.settings.server_url.rstrip('/')}/models"
        headers = self._auth_headers()
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"llama.cpp error ({exc.response.status_code}): {exc.response.text}") from exc
        except Exception as exc:  # pragma: no cover - runtime integration path
            raise RuntimeError(f"Unable to reach llama.cpp: {exc}") from exc

    async def request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.is_mock:
            clean_path = path if path.startswith("/") else f"/{path}"
            if clean_path in ("/chat/completions", "chat/completions"):
                return {
                    "id": "chatcmpl-mock",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": payload.get("model", self.settings.model_name),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Mock response from Qwen deployment service.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 8,
                        "total_tokens": 18,
                    },
                }
            if clean_path in ("/completions", "completions"):
                return {
                    "id": "cmpl-mock",
                    "object": "text_completion",
                    "created": 1700000000,
                    "model": payload.get("model", self.settings.model_name),
                    "choices": [
                        {
                            "index": 0,
                            "text": "Mock response from Qwen deployment service.",
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 8,
                        "total_tokens": 18,
                    },
                }
            return {"status": "ok", "mode": "mock", "payload": payload}

        clean_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.settings.server_url.rstrip('/')}{clean_path}"
        headers = self._auth_headers()
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text
            raise RuntimeError(f"llama.cpp error ({exc.response.status_code}): {body}") from exc
        except Exception as exc:  # pragma: no cover - runtime integration path
            raise RuntimeError(f"Unable to reach llama.cpp: {exc}") from exc

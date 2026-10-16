from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings_obj


def check_health() -> dict[str, Any]:
    settings = get_settings_obj()
    if settings.backend_mode == "mock":
        return {
            "status": "ok",
            "service": "llama.cpp",
            "mode": "mock",
            "url": settings.server_url,
            "models": [{"id": settings.model_name}],
        }

    target = settings.server_url.rstrip("/")
    kwargs: dict[str, Any] = {}
    if settings.api_key:
        kwargs["headers"] = {"Authorization": f"Bearer {settings.api_key}"}

    try:
        response = httpx.get(f"{target}/models", timeout=settings.request_timeout_seconds, **kwargs)
        response.raise_for_status()
        payload = response.json()
        return {
            "status": "ok",
            "service": "llama.cpp",
            "mode": settings.backend_mode,
            "url": target,
            "models": payload.get("data", payload),
        }
    except Exception as exc:  # pragma: no cover - exercised in runtime path
        return {
            "status": "degraded",
            "service": "llama.cpp",
            "mode": settings.backend_mode,
            "url": target,
            "error": str(exc),
        }


def main() -> None:
    result = check_health()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

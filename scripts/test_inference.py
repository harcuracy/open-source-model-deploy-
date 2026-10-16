"""Smoke test script for RunPod Serverless worker."""
from __future__ import annotations

import asyncio
import json
import os

import httpx

from app.config import get_settings_obj
from app.serverless_handler import handler


def main() -> None:
    settings = get_settings_obj()
    runpod_endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    runpod_api_key = os.getenv("RUNPOD_API_KEY")

    job_input = {
        "model": settings.model_name,
        "messages": [
            {"role": "user", "content": "Write a short haiku about scaling to millions of users."}
        ],
        "max_tokens": 64,
        "temperature": 0.7,
    }

    if runpod_endpoint_id and runpod_api_key:
        print(f"Testing live RunPod Serverless Endpoint {runpod_endpoint_id}...")
        url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/runsync"
        headers = {"Authorization": f"Bearer {runpod_api_key}"}
        res = httpx.post(url, json={"input": job_input}, headers=headers, timeout=settings.request_timeout_seconds)
        res.raise_for_status()
        print(json.dumps(res.json(), indent=2))
        return

    print("Executing worker handler test (local/mock backend)...")

    async def _run():
        results = []
        async for chunk in handler({"id": "local-smoke-test", "input": job_input}):
            results.append(chunk)
        return results

    results = asyncio.run(_run())
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

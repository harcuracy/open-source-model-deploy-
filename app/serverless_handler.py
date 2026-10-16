"""RunPod Serverless Worker Handler for Qwen LLM Inference."""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx

try:
    import runpod
except ImportError:  # pragma: no cover
    runpod = None

from app.config import get_settings_obj
from app.llama_client import LlamaClient

settings = get_settings_obj()
client = LlamaClient()


async def handler(job: dict[str, Any]) -> AsyncGenerator[Any, None] | dict[str, Any]:
    """Execute inference request received from RunPod Serverless queue."""
    job_input = job.get("input", {})
    messages = job_input.get("messages")
    prompt = job_input.get("prompt")
    stream = bool(job_input.get("stream", False))

    if client.is_mock:
        if messages:
            mock_res = await client.request("/chat/completions", {
                "model": job_input.get("model", settings.model_name),
                "messages": messages,
                "max_tokens": job_input.get("max_tokens", 64),
            })
            yield mock_res
            return
        mock_res = await client.request("/completions", {
            "model": job_input.get("model", settings.model_name),
            "prompt": prompt or "Hello",
            "max_tokens": job_input.get("max_tokens", 64),
        })
        yield mock_res
        return

    # Real mode inference request
    if messages:
        path = "/chat/completions"
        payload: dict[str, Any] = {
            "model": job_input.get("model", settings.model_name),
            "messages": messages,
            "max_tokens": job_input.get("max_tokens", 256),
            "stream": stream,
        }
    else:
        path = "/completions"
        payload = {
            "model": job_input.get("model", settings.model_name),
            "prompt": prompt or "Hello",
            "max_tokens": job_input.get("max_tokens", 256),
            "stream": stream,
        }

    if "temperature" in job_input and job_input["temperature"] is not None:
        payload["temperature"] = float(job_input["temperature"])
    if "top_p" in job_input and job_input["top_p"] is not None:
        payload["top_p"] = float(job_input["top_p"])

    url = f"{settings.server_url.rstrip('/')}{path}"
    headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}

    if stream:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http_client:
            async with http_client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            yield json.loads(data_str)
                        except Exception:
                            yield {"delta": data_str}
    else:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http_client:
            response = await http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            yield response.json()


def start() -> None:
    """Start the RunPod Serverless worker loop."""
    runpod.serverless.start({
        "handler": handler,
        "return_aggregate_stream": True,
    })


if __name__ == "__main__":
    start()

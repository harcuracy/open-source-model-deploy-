# Qwen RunPod Serverless MLOps

Autoscaling Serverless deployment for **Qwen 27B GGUF** using `llama.cpp` on **RunPod Serverless**.

Designed for high-throughput, pay-per-second GPU autoscaling capable of serving millions of requests.

---

## Architecture

* **Worker Engine:** `llama.cpp` (`llama-server`) with CUDA 12.4 acceleration and continuous batching (`PARALLEL=8`).
* **Serverless Bridge:** Native RunPod Serverless SDK (`runpod.serverless.start`) handling streaming and batched completions.
* **Storage:** Persistent Network Volume mounted at `/models` holding the GGUF weights.
* **CI/CD:** Automated cloud Docker build and push via GitHub Actions to Docker Hub / GHCR.

---

## Repository Structure

```
├── .github/workflows/
│   └── docker-build.yml        # Cloud CI/CD to build & push to Docker Hub
├── app/
│   ├── config.py               # Pydantic runtime settings
│   ├── health.py               # Backend health check
│   ├── llama_client.py         # HTTP client & mock mode engine
│   └── serverless_handler.py   # RunPod Serverless worker loop
├── deployment/
│   ├── runpod.env.example      # Example serverless environment settings
│   └── runpod.md               # End-to-end Serverless deployment guide
├── scripts/
│   ├── download_model.py       # Cloud model downloader
│   └── test_inference.py       # Serverless smoke test
├── tests/
│   └── test_serverless.py      # Automated tests
├── Dockerfile                  # CUDA 12.4 multi-stage serverless image
├── entrypoint.sh               # Container process supervisor
└── pyproject.toml              # Python project configuration
```

---

## Cloud Deployment Guide

See [`deployment/runpod.md`](deployment/runpod.md) for full instructions on configuring your RunPod Serverless endpoint.

# RunPod Serverless Deployment Guide

Production deployment guide for running **Qwen 27B GGUF** on **RunPod Serverless** with automatic scaling for millions of users.

---

## Architecture Overview

RunPod Serverless manages the global request queue, SSL termination, and horizontal autoscaling. The container runs as a serverless worker:

1. **RunPod Infrastructure:** Listens for incoming inference requests, queues jobs, and scales workers from 0 to 100+ GPUs based on demand.
2. **Worker Container (`app.serverless_handler`):** Pulls jobs from the RunPod queue via `runpod.serverless.start()`, streams or batches generation tokens, and returns output.
3. **Internal `llama-server` Engine:** C++ CUDA-accelerated inference running on `127.0.0.1:8080` with continuous batching (`PARALLEL=8`).
4. **Persistent Network Volume:** Houses the GGUF model weights at `/models` without redownloading on each cold start.

---

## 1. Prerequisites & GPU Sizing

* **Model:** `Qwen3.8-27B-GGUF` (or `Qwen2.5-32B-Instruct` GGUF)
* **Recommended GPU Types on RunPod Serverless:**
  * **1x NVIDIA A100 80GB:** Recommended for 200k context or Q8_0 weights.
  * **1x NVIDIA A6000 48GB / RTX 6000 Ada:** Excellent cost-efficiency for Q4/Q8 quants.
  * **1x NVIDIA RTX 4090 24GB:** Great for Q4_K_M quantizations with moderate context.

---

## 2. Store the Model in a Network Volume

1. In the RunPod Console, create a **Network Volume** (e.g. 100 GB).
2. Attach it to a temporary pod or use the volume terminal to download the model directly into cloud storage:
   ```bash
   pip install huggingface_hub
   huggingface-cli download unsloth/Qwen3.8-27B-GGUF Qwen3.8-27B-GGUF-Q8_0.gguf \
     --local-dir /models \
     --local-dir-use-symlinks False
   ```

---

## 3. Create the Serverless Endpoint

1. In RunPod Console, navigate to **Serverless > New Endpoint**.
2. **Endpoint Name:** `qwen-27b-serverless`
3. **Container Image:**
   ```text
   docker.io/<YOUR_DOCKERHUB_USERNAME>/qwen-runpod-mlops:latest
   ```
4. **GPU Selection:** Select `A100 (80GB SXM)` or `RTX 4090`.
5. **Network Volume:** Mount your volume to:
   ```text
   /models
   ```
6. **Environment Variables:**
   ```env
   MODEL_NAME=Qwen3.8-27B-GGUF
   MODEL_PATH=/models/Qwen3.8-27B-GGUF-Q8_0.gguf
   CONTEXT_SIZE=200000
   GPU_LAYERS=999
   PARALLEL=8
   LLAMA_BACKEND_MODE=real
   ```
7. **Autoscaling Configuration (For Millions of Users):**
   * **Active Workers (Warm):** `1` *(Keeps 1 worker hot for instant response without cold-start)*.
   * **Max Workers:** `50`–`100` *(RunPod scales up to this number under load)*.
   * **Idle Timeout:** `120s` *(Workers sleep after 2 minutes of zero traffic to save cost)*.

---

## 4. Querying Your Serverless Endpoint

### Synchronous Call (`/runsync`)
```bash
curl -X POST "https://api.runpod.ai/v2/<YOUR_ENDPOINT_ID>/runsync" \
  -H "Authorization: Bearer <YOUR_RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "How do you scale to millions of users?"}],
      "max_tokens": 128,
      "temperature": 0.7
    }
  }'
```

### Streaming Call (`/run` + `/stream`)
Pass `"stream": true` in `"input"`:
```bash
curl -X POST "https://api.runpod.ai/v2/<YOUR_ENDPOINT_ID>/run" \
  -H "Authorization: Bearer <YOUR_RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "Write a story about an AI in the cloud."}],
      "max_tokens": 512,
      "stream": true
    }
  }'
```
Then stream chunks using the returned job ID:
```bash
curl -N "https://api.runpod.ai/v2/<YOUR_ENDPOINT_ID>/stream/<JOB_ID>" \
  -H "Authorization: Bearer <YOUR_RUNPOD_API_KEY>"
```

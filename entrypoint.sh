#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_MODE="${LLAMA_BACKEND_MODE:-real}"
LLAMA_HOST="${LLAMA_SERVER_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_SERVER_PORT:-8080}"
MODEL_PATH="${MODEL_PATH:-/models/model.gguf}"
CONTEXT_SIZE="${LLAMA_CONTEXT_SIZE:-${CONTEXT_SIZE:-200000}}"
GPU_LAYERS="${GPU_LAYERS:-999}"
PARALLEL="${PARALLEL:-8}"
CACHE_TYPE_K="${CACHE_TYPE_K:-q8_0}"
CACHE_TYPE_V="${CACHE_TYPE_V:-q8_0}"
API_KEY="${API_KEY:-}"
LLAMA_BINARY="${LLAMA_SERVER_BINARY:-llama-server}"

resolve_binary() {
  local target="$1"
  if command -v "${target}" >/dev/null 2>&1; then
    command -v "${target}"
  elif [[ -x "${target}" ]]; then
    echo "${target}"
  elif [[ -x "/usr/local/bin/${target}" ]]; then
    echo "/usr/local/bin/${target}"
  else
    echo ""
  fi
}

LLAMA_PID=""
WORKER_PID=""

cleanup() {
  echo "Shutting down RunPod serverless worker..."
  if [[ -n "${WORKER_PID}" ]] && kill -0 "${WORKER_PID}" 2>/dev/null; then
    kill -TERM "${WORKER_PID}" 2>/dev/null || true
  fi
  if [[ -n "${LLAMA_PID}" ]] && kill -0 "${LLAMA_PID}" 2>/dev/null; then
    kill -TERM "${LLAMA_PID}" 2>/dev/null || true
  fi
  wait "${WORKER_PID}" 2>/dev/null || true
  wait "${LLAMA_PID}" 2>/dev/null || true
  exit 0
}
trap cleanup SIGTERM SIGINT EXIT

# Check if mock mode is requested
if [[ "${BACKEND_MODE,,}" == "mock" ]]; then
  echo "Starting in MOCK RunPod Serverless worker mode..."
  exec python3 -m app.serverless_handler
fi

# Real mode checks
if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "ERROR: model file not found at ${MODEL_PATH}" >&2
  exit 1
fi

BIN_PATH=$(resolve_binary "${LLAMA_BINARY}")
if [[ -z "${BIN_PATH}" ]]; then
  echo "ERROR: llama-server binary not found: ${LLAMA_BINARY}" >&2
  exit 1
fi

CMD=(
  "${BIN_PATH}"
  "--model" "${MODEL_PATH}"
  "--host" "${LLAMA_HOST}"
  "--port" "${LLAMA_PORT}"
  "--ctx-size" "${CONTEXT_SIZE}"
  "--n-gpu-layers" "${GPU_LAYERS}"
  "--parallel" "${PARALLEL}"
  "--cache-type-k" "${CACHE_TYPE_K}"
  "--cache-type-v" "${CACHE_TYPE_V}"
  "--embedding"
  "--log-disable"
)

if [[ -n "${API_KEY}" ]]; then
  CMD+=("--api-key" "${API_KEY}")
fi

echo "Starting llama-server backend on ${LLAMA_HOST}:${LLAMA_PORT} with model: ${MODEL_PATH}"
echo "Context: ${CONTEXT_SIZE} GPU_LAYERS: ${GPU_LAYERS} PARALLEL: ${PARALLEL}"
"${CMD[@]}" &
LLAMA_PID=$!

echo "Starting RunPod Serverless worker loop..."
python3 -m app.serverless_handler &
WORKER_PID=$!

# Wait for worker process to exit
wait -n "${LLAMA_PID}" "${WORKER_PID}" || true

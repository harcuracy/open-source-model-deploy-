FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    cmake \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 \
    && echo "/usr/local/cuda/lib64/stubs" > /etc/ld.so.conf.d/cuda-stubs.conf \
    && ldconfig

RUN git clone --branch b4200 https://github.com/ggml-org/llama.cpp.git /workspace/llama.cpp \
    && cd /workspace/llama.cpp \
    && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release \
             -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64/stubs" \
    && cmake --build build --config Release --target llama-server -j"$(nproc)" \
    && mkdir -p /dist/bin /dist/lib \
    && cp build/bin/llama-server /dist/bin/ \
    && find build -name "*.so*" -exec cp {} /dist/lib/ \; 2>/dev/null || true

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MODEL_PATH=/models/model.gguf \
    LLAMA_SERVER_HOST=127.0.0.1 \
    LLAMA_SERVER_PORT=8080 \
    LLAMA_SERVER_URL=http://127.0.0.1:8080/v1 \
    LLAMA_BACKEND_MODE=real \
    CONTEXT_SIZE=200000 \
    GPU_LAYERS=999 \
    PARALLEL=8 \
    CACHE_TYPE_K=q8_0 \
    CACHE_TYPE_V=q8_0 \
    PATH=/usr/local/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /dist/bin/ /usr/local/bin/
COPY --from=builder /dist/lib/ /usr/local/lib/
RUN ldconfig

COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    && python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip install -e .

RUN mkdir -p /models

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    log_level: str = Field(default="info", alias="LOG_LEVEL")

    model_name: str = Field(default="Qwen3.8-27B-GGUF", alias="MODEL_NAME")
    model_path: str = Field(default="/models/Qwen3.8-27B-GGUF-Q8_0.gguf", alias="MODEL_PATH")
    llama_server_url: str = Field(default="http://127.0.0.1:8080/v1", alias="LLAMA_SERVER_URL")
    llama_backend_mode: str = Field(default="real", alias="LLAMA_BACKEND_MODE")
    llama_server_binary: str = Field(default="llama-server", alias="LLAMA_SERVER_BINARY")
    llama_server_host: str = Field(default="127.0.0.1", alias="LLAMA_SERVER_HOST")
    llama_server_port: int = Field(default=8080, alias="LLAMA_SERVER_PORT")
    llama_context_size: int = Field(default=200000, alias="LLAMA_CONTEXT_SIZE")
    max_context_tokens: int = Field(default=200000, alias="MAX_CONTEXT_TOKENS")
    request_timeout_seconds: int = Field(default=180, alias="REQUEST_TIMEOUT_SECONDS")
    api_key: str = Field(default="", alias="API_KEY")
    gpu_layers: int = Field(default=999, alias="GPU_LAYERS")

    @property
    def backend_mode(self) -> str:
        return self.llama_backend_mode.lower()

    @computed_field
    @property
    def server_url(self) -> str:
        url = self.llama_server_url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        return url

    @computed_field
    @property
    def server_base_url(self) -> str:
        url = self.server_url
        if url.endswith("/v1"):
            return url[:-3]
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_settings_obj() -> Settings:
    return get_settings()


def _as_dict(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else vars(model)

from __future__ import annotations

import os
from dataclasses import dataclass, field


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.casefold() in {"1", "true", "yes", "on"}


def env_optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


def model_provider() -> str:
    return os.getenv("MODEL_PROVIDER", "openai").casefold()


def model_base_url() -> str:
    default = "https://api.openai.com/v1" if model_provider() == "openai" else "http://host.docker.internal:4000/v1"
    return (os.getenv("MODEL_BASE_URL", "").strip() or default).rstrip("/")


def model_api_key() -> str:
    provider_key = os.getenv("MODEL_API_KEY", "")
    if provider_key:
        return provider_key
    key_name = "OPENAI_API_KEY" if model_provider() == "openai" else "LITELLM_API_KEY"
    return os.getenv(key_name, "")


@dataclass(frozen=True)
class Settings:
    model_version: str = field(default_factory=lambda: os.getenv("MODEL_VERSION", "multimodal-responses-presidio-v1"))
    model_enabled: bool = field(default_factory=lambda: env_bool("MODEL_ENABLED", False))
    model_provider: str = field(default_factory=model_provider)
    model_base_url: str = field(default_factory=model_base_url)
    model_api_key: str = field(default_factory=model_api_key)
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", ""))
    model_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("MODEL_TIMEOUT_SECONDS", "20")))
    model_max_output_tokens: int = field(default_factory=lambda: int(os.getenv("MODEL_MAX_OUTPUT_TOKENS", "128")))
    model_temperature: float | None = field(default_factory=lambda: env_optional_float("MODEL_TEMPERATURE"))
    model_send_pii: bool = field(default_factory=lambda: env_bool("MODEL_SEND_PII", False))
    model_send_images: bool = field(default_factory=lambda: env_bool("MODEL_SEND_IMAGES", False))
    model_image_detail: str = field(default_factory=lambda: os.getenv("MODEL_IMAGE_DETAIL", "auto").casefold())
    model_max_images: int = field(default_factory=lambda: int(os.getenv("MODEL_MAX_IMAGES", "4")))
    presidio_enabled: bool = field(default_factory=lambda: env_bool("PRESIDIO_ENABLED", True))
    presidio_analyzer_url: str = field(
        default_factory=lambda: os.getenv("PRESIDIO_ANALYZER_URL", "http://presidio-analyzer:3000").rstrip("/")
    )
    presidio_anonymizer_url: str = field(
        default_factory=lambda: os.getenv("PRESIDIO_ANONYMIZER_URL", "http://presidio-anonymizer:3000").rstrip("/")
    )
    presidio_language: str = field(default_factory=lambda: os.getenv("PRESIDIO_LANGUAGE", "en"))
    presidio_score_threshold: float = field(default_factory=lambda: float(os.getenv("PRESIDIO_SCORE_THRESHOLD", "0.5")))
    presidio_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("PRESIDIO_TIMEOUT_SECONDS", "10")))
    pii_fail_closed: bool = field(default_factory=lambda: env_bool("PII_FAIL_CLOSED", True))

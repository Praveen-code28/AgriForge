import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # Core API Settings
    PROJECT_NAME: str = "AgriForge API"
    API_V1_PREFIX: str = "/api/v1"

    # Database & Auth Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agriforge"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    # DL Model & File Upload Settings
    MODEL_PATH: str = "checkpoints/agriforge_crop_health_v1.pth"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # External APIs & Paths
    OPENWEATHER_API_KEY: str = ""
    KNOWLEDGE_BASE_PATH: str = "ml/weather/knowledge"

    # LLM Settings.
    # For OpenAI-compatible endpoints (NVIDIA NIM, GLM, vLLM, Ollama, etc.) set
    # LLM_BASE_URL and keep the raw model id in LLM_MODEL; the provider layer
    # prefixes it with "openai/" so crewai routes it through the OpenAI-compatible
    # client. Provide LLM_API_KEY via the environment / .env, never in source.
    LLM_PROVIDER: str = "nvidia"
    LLM_MODEL: str = "z-ai/glm-5.2"  # raw model id; provider layer adds routing prefix
    LLM_API_KEY: str = ""
    LLM_BASE_URL: Optional[str] = "https://integrate.api.nvidia.com/v1"
    LLM_TIMEOUT_SECONDS: int = 45
    LLM_MAX_TOKENS: int = 900  # cap synthesis output for lower latency/cost

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR)

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    # Known crewai/litellm native provider prefixes. If the configured model
    # already starts with one of these, we leave it untouched.
    _KNOWN_PREFIXES = (
        "openai/", "anthropic/", "claude", "azure/", "azure_openai/", "gemini/",
        "google/", "bedrock/", "aws/", "openrouter/", "deepseek/", "ollama/",
        "ollama_chat/", "hosted_vllm/", "cerebras/", "dashscope/", "snowflake/",
        "nvidia_nim/",
    )

    @property
    def resolved_llm_model(self) -> str:
        """Model string with a routing prefix suitable for crewai/litellm.

        When a custom OpenAI-compatible base URL is configured (NVIDIA NIM, GLM,
        vLLM, ...) but the model id has no provider prefix, prepend ``openai/``
        so it is routed through the OpenAI-compatible client rather than being
        treated as an unknown native provider.
        """
        model = self.LLM_MODEL.strip()
        if any(model.startswith(p) for p in self._KNOWN_PREFIXES):
            return model
        if self.LLM_BASE_URL:
            return f"openai/{model}"
        return model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a cached instance of the Settings."""
    return Settings()


def validate_config(settings: Optional[Settings] = None) -> dict:
    """Validate configuration on startup.

    Logs clear, secret-free messages for missing required/optional settings and
    returns a structured summary. Never raises and never prints secret values.
    """
    settings = settings or get_settings()
    errors: List[str] = []
    warnings: List[str] = []

    # Required for auth.
    if not settings.SECRET_KEY or settings.SECRET_KEY in ("change-me-in-production", "change-me-to-a-long-random-string"):
        warnings.append("SECRET_KEY is using an insecure default; set a long random value for production.")
    if not settings.DATABASE_URL:
        errors.append("Missing required environment variable: DATABASE_URL")

    # Optional external services.
    if not settings.OPENWEATHER_API_KEY:
        warnings.append("OPTIONAL SERVICE UNAVAILABLE: OpenWeatherMap (OPENWEATHER_API_KEY missing). Weather analysis will be skipped; the rest of the pipeline continues with fallbacks.")
    if not settings.LLM_API_KEY:
        warnings.append("OPTIONAL SERVICE UNAVAILABLE: LLM (LLM_API_KEY missing). Reports will use the deterministic fallback synthesis.")

    for msg in errors:
        logger.error("CONFIGURATION ERROR: %s", msg)
    for msg in warnings:
        logger.warning(msg)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "llm_model": settings.resolved_llm_model,
        "llm_configured": bool(settings.LLM_API_KEY),
        "weather_configured": bool(settings.OPENWEATHER_API_KEY),
    }

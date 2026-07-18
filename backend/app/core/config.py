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
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # DL Model & File Upload Settings
    MODEL_PATH: str = "checkpoints/agriforge_crop_health_v1.pth"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # External APIs & Paths
    OPENWEATHER_API_KEY: str = ""
    KNOWLEDGE_BASE_PATH: str = "ml/weather/knowledge"

    # LLM Settings (CrewAI uses LiteLLM under the hood, so the model string must match LiteLLM's expected format)
    LLM_PROVIDER: str = "nvidia"
    LLM_MODEL: str = "z-ai/glm-5.2"  # Format: "{provider}/{model_name}"
    LLM_API_KEY: str = "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"
    LLM_BASE_URL: Optional[str] = "https://integrate.api.nvidia.com/v1"

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a cached instance of the Settings."""
    return Settings()

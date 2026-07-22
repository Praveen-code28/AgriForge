import logging
from functools import lru_cache
from typing import Optional

from crewai import LLM
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> Optional[LLM]:
    """
    Returns a configured CrewAI LLM instance based on environment variables.
    
    The LLM provider abstraction allows switching providers (OpenAI, Anthropic, 
    local LLMs via Ollama, NVIDIA NIM, etc.) without changing agent code.
    
    Returns None if initialization fails to prevent crashing the AgriForgeAgents 
    instantiation. Downstream task execution will fail safely and fallback to 
    deterministic results as enforced by AgriForgeCrew.
    """
    settings = get_settings()

    if not settings.LLM_API_KEY:
        logger.warning(
            "LLM_API_KEY not set; AI synthesis disabled. Reports will use the "
            "deterministic fallback."
        )
        return None

    model = settings.resolved_llm_model
    kwargs = {
        "model": model,
        "api_key": settings.LLM_API_KEY,
        "timeout": settings.LLM_TIMEOUT_SECONDS,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL

    try:
        logger.info(
            "Initializing LLM: model=%s base_url=%s", model, settings.LLM_BASE_URL
        )
        return LLM(**kwargs)
    except Exception as e:
        logger.error(
            "Failed to initialize LLM (model=%s, base_url=%s): %s. "
            "AI synthesis disabled; using deterministic fallback.",
            model,
            settings.LLM_BASE_URL,
            e,
        )
        return None

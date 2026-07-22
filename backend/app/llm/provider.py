import logging
from functools import lru_cache
from typing import Optional

from crewai import LLM
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> Optional[LLM]:
    """
    Create and return the CrewAI LLM used by all AgriForge agents.

    Supports OpenAI-compatible API providers such as NVIDIA NIM
    through LiteLLM.

    If initialization fails, None is returned so the AgriForge
    deterministic fallback pipeline can continue working.
    """

    settings = get_settings()

    try:
        # NVIDIA NIM exposes an OpenAI-compatible API.
        #
        # LiteLLM requires the "openai/" prefix so that it knows
        # which provider implementation should handle the model.
        model_name = settings.LLM_MODEL

        if settings.LLM_PROVIDER.lower() == "nvidia":
            if not model_name.startswith("openai/"):
                model_name = f"openai/{model_name}"

        kwargs = {
            "model": model_name,
        }

        if settings.LLM_API_KEY:
            kwargs["api_key"] = settings.LLM_API_KEY

        if settings.LLM_BASE_URL:
            kwargs["base_url"] = settings.LLM_BASE_URL

        logger.info(
            "Initializing CrewAI LLM | provider=%s | model=%s | base_url=%s",
            settings.LLM_PROVIDER,
            model_name,
            settings.LLM_BASE_URL,
        )

        llm = LLM(**kwargs)

        logger.info("CrewAI LLM initialized successfully.")

        return llm

    except Exception as e:
        logger.exception(
            "Failed to initialize CrewAI LLM with provider '%s' "
            "and model '%s': %s. "
            "AI orchestration will be disabled and AgriForge "
            "will fall back to the deterministic pipeline.",
            settings.LLM_PROVIDER,
            settings.LLM_MODEL,
            e,
        )

        return None


def clear_llm_cache():
    """
    Clear cached LLM instance.

    Useful when changing LLM configuration during development.
    """
    get_llm.cache_clear()
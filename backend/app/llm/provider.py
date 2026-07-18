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
    
    kwargs = {
        "model": settings.LLM_MODEL,
    }
    
    # Only pass api_key if explicitly set. Otherwise, LiteLLM will automatically
    # look for standard environment variables (e.g., OPENAI_API_KEY).
    if settings.LLM_API_KEY:
        kwargs["api_key"] = settings.LLM_API_KEY
        
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL
        
    try:
        logger.info(f"Initializing CrewAI LLM with model: {settings.LLM_MODEL}")
        return LLM(**kwargs)
    except Exception as e:
        logger.error(
            f"Failed to initialize LLM with model '{settings.LLM_MODEL}': {e}. "
            "AI orchestration will be disabled. Falling back to deterministic pipeline."
        )
        return None

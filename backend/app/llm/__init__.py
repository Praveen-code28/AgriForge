"""AgriForge LLM package.

Re-exports the high-level LLM provider factory so callers can do:

    from app.llm import get_llm

instead of importing the concrete module path. Keeping the indirect
import in one place lets us later swap to a lazy loader or a different
factory without touching every consumer.
"""

from __future__ import annotations

from .provider import get_llm

__all__ = ["get_llm"]

"""AgriForge search package.

Re-exports the high-level search provider factory and base class so callers can do:

    from app.search import get_search_provider, SearchProvider

instead of importing the concrete module path. Keeping the indirect
import in one place lets us later swap to a lazy loader or a different
factory without touching every consumer.
"""

from __future__ import annotations

from .provider import get_search_provider, SearchProvider

__all__ = ["get_search_provider", "SearchProvider"]

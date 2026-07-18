import logging
import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# We use duckduckgo-search (the ddgs package).
try:
    from duckduckgo_search import DDGS
except ImportError:
    logger.warning("duckduckgo_search package is not installed. Search features will be disabled.")
    DDGS = None


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        pass


class DDGSSearchProvider(SearchProvider):
    def __init__(self):
        # No need to raise ImportError here; search() will safely return [] if DDGS is None.
        # This prevents crashing the request pipeline if the package is missing.
        pass

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if DDGS is None:
            logger.error("DuckDuckGo Search package is not installed. Returning empty results.")
            return []

        results = []
        try:
            with DDGS() as ddgs:
                # Use standard text search
                ddgs_results = list(ddgs.text(query, max_results=max_results))
                
            for res in ddgs_results:
                results.append({
                    "title": res.get("title", ""),
                    "url": res.get("href", ""),
                    "snippet": res.get("body", ""),
                    "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
        except Exception as e:
            # Handle potential rate limits or connection errors
            logger.error(f"Error during DDGS search: {e}")
            
        return results


def get_search_provider() -> SearchProvider:
    """
    Returns the search provider.
    Here we could switch based on env variables in the future,
    e.g., if settings.SEARCH_PROVIDER == 'tavily' return TavilySearchProvider()
    """
    return DDGSSearchProvider()

import json
import logging
from urllib.parse import urlparse
from typing import Type, Optional
import requests

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from backend.app.search.provider import get_search_provider

logger = logging.getLogger(__name__)

# If bs4 is available, we use it to parse full text.
try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning("beautifulsoup4 package is not installed. Content extraction will be skipped.")
    BeautifulSoup = None


class TrustedSearchInput(BaseModel):
    query: str = Field(description="The agricultural topic to search for.")


# Define the trusted domain rules
TRUSTED_EXACT_DOMAINS = {
    "fao.org",
    "ippc.int",
    "icar.gov.in",
}

TRUSTED_SUFFIXES = (
    ".gov.in",
    ".nic.in",
    ".edu",
    ".fao.org",
    ".ippc.int",
    ".icar.gov.in",
    ".gov",
)

class TrustedAgricultureSearchTool(BaseTool):
    name: str = "trusted_agriculture_search"
    description: str = (
        "Searches the web for agricultural information, strictly filtering for trusted authoritative "
        "domains like FAO, IPPC, .edu, and .gov.in. Use this to find verified agricultural practices, "
        "disease treatments, and pesticide regulations."
    )
    args_schema: Type[BaseModel] = TrustedSearchInput

    def _is_trusted_domain(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Strip "www." for consistent matching
            if domain.startswith("www."):
                domain = domain[4:]

            if domain in TRUSTED_EXACT_DOMAINS:
                return True
                
            for suffix in TRUSTED_SUFFIXES:
                if domain.endswith(suffix):
                    # Suffixes start with a dot, so endswith is safe (e.g. 'fakeedu.com' won't match '.edu')
                    return True
                    
            return False
        except Exception:
            return False
            
    def _extract_page_content(self, url: str) -> str:
        """Attempt to fetch and extract the text from the URL."""
        if not BeautifulSoup:
            return ""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=" ", strip=True)
                # Return first 1500 chars to avoid overwhelming the LLM
                return text[:1500] + ("..." if len(text) > 1500 else "")
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
        return ""

    def _run(self, query: str) -> str:
        try:
            provider = get_search_provider()
            # Fetch a larger number of results so we can filter them down
            raw_results = provider.search(query, max_results=15)
        except Exception as e:
            logger.error(f"Failed to execute search via provider: {e}")
            return "Search tool failed to execute properly."
            
        trusted_results = []
        for res in raw_results:
            url = res.get("url", "")
            if self._is_trusted_domain(url):
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                
                # Optionally fetch content
                full_text = self._extract_page_content(url)
                
                trusted_results.append({
                    "title": res.get("title"),
                    "url": url,
                    "domain": domain,
                    "organization_hint": domain, 
                    "snippet": res.get("snippet"),
                    "extracted_content": full_text,
                    "retrieved_at": res.get("retrieved_at")
                })
                
                if len(trusted_results) >= 3:
                    break
                    
        if not trusted_results:
            return "No information found from trusted agricultural sources."
            
        return json.dumps({
            "query": query,
            "results": trusted_results
        }, indent=2)

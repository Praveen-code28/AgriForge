import ipaddress
import json
import logging
import socket
from urllib.parse import urlparse
from typing import Type, Optional
import requests

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from backend.app.search.provider import get_search_provider

logger = logging.getLogger(__name__)

# SSRF / fetch safety limits.
MAX_CONTENT_BYTES = 512 * 1024  # 512 KB cap on fetched page size
MAX_REDIRECTS = 3
FETCH_TIMEOUT = 5

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
            
    def _is_public_host(self, hostname: str) -> bool:
        """Resolve a hostname and ensure every IP is public (SSRF guard)."""
        if not hostname:
            return False
        try:
            infos = socket.getaddrinfo(hostname, None)
        except Exception as e:  # noqa: BLE001
            logger.warning("DNS resolution failed for %s: %s", hostname, e)
            return False
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                logger.warning("Blocked SSRF attempt to non-public IP %s (%s)", ip, hostname)
                return False
        return True

    def _safe_url(self, url: str) -> bool:
        """A URL is safe only if it is https/http, on a trusted domain, and
        resolves exclusively to public IP addresses."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not self._is_trusted_domain(url):
            return False
        return self._is_public_host(parsed.hostname or "")

    def _extract_page_content(self, url: str) -> str:
        """Fetch and extract text from a trusted URL with SSRF protections.

        Guards: scheme allow-list, trusted-domain check, public-IP check on every
        redirect hop, response size cap, and content-type check.
        """
        if not BeautifulSoup:
            return ""
        headers = {"User-Agent": "AgriForge/1.0 (+agricultural-research-bot)"}
        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                if not self._safe_url(current):
                    logger.warning("Refusing to fetch unsafe/untrusted URL: %s", current)
                    return ""
                resp = requests.get(
                    current,
                    headers=headers,
                    timeout=FETCH_TIMEOUT,
                    stream=True,
                    allow_redirects=False,
                )
                if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location")
                    resp.close()
                    if not location:
                        return ""
                    current = requests.compat.urljoin(current, location)
                    continue

                if resp.status_code != 200:
                    resp.close()
                    return ""

                content_type = resp.headers.get("Content-Type", "")
                if "html" not in content_type and "text" not in content_type:
                    resp.close()
                    return ""

                chunks = b""
                for chunk in resp.iter_content(chunk_size=8192):
                    chunks += chunk
                    if len(chunks) >= MAX_CONTENT_BYTES:
                        break
                resp.close()

                soup = BeautifulSoup(chunks, "html.parser")
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=" ", strip=True)
                return text[:1500] + ("..." if len(text) > 1500 else "")
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to extract content from %s: %s", url, e)
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

"""AgriForge crew package.

Re-exports the high-level crew orchestrator so callers can do:

    from app.crew import AgriForgeCrew

instead of importing the concrete module path. Keeping the indirect
import in one place lets us later swap to lazy loading or a factory
function without touching every consumer.
"""

from __future__ import annotations

from .agriforge_crew import AgriForgeCrew

__all__ = ["AgriForgeCrew"]

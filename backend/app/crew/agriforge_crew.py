"""AgriForge report orchestration.

Historically this ran a sequential multi-agent CrewAI pipeline (weather →
treatment → research → risk → report), which meant 4-5 LLM calls per analysis
and unacceptable latency. It now delegates to a single-call synthesis pipeline
(see ``report_synthesis``): deterministic systems remain the source of truth and
the LLM is used at most once, with a hard timeout and a deterministic fallback.

The class name/interface is preserved for backwards compatibility.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from backend.app.services import report_synthesis

logger = logging.getLogger(__name__)


class AgriForgeCrew:
    def __init__(self, agents: Any):
        self.agents = agents
        self.last_report_source = "deterministic_fallback"

    def _llm(self) -> Any:
        return getattr(self.agents, "llm", None)

    def _search_fn(self) -> Optional[Any]:
        tool = getattr(self.agents, "search_tool", None)
        if tool is None:
            return None

        def _run(query: str):
            import json as _json

            raw = tool._run(query)
            try:
                data = _json.loads(raw)
                return data.get("results", []) if isinstance(data, dict) else []
            except Exception:  # noqa: BLE001
                return []

        return _run

    def run(
        self,
        disease_result: Dict[str, Any],
        weather_result: Dict[str, Any],
        treatment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synchronous wrapper. Use run_async() from FastAPI endpoints."""
        return asyncio.run(
            self.run_async(disease_result, weather_result, treatment_result)
        )

    async def run_async(
        self,
        disease_result: Dict[str, Any],
        weather_result: Dict[str, Any],
        treatment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        report, source, timings = await report_synthesis.generate_report(
            disease_result=disease_result,
            weather_result=weather_result,
            treatment_result=treatment_result,
            llm=self._llm(),
            search_fn=self._search_fn(),
        )
        self.last_report_source = source
        self.last_timings = timings
        logger.info("AI_REPORT_SOURCE=%s TIMING %s", source, timings)
        return report

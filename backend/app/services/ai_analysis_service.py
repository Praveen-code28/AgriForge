import logging
import sys
import time
from typing import Any
from sqlalchemy.orm import Session

from backend.app.services import report_synthesis
from backend.app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class AIAnalysisService:
    def __init__(self, analysis_service: AnalysisService, db: Session, prediction_repo: Any = None):
        self.analysis_service = analysis_service
        self.db = db
        self.crew_available = False
        
        try:
            from backend.app.agents.agriforge_agents import AgriForgeAgents
            from backend.app.crew.agriforge_crew import AgriForgeCrew
            
            self.agents = AgriForgeAgents(
                disease_service=analysis_service.disease_service,
                weather_service=analysis_service.weather_service,
                treatment_service=analysis_service.treatment_service,
                prediction_repo=prediction_repo,
                db=db,
            )
            self.crew = AgriForgeCrew(self.agents)
            self.crew_available = True
        except Exception as e:
            sys.stderr.write(f"Warning: CrewAI is not available: {e}. Using deterministic AI report fallback.\n")
            self.agents = None
            self.crew = None

    async def complete_ai_analysis(
        self,
        image_path: str,
        lat: float | None = None,
        lon: float | None = None,
        address: str | None = None,
    ) -> dict[str, Any]:
        """
        Runs the deterministic pipeline first, then optionally runs the CrewAI orchestration.
        Guarantees fallback to deterministic results if LLM or CrewAI fails.
        """
        # 1. Run deterministic pipeline (source of truth). Timed for diagnostics.
        t0 = time.perf_counter()
        try:
            base_results = self.analysis_service.complete_analysis(image_path, lat, lon, address)
        except Exception as e:
            # If the core deterministic pipeline fails, we have to raise.
            raise RuntimeError(f"Core analysis failed: {e}") from e
        deterministic_time = round(time.perf_counter() - t0, 3)

        disease_result = base_results["disease"]
        treatment_result = base_results["treatment"]
        weather_result = base_results["weather"]

        # 2. Single-call AI synthesis with deterministic fallback.
        source = "deterministic_fallback"
        timings: dict[str, Any] = {"deterministic": deterministic_time}
        if self.crew_available and self.crew is not None:
            try:
                ai_report = await self.crew.run_async(disease_result, weather_result, treatment_result)
                source = getattr(self.crew, "last_report_source", "deterministic_fallback")
                timings.update(getattr(self.crew, "last_timings", {}) or {})
            except Exception as e:
                logger.warning("AI synthesis failed: %s. Using deterministic report.", e)
                ai_report = report_synthesis.build_deterministic_report(
                    disease_result, weather_result, treatment_result
                )
        else:
            ai_report = report_synthesis.build_deterministic_report(
                disease_result, weather_result, treatment_result
            )

        timings["total_analysis"] = round(time.perf_counter() - t0, 3)
        logger.info("AI_REPORT_SOURCE=%s TIMING %s", source, timings)

        # 3. Format final response
        return {
            "disease": disease_result,
            "treatment": treatment_result,
            "weather": weather_result,
            "combined": base_results["combined"],
            "ai_report": ai_report,
            "ai_report_source": source,
            "timings": timings,
        }


from typing import Any
from sqlalchemy.orm import Session

from backend.app.services.analysis_service import AnalysisService
from backend.app.agents.agriforge_agents import AgriForgeAgents
from backend.app.crew.agriforge_crew import AgriForgeCrew


class AIAnalysisService:
    def __init__(self, analysis_service: AnalysisService, db: Session, prediction_repo: Any = None):
        self.analysis_service = analysis_service
        self.db = db
        
        # Initialize agents and crew
        self.agents = AgriForgeAgents(
            disease_service=analysis_service.disease_service,
            weather_service=analysis_service.weather_service,
            treatment_service=analysis_service.treatment_service,
            prediction_repo=prediction_repo,
            db=db,
        )
        self.crew = AgriForgeCrew(self.agents)

    def complete_ai_analysis(
        self,
        image_path: str,
        lat: float | None = None,
        lon: float | None = None,
        address: str | None = None,
    ) -> dict[str, Any]:
        """
        Runs the deterministic pipeline first, then optionally runs the CrewAI orchestration.
        Guarantees fallback to deterministic results if LLM fails.
        """
        # 1. Run deterministic pipeline
        try:
            base_results = self.analysis_service.complete_analysis(image_path, lat, lon, address)
        except Exception as e:
            # If the core deterministic pipeline fails, we have to raise.
            raise RuntimeError(f"Core analysis failed: {e}") from e

        disease_result = base_results["disease"]
        treatment_result = base_results["treatment"]
        weather_result = base_results["weather"]

        # 2. Run CrewAI Orchestration
        ai_report = None
        try:
            ai_report = self.crew.run(disease_result, weather_result, treatment_result)
        except Exception as e:
            print(f"CrewAI orchestration failed: {e}. Falling back to deterministic results.")
            # We don't raise here, we fall back to deterministic results

        # 3. Format final response
        return {
            "disease": disease_result,
            "treatment": treatment_result,
            "weather": weather_result,
            "combined": base_results["combined"],
            "ai_report": ai_report, # Will be None if CrewAI failed, handled cleanly by the client
        }

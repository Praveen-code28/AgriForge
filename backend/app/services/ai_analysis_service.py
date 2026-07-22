import sys
from typing import Any
from sqlalchemy.orm import Session

from backend.app.services.analysis_service import AnalysisService


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

    def complete_ai_analysis(
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
        crop = disease_result.get("primary", {}).get("plant", "Unknown")
        disease = disease_result.get("primary", {}).get("disease", "Unknown")

        if self.crew_available and self.crew is not None:
            try:
                ai_report = self.crew.run(disease_result, weather_result, treatment_result)
            except Exception as e:
                print(f"CrewAI orchestration failed: {e}. Falling back to deterministic results.")

        if ai_report is None:
            # Construct the fallback report dict directly matching AIReport schema
            ai_report = {
                "crop": crop,
                "disease": {
                    "name": disease,
                    "confidence": disease_result.get("primary", {}).get("confidence", 0.0)
                },
                "weather": {
                    "summary": "Weather data retrieved successfully.",
                    "impact": "Unable to determine impact due to AI synthesis absence."
                },
                "risk": {
                    "level": "MODERATE" if disease.lower() != "healthy" else "LOW",
                    "reasons": ["AI report synthesis skipped. Relying on local rule-based database."]
                },
                "treatment": {
                    "immediate_actions": [treatment_result.get("farmer_advice") or treatment_result.get("message") or "Contact local advisor."] if disease.lower() != "healthy" else [],
                    "preventive_measures": []
                },
                "maintenance": [],
                "if_untreated": "Please consult a local agricultural extension officer immediately.",
                "additional_research": ["CrewAI orchestration is not installed."],
                "farmer_summary": f"Automated analysis for {crop} encountering {disease}. Refer to local data.",
                "sources": []
            }

        # 3. Format final response
        return {
            "disease": disease_result,
            "treatment": treatment_result,
            "weather": weather_result,
            "combined": base_results["combined"],
            "ai_report": ai_report,
        }


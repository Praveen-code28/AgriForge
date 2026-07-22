import asyncio
import json
import logging
from typing import Any, Dict

from crewai import Crew, Process

from backend.app.agents.agriforge_agents import AgriForgeAgents
from backend.app.crew.tasks import AgriForgeTasks
from backend.app.schemas.ai_report import (
    AIReport,
    AIReportDisease,
    AIReportWeather,
    AIReportRisk,
    AIReportTreatment,
)

logger = logging.getLogger(__name__)


class AgriForgeCrew:
    def __init__(self, agents: AgriForgeAgents):
        self.agents = agents
        self.tasks_factory = AgriForgeTasks(agents)
        self.last_report_source = "deterministic_fallback"

    def run(self, disease_result: Dict[str, Any], weather_result: Dict[str, Any], treatment_result: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.run_async(disease_result, weather_result, treatment_result))

    async def run_async(
        self,
        disease_result: Dict[str, Any],
        weather_result: Dict[str, Any],
        treatment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes the CrewAI orchestration asynchronously using the supported CrewAI API.
        Handles failures by falling back to a deterministic, safe minimal report.
        """
        crop = disease_result.get("primary", {}).get("plant", "Unknown")
        disease = disease_result.get("primary", {}).get("disease", "Unknown")
        is_healthy = disease.lower() == "healthy" or disease == "Unknown"

        weather_task = self.tasks_factory.weather_analysis_task(json.dumps(weather_result))
        treatment_task = self.tasks_factory.treatment_task(json.dumps(treatment_result))

        tasks_list = [weather_task, treatment_task]

        knowledge_found = treatment_result.get("found", False)
        if not is_healthy and not knowledge_found:
            research_task = self.tasks_factory.research_task(crop, disease)
            tasks_list.append(research_task)

        risk_task = self.tasks_factory.risk_analysis_task()
        report_task = self.tasks_factory.report_task()
        report_task.output_pydantic = AIReport
        tasks_list.extend([risk_task, report_task])

        crew = Crew(
            agents=[t.agent for t in tasks_list],
            tasks=tasks_list,
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = await crew.kickoff_async(
                inputs={
                    "crop": crop,
                    "disease": disease,
                    "confidence": disease_result.get("primary", {}).get("confidence", 0.0),
                    "weather_result": weather_result,
                    "treatment_result": treatment_result,
                }
            )

            if hasattr(result, "pydantic") and result.pydantic:
                self.last_report_source = "crewai"
                return result.pydantic.model_dump()

            if isinstance(result, dict):
                self.last_report_source = "crewai"
                return result

            raw_str = str(result)
            if "```json" in raw_str:
                raw_str = raw_str.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(raw_str)
            self.last_report_source = "crewai"
            return parsed
        except Exception as exc:
            logger.error("Crew execution failed: %s. Falling back to deterministic AI report.", exc)
            self.last_report_source = "deterministic_fallback"

            fallback_report = AIReport(
                crop=crop,
                disease=AIReportDisease(
                    name=disease,
                    confidence=disease_result.get("primary", {}).get("confidence", 0.0),
                ),
                weather=AIReportWeather(
                    summary="Weather data retrieved successfully.",
                    impact="Unable to determine impact due to AI synthesis failure.",
                ),
                risk=AIReportRisk(
                    level="UNKNOWN",
                    reasons=["AI report synthesis failed. Relying on local data only."],
                ),
                treatment=AIReportTreatment(immediate_actions=[], preventive_measures=[]),
                maintenance=[],
                if_untreated="Please consult a local agricultural extension officer immediately.",
                additional_research=["AI research module failed to execute."],
                farmer_summary=f"Automated analysis for {crop} encountering {disease} encountered an error during AI synthesis. Refer to raw data.",
                sources=[],
            )
            return fallback_report.model_dump()

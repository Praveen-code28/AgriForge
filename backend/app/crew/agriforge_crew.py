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

    def run(
        self, 
        disease_result: Dict[str, Any], 
        weather_result: Dict[str, Any], 
        treatment_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes the CrewAI orchestration.
        Dynamically adds the research agent ONLY if local treatment knowledge is insufficient.
        Handles failures by falling back to a deterministic, safe minimal report.
        """
        crop = disease_result.get("primary", {}).get("plant", "Unknown")
        disease = disease_result.get("primary", {}).get("disease", "Unknown")
        is_healthy = disease.lower() == "healthy" or disease == "Unknown"

        # 1. Base Tasks (Weather & Treatment)
        weather_task = self.tasks_factory.weather_analysis_task(json.dumps(weather_result))
        treatment_task = self.tasks_factory.treatment_task(json.dumps(treatment_result))
        
        tasks_list = [weather_task, treatment_task]

        # 2. Conditional Research Task
        # Check if local knowledge was insufficient and not explicitly healthy
        knowledge_found = treatment_result.get("found", False)
        
        # Only research if disease is not healthy AND we didn't find treatment
        if not is_healthy and not knowledge_found:
            # Check if the research agent is available (might be disabled if search APIs failed earlier)
            research_task = self.tasks_factory.research_task(crop, disease)
            tasks_list.append(research_task)

        # 3. Final Synthesis Tasks
        risk_task = self.tasks_factory.risk_analysis_task()
        report_task = self.tasks_factory.report_task()
        
        # In modern CrewAI, we can enforce Pydantic output directly on the task
        report_task.output_pydantic = AIReport
        
        tasks_list.extend([risk_task, report_task])

        # Create and run the Crew
        crew = Crew(
            agents=[t.agent for t in tasks_list],
            tasks=tasks_list,
            process=Process.sequential,
            verbose=True,
        )

        try:
            # Kickoff the crew
            result = crew.kickoff()
            
            # CrewAI returns a CrewOutput object in newer versions.
            # If output_pydantic is set on the final task, result.pydantic should contain it.
            if hasattr(result, "pydantic") and result.pydantic:
                return result.pydantic.model_dump()
            
            # Fallback if it returned a raw JSON string (CrewAI sometimes does this if Pydantic parsing fails internally)
            raw_str = str(result)
            if "```json" in raw_str:
                raw_str = raw_str.split("```json")[1].split("```")[0].strip()
            return json.loads(raw_str)
            
        except Exception as e:
            logger.error(f"Crew execution failed: {e}. Falling back to deterministic AI report.")
            
            # DETERMINISTIC FALLBACK: Construct the Pydantic models explicitly
            fallback_report = AIReport(
                crop=crop,
                disease=AIReportDisease(
                    name=disease, 
                    confidence=disease_result.get("primary", {}).get("confidence", 0.0)
                ),
                weather=AIReportWeather(
                    summary="Weather data retrieved successfully.", 
                    impact="Unable to determine impact due to AI synthesis failure."
                ),
                risk=AIReportRisk(
                    level="UNKNOWN",
                    reasons=["AI report synthesis failed. Relying on local data only."]
                ),
                treatment=AIReportTreatment(
                    immediate_actions=[], 
                    preventive_measures=[]
                ),
                maintenance=[],
                if_untreated="Please consult a local agricultural extension officer immediately.",
                additional_research=["AI research module failed to execute."],
                farmer_summary=f"Automated analysis for {crop} encountering {disease} encountered an error during AI synthesis. Refer to raw data.",
                sources=[]
            )
            return fallback_report.model_dump()

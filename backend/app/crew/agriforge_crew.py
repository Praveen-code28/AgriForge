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
    """
    CrewAI orchestration layer for AgriForge.

    This class combines:
    - Disease detection results from the DL model
    - Weather analysis results
    - Local treatment knowledge
    - Optional trusted agricultural research
    - Risk analysis
    - Final farmer-friendly AI report

    If CrewAI or the LLM fails, the system safely falls back
    to a deterministic report.
    """

    def __init__(self, agents: AgriForgeAgents):
        self.agents = agents
        self.tasks_factory = AgriForgeTasks(agents)
        self.last_report_source = "deterministic_fallback"

    def run(
        self,
        disease_result: Dict[str, Any],
        weather_result: Dict[str, Any],
        treatment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper.

        Use run_async() when calling from FastAPI async endpoints.
        """

        return asyncio.run(
            self.run_async(
                disease_result=disease_result,
                weather_result=weather_result,
                treatment_result=treatment_result,
            )
        )

    async def run_async(
        self,
        disease_result: Dict[str, Any],
        weather_result: Dict[str, Any],
        treatment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the AgriForge CrewAI pipeline asynchronously.

        Pipeline:

        Disease DL Result
                |
                v
        Weather Analysis
                |
                v
        Treatment Knowledge
                |
                v
        Optional Trusted Research
                |
                v
        Risk Analysis
                |
                v
        Farmer-Friendly Final Report

        If CrewAI execution fails, a safe deterministic
        fallback report is returned.
        """

        # -----------------------------------------------------
        # 1. Extract deterministic disease information
        # -----------------------------------------------------

        primary_result = disease_result.get("primary", {})

        crop = primary_result.get("plant", "Unknown")
        disease = primary_result.get("disease", "Unknown")
        confidence = primary_result.get("confidence", 0.0)

        is_healthy = (
            str(disease).lower() == "healthy"
            or str(disease).lower() == "unknown"
        )

        logger.info(
            "Starting AgriForge CrewAI analysis: crop=%s disease=%s",
            crop,
            disease,
        )

        # -----------------------------------------------------
        # 2. Convert deterministic results to JSON
        #
        # CrewAI template variables must receive strings when
        # inserted into task descriptions.
        # -----------------------------------------------------

        weather_data_json = json.dumps(
            weather_result,
            default=str,
            ensure_ascii=False,
        )

        treatment_data_json = json.dumps(
            treatment_result,
            default=str,
            ensure_ascii=False,
        )

        disease_data_json = json.dumps(
            disease_result,
            default=str,
            ensure_ascii=False,
        )

        # -----------------------------------------------------
        # 3. Create Weather Analysis Task
        # -----------------------------------------------------

        weather_task = self.tasks_factory.weather_analysis_task(
            weather_data_json
        )

        # -----------------------------------------------------
        # 4. Create Treatment Task
        # -----------------------------------------------------

        treatment_task = self.tasks_factory.treatment_task(
            treatment_data_json
        )

        tasks_list = [
            weather_task,
            treatment_task,
        ]

        # -----------------------------------------------------
        # 5. Determine whether trusted external research
        #    is required
        #
        # Research is only performed when:
        # - Disease is not healthy
        # - Local treatment knowledge is unavailable
        # -----------------------------------------------------

        knowledge_found = treatment_result.get("found", False)

        if not is_healthy and not knowledge_found:

            logger.info(
                "Local treatment knowledge unavailable. "
                "Enabling trusted agricultural research."
            )

            research_task = self.tasks_factory.research_task(
                crop,
                disease,
            )

            tasks_list.append(research_task)

        else:

            logger.info(
                "Trusted research skipped. "
                "Local treatment knowledge available or crop healthy."
            )

        # -----------------------------------------------------
        # 6. Risk Analysis Task
        # -----------------------------------------------------

        risk_task = self.tasks_factory.risk_analysis_task()

        tasks_list.append(risk_task)

        # -----------------------------------------------------
        # 7. Final Farmer Report Task
        # -----------------------------------------------------

        report_task = self.tasks_factory.report_task()

        # Enforce structured Pydantic output
        report_task.output_pydantic = AIReport

        tasks_list.append(report_task)

        # -----------------------------------------------------
        # 8. Build CrewAI Crew
        # -----------------------------------------------------

        crew = Crew(
            agents=[task.agent for task in tasks_list],
            tasks=tasks_list,
            process=Process.sequential,
            verbose=True,
        )

        # -----------------------------------------------------
        # 9. Execute CrewAI asynchronously
        # -----------------------------------------------------

        try:

            result = await crew.kickoff_async(
                inputs={
                    # Basic prediction information
                    "crop": crop,
                    "disease": disease,
                    "confidence": confidence,

                    # JSON template variables
                    #
                    # These names MUST match variables such as:
                    # {weather_data_json}
                    # {treatment_data_json}
                    # {disease_data_json}
                    #
                    # inside CrewAI task descriptions.
                    "weather_data_json": weather_data_json,
                    "treatment_data_json": treatment_data_json,
                    "disease_data_json": disease_data_json,

                    # Keep raw data available if future tasks
                    # require direct dictionary access.
                    "weather_result": weather_result,
                    "treatment_result": treatment_result,
                    "disease_result": disease_result,
                }
            )

            # -------------------------------------------------
            # 10. Handle Pydantic structured output
            # -------------------------------------------------

            if hasattr(result, "pydantic") and result.pydantic:

                logger.info(
                    "AI_REPORT_SOURCE=crewai"
                )

                self.last_report_source = "crewai"

                return result.pydantic.model_dump()

            # -------------------------------------------------
            # 11. Handle dictionary output
            # -------------------------------------------------

            if isinstance(result, dict):

                logger.info(
                    "AI_REPORT_SOURCE=crewai"
                )

                self.last_report_source = "crewai"

                return result

            # -------------------------------------------------
            # 12. Attempt JSON parsing
            # -------------------------------------------------

            raw_str = str(result).strip()

            # Remove Markdown JSON fences if the LLM returns them
            if "```json" in raw_str:

                raw_str = (
                    raw_str
                    .split("```json", 1)[1]
                    .split("```", 1)[0]
                    .strip()
                )

            elif raw_str.startswith("```"):

                raw_str = (
                    raw_str
                    .split("```", 1)[1]
                    .split("```", 1)[0]
                    .strip()
                )

            parsed = json.loads(raw_str)

            logger.info(
                "AI_REPORT_SOURCE=crewai"
            )

            self.last_report_source = "crewai"

            return parsed

        # -----------------------------------------------------
        # 13. Safe Deterministic Fallback
        # -----------------------------------------------------

        except Exception as exc:

            logger.exception(
                "Crew execution failed: %s. "
                "Falling back to deterministic AI report.",
                exc,
            )

            logger.info(
                "AI_REPORT_SOURCE=deterministic_fallback"
            )

            self.last_report_source = "deterministic_fallback"

            # Try to preserve useful deterministic treatment
            # information when CrewAI fails.

            immediate_actions = treatment_result.get(
                "immediate_actions",
                [],
            )

            preventive_measures = treatment_result.get(
                "preventive_measures",
                [],
            )

            # Ensure correct types
            if not isinstance(immediate_actions, list):
                immediate_actions = []

            if not isinstance(preventive_measures, list):
                preventive_measures = []

            fallback_report = AIReport(

                crop=crop,

                disease=AIReportDisease(
                    name=disease,
                    confidence=confidence,
                ),

                weather=AIReportWeather(
                    summary=(
                        "Weather data was retrieved, but the AI "
                        "analysis could not be completed."
                    ),
                    impact=(
                        "Weather impact could not be synthesized "
                        "by the AI system. Refer to available "
                        "weather data and local agricultural guidance."
                    ),
                ),

                risk=AIReportRisk(
                    level="UNKNOWN",
                    reasons=[
                        "AI risk synthesis was unavailable.",
                        "Disease detection results remain available.",
                    ],
                ),

                treatment=AIReportTreatment(
                    immediate_actions=immediate_actions,
                    preventive_measures=preventive_measures,
                ),

                maintenance=[
                    "Monitor the crop regularly for changes in symptoms.",
                    "Follow locally approved agricultural practices.",
                ],

                if_untreated=(
                    "The condition may worsen if left untreated. "
                    "Consult a qualified agricultural extension officer "
                    "for crop-specific guidance."
                ),

                additional_research=[
                    "AI-assisted research was unavailable during this analysis."
                ],

                farmer_summary=(
                    f"AgriForge detected {disease} in {crop}. "
                    "The AI report generation service was unavailable, "
                    "so this report uses available deterministic analysis data."
                ),

                sources=[],
            )

            return fallback_report.model_dump()
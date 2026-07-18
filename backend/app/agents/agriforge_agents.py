import logging
from typing import Any, List, Optional

from crewai import Agent

from backend.app.llm.provider import get_llm
from backend.app.tools.service_tools import (
    DiseasePredictionTool,
    WeatherAnalysisTool,
    TreatmentKnowledgeTool,
    PredictionHistoryTool,
)
from backend.app.tools.trusted_search_tool import TrustedAgricultureSearchTool

logger = logging.getLogger(__name__)


class AgriForgeAgents:
    """
    Orchestrates the creation of specialized CrewAI agents for the AgriForge pipeline.
    
    Agents are designed to strictly respect deterministic results (DL disease prediction, 
    weather analysis) and use LLM/search capabilities only to supplement, synthesize, 
    and format the final farmer report. 
    """

    def __init__(
        self,
        disease_service: Optional[Any] = None,
        weather_service: Optional[Any] = None,
        treatment_service: Optional[Any] = None,
        prediction_repo: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        # LLM Provider initialization
        self.llm = get_llm()
        
        # Initialize deterministic internal tools
        self.disease_tool = (
            DiseasePredictionTool(disease_service=disease_service) 
            if disease_service 
            else None
        )
        self.weather_tool = (
            WeatherAnalysisTool(weather_service=weather_service) 
            if weather_service 
            else None
        )
        self.treatment_tool = (
            TreatmentKnowledgeTool(treatment_service=treatment_service) 
            if treatment_service 
            else None
        )
        self.history_tool = (
            PredictionHistoryTool(prediction_repo=prediction_repo, db=db) 
            if prediction_repo and db 
            else None
        )
        
        # Initialize external search tool safely
        # Network/API failures should not break the deterministic pipeline
        try:
            self.search_tool = TrustedAgricultureSearchTool()
        except Exception as e:
            logger.error(
                f"Failed to initialize TrustedAgricultureSearchTool: {e}. "
                "Web research will be disabled for this run."
            )
            self.search_tool = None

    def weather_analysis_agent(self) -> Agent:
        """Analyzes weather data and its impact on disease spread."""
        tools: List[Any] = [self.weather_tool] if self.weather_tool else []
        
        return Agent(
            role="Agricultural Weather Analyst",
            goal="Analyze current and forecasted weather conditions and explain their impact on the detected crop and disease.",
            backstory=(
                "You are an expert agrometeorologist. You use exact data provided by deterministic "
                "weather models and translate it into practical advice for farmers. You never invent "
                "weather conditions or temperature values. If weather data is provided to you, you treat "
                "it as the absolute source of truth."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
        )

    def treatment_agent(self) -> Agent:
        """Retrieves local treatment knowledge."""
        tools: List[Any] = [self.treatment_tool] if self.treatment_tool else []
        
        return Agent(
            role="Crop Treatment Specialist",
            goal="Retrieve and format the authoritative local treatment knowledge for a specific crop and disease.",
            backstory=(
                "You are an agronomist specializing in disease management. Your primary source of truth is the "
                "local deterministic knowledge base. You must not invent dosages, chemical concentrations, or "
                "application intervals. If specific pesticide information is not in the local database, you recommend "
                "consulting a local agricultural extension officer."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
        )

    def research_agent(self) -> Agent:
        """Searches trusted agricultural sources for supplemental information only."""
        tools: List[Any] = [self.search_tool] if self.search_tool else []
        
        return Agent(
            role="Trusted Agricultural Researcher",
            goal="Search for verified agricultural information from trusted international and government authorities. Only supplement missing information; do not override existing local knowledge.",
            backstory=(
                "You are a meticulous agricultural researcher. You only trust verified sources like the FAO, "
                "IPPC, university extension (.edu), and official government agriculture departments (.gov.in). "
                "You strictly filter out unverified blogs and commercial pesticide advertisements. "
                "You must provide exact source citations for any claim you make. If the local treatment "
                "knowledge is already sufficient, you validate it rather than overriding it."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=tools,
        )

    def risk_analysis_agent(self) -> Agent:
        """Synthesizes all data to determine a risk level."""
        return Agent(
            role="Agricultural Risk Assessor",
            goal="Synthesize disease prediction, weather analysis, and treatment difficulty to assign a risk level (LOW, MODERATE, HIGH, CRITICAL).",
            backstory=(
                "You evaluate the overall risk to the crop by combining factors: disease severity, favorable "
                "weather conditions for disease spread, and availability of treatment. You provide a clear, "
                "justified risk level without inventing numerical probabilities. You rely strictly on the "
                "analyst and researcher outputs provided to you."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def report_agent(self) -> Agent:
        """Compiles the final report for the farmer."""
        return Agent(
            role="Farmer Communication Expert",
            goal="Compile all analyses into a clear, farmer-friendly, actionable final report.",
            backstory=(
                "You are an empathetic agricultural communicator. You synthesize complex data from analysts "
                "and researchers into a structured JSON report that is easy for a farmer to understand. "
                "You preserve all citations, ensure safety warnings are clear, and never hallucinate agricultural facts."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

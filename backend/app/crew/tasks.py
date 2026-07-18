import logging
from typing import Any

from crewai import Task
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgriForgeTasks:
    def __init__(self, agents: Any):
        self.agents = agents

    def weather_analysis_task(self, weather_data_json: str) -> Task:
        return Task(
            description=(
                "Analyze the provided weather data for the crop and disease. "
                "Data: {weather_data_json}\n"
                "Explain the impact of these specific conditions on the disease's progression. "
                "Do not hallucinate weather data. Use strictly what is provided."
            ),
            expected_output="A structured summary of the weather conditions and their specific impact on the crop/disease.",
            agent=self.agents.weather_analysis_agent(),
        )

    def treatment_task(self, treatment_data_json: str) -> Task:
        return Task(
            description=(
                "Format the provided local treatment data into actionable advice. "
                "Data: {treatment_data_json}\n"
                "If the data says treatment was not found or is insufficient, explicitly state that. "
                "Do not invent dosages or chemicals not present in the data."
            ),
            expected_output="A clear list of immediate actions and preventive measures based STRICTLY on the provided data.",
            agent=self.agents.treatment_agent(),
        )

    def research_task(self, crop: str, disease: str) -> Task:
        return Task(
            description=(
                f"The local knowledge base had insufficient information for treating '{disease}' on '{crop}'. "
                f"Use the TrustedAgricultureSearchTool to search for verified treatment and management "
                f"practices for {crop} {disease}. Provide citations for every claim. "
                f"If the tool fails or returns nothing, state 'No trusted external sources found'."
            ),
            expected_output=(
                "A detailed, properly cited research summary on managing the disease. "
                "Must include 'Sources' with organization, title, and URL."
            ),
            agent=self.agents.research_agent(),
        )

    def risk_analysis_task(self) -> Task:
        return Task(
            description=(
                "Synthesize the disease prediction (including confidence), the weather analysis, "
                "and the available treatment/research to assess the current risk to the farm."
            ),
            expected_output=(
                "A risk assessment containing a level (LOW, MODERATE, HIGH, CRITICAL) "
                "and a list of reasons justifying that level."
            ),
            agent=self.agents.risk_analysis_agent(),
        )

    def report_task(self) -> Task:
        return Task(
            description=(
                "Compile all previous analyses into the final structured farmer report. "
                "Ensure that if the disease is 'healthy', the risk and treatment reflect that. "
                "Make sure to output the final result strictly matching the AIReport JSON schema."
            ),
            expected_output=(
                "A JSON object matching the AIReport schema containing crop, disease, weather, "
                "risk, treatment, maintenance, if_untreated, additional_research, farmer_summary, and sources."
            ),
            agent=self.agents.report_agent(),
        )

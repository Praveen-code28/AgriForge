from typing import List, Literal
from pydantic import BaseModel, Field


class AIReportDisease(BaseModel):
    name: str = Field(..., description="The name of the detected disease.")
    confidence: float = Field(..., description="The confidence score of the disease prediction, from 0.0 to 1.0.")


class AIReportWeather(BaseModel):
    summary: str = Field(..., description="A brief summary of current weather conditions.")
    impact: str = Field(..., description="Explanation of how the weather impacts the disease progression.")


class AIReportRisk(BaseModel):
    # Enforce strict validation to prevent LLM hallucinations of arbitrary risk levels
    level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL", "UNKNOWN"] = Field(
        ..., description="The assessed risk level to the crop."
    )
    reasons: List[str] = Field(..., description="A list of reasons justifying the assigned risk level.")


class AIReportTreatment(BaseModel):
    immediate_actions: List[str] = Field(..., description="Immediate actions the farmer should take.")
    preventive_measures: List[str] = Field(..., description="Preventive measures for future seasons.")


class AIReportSource(BaseModel):
    organization: str = Field(..., description="The organization publishing the source (e.g., FAO, ICAR).")
    title: str = Field(..., description="The title of the article or document.")
    url: str = Field(..., description="The exact URL of the source.")
    retrieved_at: str = Field(..., description="ISO timestamp of when the information was retrieved.")


class AIReport(BaseModel):
    crop: str = Field(..., description="The name of the crop being analyzed.")
    disease: AIReportDisease = Field(..., description="Details of the disease prediction.")
    weather: AIReportWeather = Field(..., description="Weather analysis and impact.")
    risk: AIReportRisk = Field(..., description="Risk assessment level and reasons.")
    treatment: AIReportTreatment = Field(..., description="Treatment and prevention plan.")
    maintenance: List[str] = Field(default_factory=list, description="General maintenance tasks for the crop.")
    if_untreated: str = Field(..., description="What happens if the disease is left untreated.")
    additional_research: List[str] = Field(default_factory=list, description="Additional researched information on the disease.")
    farmer_summary: str = Field(..., description="A highly readable, actionable summary for the farmer.")
    sources: List[AIReportSource] = Field(default_factory=list, description="Citations from trusted agricultural sources.")

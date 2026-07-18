import json
import pytest
from unittest.mock import MagicMock, patch

from backend.app.agents.agriforge_agents import AgriForgeAgents
from backend.app.crew.agriforge_crew import AgriForgeCrew
from backend.app.tools.trusted_search_tool import TrustedAgricultureSearchTool
from backend.app.schemas.ai_report import AIReport


@pytest.fixture
def mock_agents():
    # We don't need real services for testing the orchestration routing
    agents = AgriForgeAgents(
        disease_service=MagicMock(),
        weather_service=MagicMock(),
        treatment_service=MagicMock(),
    )
    # CrewAI Pydantic validation requires a string or a valid LLM object
    agents.llm = "gpt-4o"
    return agents


@pytest.fixture
def crew(mock_agents):
    return AgriForgeCrew(mock_agents)


def test_trusted_search_domain_filtering():
    tool = TrustedAgricultureSearchTool()
    
    assert tool._is_trusted_domain("https://fao.org/some/path") is True
    assert tool._is_trusted_domain("http://www.fao.org") is True
    assert tool._is_trusted_domain("https://ippc.int") is True
    assert tool._is_trusted_domain("https://icar.gov.in/research") is True
    
    assert tool._is_trusted_domain("https://agri.gov.in") is True
    assert tool._is_trusted_domain("https://state.nic.in") is True
    assert tool._is_trusted_domain("https://university.edu/extension") is True
    
    assert tool._is_trusted_domain("https://evil-fao.org") is False
    assert tool._is_trusted_domain("https://fakeedu.com") is False
    assert tool._is_trusted_domain("https://blog.com") is False


@patch("backend.app.crew.agriforge_crew.Crew")
def test_crew_routing_local_knowledge_sufficient(mock_crew_class, crew):
    # Setup mock crew kickoff return
    mock_crew_instance = mock_crew_class.return_value
    mock_crew_instance.kickoff.return_value = '```json\n{"crop": "tomato", "disease": "blight", "weather": {}, "risk": {}, "treatment": {}, "maintenance": [], "if_untreated": "", "farmer_summary": "", "sources": []}\n```'

    disease_result = {"primary": {"plant": "tomato", "disease": "blight", "confidence": 0.99}}
    weather_result = {}
    treatment_result = {"found": True, "treatment": "Copper fungicide"}
    
    result = crew.run(disease_result, weather_result, treatment_result)
    
    # Verify research task is NOT included
    # The tasks_list should have weather, treatment, risk, report (4 tasks)
    called_tasks = mock_crew_class.call_args[1]["tasks"]
    assert len(called_tasks) == 4
    task_descriptions = [t.description for t in called_tasks]
    assert not any("TrustedAgricultureSearchTool" in desc for desc in task_descriptions)
    
    assert "crop" in result


@patch("backend.app.crew.agriforge_crew.Crew")
def test_crew_routing_research_fallback(mock_crew_class, crew):
    # Setup mock crew kickoff return
    mock_crew_instance = mock_crew_class.return_value
    mock_crew_instance.kickoff.return_value = '{"crop": "potato", "disease": "blight", "weather": {}, "risk": {}, "treatment": {}, "maintenance": [], "if_untreated": "", "farmer_summary": "", "sources": []}'

    disease_result = {"primary": {"plant": "potato", "disease": "blight", "confidence": 0.95}}
    weather_result = {}
    treatment_result = {"found": False, "message": "No local knowledge"}
    
    result = crew.run(disease_result, weather_result, treatment_result)
    
    # Verify research task IS included
    # The tasks_list should have weather, treatment, research, risk, report (5 tasks)
    called_tasks = mock_crew_class.call_args[1]["tasks"]
    assert len(called_tasks) == 5
    task_descriptions = [t.description for t in called_tasks]
    assert any("TrustedAgricultureSearchTool" in desc for desc in task_descriptions)


@patch("backend.app.crew.agriforge_crew.Crew")
def test_crew_routing_healthy_crop(mock_crew_class, crew):
    mock_crew_instance = mock_crew_class.return_value
    mock_crew_instance.kickoff.return_value = "{}"

    disease_result = {"primary": {"plant": "tomato", "disease": "healthy", "confidence": 0.99}}
    weather_result = {}
    # Even if treatment_result says found=False, we don't research for 'healthy'
    treatment_result = {"found": False}
    
    crew.run(disease_result, weather_result, treatment_result)
    
    called_tasks = mock_crew_class.call_args[1]["tasks"]
    assert len(called_tasks) == 4  # Research task skipped because disease == 'healthy'

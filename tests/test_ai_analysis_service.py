import asyncio
import json

from backend.app.crew.agriforge_crew import AgriForgeCrew


class FakeLLM:
    """Minimal stand-in for the crewai LLM used in report synthesis."""

    def call(self, messages):
        return json.dumps(
            {
                "weather_summary": "clear",
                "weather_impact": "mild",
                "immediate_actions": ["inspect leaves"],
                "preventive_measures": ["water early"],
                "maintenance": [],
                "if_untreated": "risk rises",
                "farmer_summary": "test summary",
            }
        )


def test_agriforge_crew_single_llm_synthesis():
    agents = type("A", (), {"llm": FakeLLM(), "search_tool": None})()
    crew = AgriForgeCrew(agents)

    result = asyncio.run(
        crew.run_async(
            disease_result={"primary": {"plant": "tomato", "disease": "late_blight", "confidence": 0.91}},
            weather_result={"weather_analysis": {"risk_score": 80}},
            treatment_result={"found": True, "farmer_advice": "Keep leaves dry", "treatment": {"immediate_actions": ["x"]}},
        )
    )

    assert result["crop"] == "tomato"
    assert result["disease"]["name"] == "late_blight"
    # Core value (risk) stays deterministic, not invented by the LLM.
    assert result["risk"]["level"] == "HIGH"
    assert crew.last_report_source == "llm"


def test_agriforge_crew_deterministic_fallback_on_llm_failure():
    class BrokenLLM:
        def call(self, messages):
            raise RuntimeError("401 authentication failed")

    agents = type("A", (), {"llm": BrokenLLM(), "search_tool": None})()
    crew = AgriForgeCrew(agents)

    result = asyncio.run(
        crew.run_async(
            disease_result={"primary": {"plant": "tomato", "disease": "late_blight", "confidence": 0.91}},
            weather_result={"weather_analysis": {"risk_score": 80}},
            treatment_result={"found": True, "treatment": {"immediate_actions": ["Remove infected leaves"]}},
        )
    )

    assert crew.last_report_source == "deterministic_fallback"
    assert result["risk"]["level"] != "UNKNOWN"
    assert result["treatment"]["immediate_actions"]

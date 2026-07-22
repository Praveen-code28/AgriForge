import asyncio
import json

from backend.app.crew.agriforge_crew import AgriForgeCrew
from backend.app.services import report_synthesis
from backend.app.tools.trusted_search_tool import TrustedAgricultureSearchTool


# ---------------------------------------------------------------------------
# Trusted search domain filtering (unchanged behaviour)
# ---------------------------------------------------------------------------
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


def test_ssrf_blocks_private_hosts(monkeypatch):
    tool = TrustedAgricultureSearchTool()
    # localhost / private ranges must never be fetched even if scheme is fine.
    assert tool._is_public_host("localhost") in (False,)
    # A trusted-looking domain that resolves to a private IP is rejected.
    monkeypatch.setattr(
        "backend.app.tools.trusted_search_tool.socket.getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 0))],
    )
    assert tool._safe_url("https://icar.gov.in/x") is False


# ---------------------------------------------------------------------------
# Deterministic risk + report (no LLM required, never UNKNOWN)
# ---------------------------------------------------------------------------
def test_compute_risk_healthy_is_low():
    level, reasons = report_synthesis.compute_risk("healthy", True, {})
    assert level == "LOW"
    assert reasons


def test_compute_risk_disease_high_weather():
    weather = {"weather_analysis": {"risk_score": 80}}
    level, _ = report_synthesis.compute_risk("late_blight", True, weather)
    assert level == "HIGH"


def test_compute_risk_no_treatment_escalates_to_critical():
    weather = {"weather_analysis": {"risk_score": 85}}
    level, _ = report_synthesis.compute_risk("late_blight", False, weather)
    assert level == "CRITICAL"


def test_deterministic_report_is_useful():
    disease_result = {"primary": {"plant": "tomato", "disease": "early_blight", "confidence": 0.91}}
    weather_result = {
        "weather_analysis": {"risk": "High", "risk_score": 75, "reasons": ["humid"]},
        "current_weather": {"temperature": 27, "humidity": 85, "condition": "Cloudy"},
        "spray_recommendation": {"spray_today": False, "best_time": "06:00 AM"},
    }
    treatment_result = {
        "found": True,
        "disease_name": "Early Blight",
        "treatment": {"immediate_actions": ["Remove infected leaves"]},
        "prevention": ["Rotate crops"],
        "farmer_advice": "Inspect lower leaves.",
    }
    report = report_synthesis.build_deterministic_report(disease_result, weather_result, treatment_result)

    assert report["crop"] == "tomato"
    assert report["disease"]["name"] == "early_blight"
    assert report["risk"]["level"] != "UNKNOWN"
    assert report["treatment"]["immediate_actions"]
    assert report["farmer_summary"]


# ---------------------------------------------------------------------------
# Orchestration: single-call synthesis + research routing
# ---------------------------------------------------------------------------
class FakeLLM:
    def __init__(self):
        self.calls = 0

    def call(self, messages):
        self.calls += 1
        return json.dumps(
            {
                "weather_summary": "Warm and humid.",
                "weather_impact": "Favours blight.",
                "immediate_actions": ["Remove infected leaves"],
                "preventive_measures": ["Rotate crops"],
                "maintenance": ["Scout weekly"],
                "if_untreated": "Spread will worsen.",
                "farmer_summary": "Act now to protect your tomato.",
            }
        )


def test_generate_report_uses_single_llm_call():
    llm = FakeLLM()
    disease_result = {"primary": {"plant": "tomato", "disease": "early_blight", "confidence": 0.91}}
    treatment_result = {"found": True, "treatment": {"immediate_actions": ["x"]}, "prevention": ["y"]}
    report, source, timings = asyncio.run(
        report_synthesis.generate_report(disease_result, {}, treatment_result, llm=llm)
    )
    assert llm.calls == 1
    assert source == "llm"
    assert report["farmer_summary"] == "Act now to protect your tomato."
    assert "llm" in timings


def test_generate_report_falls_back_without_llm():
    disease_result = {"primary": {"plant": "tomato", "disease": "early_blight", "confidence": 0.91}}
    treatment_result = {"found": True, "treatment": {"immediate_actions": ["x"]}}
    report, source, _ = asyncio.run(
        report_synthesis.generate_report(disease_result, {}, treatment_result, llm=None)
    )
    assert source == "deterministic_fallback"
    assert report["risk"]["level"] != "UNKNOWN"


def test_research_only_when_needed():
    calls = []

    def search_fn(query):
        calls.append(query)
        return [{"title": "FAO guide", "url": "https://fao.org/x", "snippet": "..."}]

    # healthy -> no research
    asyncio.run(
        report_synthesis.generate_report(
            {"primary": {"plant": "tomato", "disease": "healthy", "confidence": 0.99}},
            {},
            {"found": False},
            llm=None,
            search_fn=search_fn,
        )
    )
    assert calls == []

    # disease present + local knowledge found -> no research
    asyncio.run(
        report_synthesis.generate_report(
            {"primary": {"plant": "tomato", "disease": "late_blight", "confidence": 0.95}},
            {},
            {"found": True, "treatment": {"immediate_actions": ["x"]}},
            llm=None,
            search_fn=search_fn,
        )
    )
    assert calls == []

    # disease present + no local knowledge -> research runs
    asyncio.run(
        report_synthesis.generate_report(
            {"primary": {"plant": "tomato", "disease": "late_blight", "confidence": 0.95}},
            {},
            {"found": False},
            llm=None,
            search_fn=search_fn,
        )
    )
    assert len(calls) == 1


def test_crew_wrapper_delegates():
    llm = FakeLLM()
    agents = type("A", (), {"llm": llm, "search_tool": None})()
    crew = AgriForgeCrew(agents)
    result = crew.run(
        {"primary": {"plant": "tomato", "disease": "early_blight", "confidence": 0.9}},
        {},
        {"found": True, "treatment": {"immediate_actions": ["x"]}, "prevention": ["y"]},
    )
    assert result["crop"] == "tomato"
    assert crew.last_report_source == "llm"

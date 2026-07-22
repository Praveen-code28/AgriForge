import asyncio
from types import SimpleNamespace

from backend.app.crew.agriforge_crew import AgriForgeCrew


class DummyTask:
    def __init__(self):
        self.agent = object()
        self.output_pydantic = None


class DummyTasksFactory:
    def __init__(self, agents):
        self.agents = agents

    def weather_analysis_task(self, weather_data_json):
        return DummyTask()

    def treatment_task(self, treatment_data_json):
        return DummyTask()

    def research_task(self, crop, disease):
        return DummyTask()

    def risk_analysis_task(self):
        return DummyTask()

    def report_task(self):
        return DummyTask()


class DummyCrew:
    def __init__(self, agents, tasks, process, verbose):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.kickoff_async_calls = 0

    async def kickoff_async(self, inputs=None, input_files=None, from_checkpoint=None):
        self.kickoff_async_calls += 1
        self.inputs = inputs
        return '{"crop": "tomato", "disease": {"name": "late_blight", "confidence": 0.91}, "weather": {"summary": "clear", "impact": "mild"}, "risk": {"level": "MODERATE", "reasons": ["test"]}, "treatment": {"immediate_actions": ["inspect leaves"], "preventive_measures": ["water early"]}, "maintenance": [], "if_untreated": "risk rises", "additional_research": [], "farmer_summary": "test summary", "sources": []}'


def test_agriforge_crew_uses_async_kickoff(monkeypatch):
    import backend.app.crew.agriforge_crew as crew_module

    monkeypatch.setattr(crew_module, "AgriForgeTasks", DummyTasksFactory)

    def fake_crew_factory(*args, **kwargs):
        return DummyCrew(*args, **kwargs)

    monkeypatch.setattr(crew_module, "Crew", fake_crew_factory)

    crew = AgriForgeCrew(agents=object())
    result = asyncio.run(
        crew.run_async(
            disease_result={"primary": {"plant": "tomato", "disease": "late_blight", "confidence": 0.91}},
            weather_result={"summary": "test"},
            treatment_result={"found": True, "farmer_advice": "Keep leaves dry"},
        )
    )

    assert result["crop"] == "tomato"
    assert result["disease"]["name"] == "late_blight"

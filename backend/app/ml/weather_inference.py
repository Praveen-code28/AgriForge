from typing import Any

from ml.weather.orchestrator import WeatherIntelligence


class WeatherInferenceService:
    """Wrap rule-based WeatherIntelligence module."""

    _instance: "WeatherInferenceService | None" = None

    def __init__(self, knowledge_base_path: str, api_key: str | None = None):
        self.engine = WeatherIntelligence(knowledge_base_path=knowledge_base_path, api_key=api_key)

    @classmethod
    def get_instance(cls, knowledge_base_path: str, api_key: str | None = None) -> "WeatherInferenceService":
        if cls._instance is None:
            cls._instance = cls(knowledge_base_path, api_key)
        return cls._instance

    def analyze(
        self,
        crop: str,
        disease: str,
        confidence: float,
        lat: float | None = None,
        lon: float | None = None,
        address: str | None = None,
    ) -> dict[str, Any]:
        return self.engine.process(
            crop=crop.lower(),
            disease=disease.lower(),
            confidence=confidence,
            lat=lat,
            lon=lon,
            address=address,
        )

    def analyze_healthy_summary(self, crop: str, lat: float | None, lon: float | None) -> dict[str, Any]:
        """Simplified weather context for healthy plants."""
        if lat is None or lon is None:
            return {
                "skipped": True,
                "reason": "No location provided; weather analysis optional for healthy plants.",
            }
        result = self.analyze(crop=crop, disease="healthy", confidence=1.0, lat=lat, lon=lon)
        return {"skipped": False, "summary": result}

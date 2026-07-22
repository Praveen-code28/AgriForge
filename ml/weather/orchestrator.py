import json
import os
from typing import Any, Dict, Optional

from .analysis.bonus.confidence_validator import ConfidenceValidator
from .analysis.bonus.recovery_probability import RecoveryProbability
from .analysis.bonus.treatment_window import TreatmentWindowScorer
from .analysis.disease_weather import DiseaseWeatherAnalyzer
from .analysis.emergency import EmergencyRecommender
from .analysis.progression import ProgressionPredictor
from .analysis.risk_score import RiskScoreCalculator
from .analysis.spray_timing import SprayTimingRecommender
from .analysis.weather_summary import generate_summary
from .current_weather import get_current_weather
from .forecast import aggregate_forecast_by_day, get_forecast
from .knowledge_adapter import adapt_knowledge, healthy_knowledge
from .location import LocationResolver
from .weather_client import OpenWeatherMapClient


class WeatherIntelligence:
    def __init__(self, knowledge_base_path: str = "ml/weather/knowledge", api_key: str | None = None):
        self.knowledge_base_path = knowledge_base_path
        self._api_key = api_key
        self.location_resolver = LocationResolver()
        self.weather_client: OpenWeatherMapClient | None = None
        self._knowledge_cache: Dict[str, Dict[str, Any]] = {}

    def _get_weather_client(self) -> OpenWeatherMapClient:
        api_key = self._api_key or os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OpenWeatherMap API key missing")
        if self.weather_client is None:
            self.weather_client = OpenWeatherMapClient(api_key=api_key)
        return self.weather_client

    def _load_knowledge(self, crop: str, disease: str) -> Dict[str, Any]:
        key = f"{crop}_{disease}"
        if key not in self._knowledge_cache:
            if disease == "healthy":
                self._knowledge_cache[key] = healthy_knowledge(crop)
            else:
                filepath = os.path.join(self.knowledge_base_path, crop, f"{disease}.json")
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Knowledge file not found: {filepath}")
                with open(filepath, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._knowledge_cache[key] = adapt_knowledge(raw)
        return self._knowledge_cache[key]

    def _build_unavailable_result(self, location: Optional[Any] = None, reason: str = "Weather analysis unavailable.") -> Dict[str, Any]:
        location_payload = {
            "lat": None,
            "lon": None,
            "district": None,
            "state": None,
            "country": None,
        }
        if location is not None:
            location_payload.update(
                {
                    "lat": getattr(location, "lat", None),
                    "lon": getattr(location, "lon", None),
                    "district": getattr(location, "district", None),
                    "state": getattr(location, "state", None),
                    "country": getattr(location, "country", None),
                }
            )
        return {
            "skipped": True,
            "reason": reason,
            "summary": "Weather analysis unavailable.",
            "location": location_payload,
        }

    def process(
        self,
        crop: str,
        disease: str,
        confidence: float,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            location = self.location_resolver.resolve(lat, lon, address)
        except Exception as exc:
            return self._build_unavailable_result(reason=f"Unable to resolve location: {exc}")

        try:
            client = self._get_weather_client()
            current = get_current_weather(client, location.lat, location.lon)
            forecast_periods = get_forecast(client, location.lat, location.lon, hours=48)
            if current is None or not forecast_periods:
                raise ValueError("Weather service returned no usable data")
        except Exception as exc:
            return self._build_unavailable_result(location, reason=f"Weather service unavailable: {exc}")

        try:
            forecast_agg = aggregate_forecast_by_day(forecast_periods)

            knowledge = self._load_knowledge(crop, disease)

            disease_analyzer = DiseaseWeatherAnalyzer(knowledge)
            weather_analysis = disease_analyzer.analyze(current, forecast_periods)

            spray_recommender = SprayTimingRecommender(knowledge)
            spray_rec = spray_recommender.recommend(forecast_periods)

            progression_predictor = ProgressionPredictor(knowledge)
            progression = progression_predictor.predict(weather_analysis["risk_score"])

            emergency_recommender = EmergencyRecommender(knowledge)
            emergency_rec = emergency_recommender.recommend(
                spray_rec["spray_today"], weather_analysis["risk_score"]
            )

            risk_calc = RiskScoreCalculator(knowledge)
            crop_health = risk_calc.calculate(
                confidence, weather_analysis["risk_score"], current, forecast_periods
            )

            validator = ConfidenceValidator(knowledge)
            validation = validator.validate(disease, current, forecast_periods)
            confidence_validation = validation if validation["inconsistent"] else None

            window_scorer = TreatmentWindowScorer(knowledge)
            treatment_window_score = window_scorer.score(forecast_periods)

            recovery = RecoveryProbability(knowledge)
            recovery_probability = recovery.estimate(
                confidence, weather_analysis["risk_score"], spray_rec["spray_today"]
            )

            summary = generate_summary(
                location,
                current,
                forecast_agg,
                weather_analysis,
                spray_rec,
                crop_health,
                emergency_rec,
                progression,
                confidence_validation=confidence_validation,
                treatment_window_score=treatment_window_score,
                recovery_probability=recovery_probability,
            )
            return summary
        except Exception as exc:
            return self._build_unavailable_result(location, reason=f"Weather analysis unavailable: {exc}")

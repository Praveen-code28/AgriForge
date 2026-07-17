import json
import os
from typing import Optional, Dict, Any
from .location import LocationResolver
from .weather_client import OpenWeatherMapClient
from .current_weather import get_current_weather
from .forecast import get_forecast, aggregate_forecast_by_day
from .analysis.disease_weather import DiseaseWeatherAnalyzer
from .analysis.spray_timing import SprayTimingRecommender
from .analysis.progression import ProgressionPredictor
from .analysis.emergency import EmergencyRecommender
from .analysis.risk_score import RiskScoreCalculator
from .analysis.weather_summary import generate_summary
# bonus imports
from .analysis.bonus.confidence_validator import ConfidenceValidator
from .analysis.bonus.treatment_window import TreatmentWindowScorer
from .analysis.bonus.recovery_probability import RecoveryProbability

class WeatherIntelligence:
    def __init__(self, knowledge_base_path: str = "ml/weather/knowledge"):
        self.knowledge_base_path = knowledge_base_path
        self.location_resolver = LocationResolver()
        self.weather_client = OpenWeatherMapClient()
        self._knowledge_cache = {}

    def _load_knowledge(self, crop: str, disease: str) -> Dict[str, Any]:
        key = f"{crop}_{disease}"
        if key not in self._knowledge_cache:
            filepath = os.path.join(self.knowledge_base_path, crop, f"{disease}.json")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Knowledge file not found: {filepath}")
            with open(filepath, "r") as f:
                self._knowledge_cache[key] = json.load(f)
        return self._knowledge_cache[key]

    def process(self,
                crop: str,
                disease: str,
                confidence: float,
                lat: Optional[float] = None,
                lon: Optional[float] = None,
                address: Optional[str] = None) -> Dict[str, Any]:
        # 1. Resolve location
        location = self.location_resolver.resolve(lat, lon, address)

        # 2. Get weather
        current = get_current_weather(self.weather_client, location.lat, location.lon)
        forecast_periods = get_forecast(self.weather_client, location.lat, location.lon, hours=48)
        forecast_agg = aggregate_forecast_by_day(forecast_periods)

        # 3. Load knowledge
        knowledge = self._load_knowledge(crop, disease)

        # 4. Disease weather analysis
        disease_analyzer = DiseaseWeatherAnalyzer(knowledge)
        weather_analysis = disease_analyzer.analyze(current, forecast_periods)

        # 5. Spray timing
        spray_recommender = SprayTimingRecommender(knowledge)
        spray_rec = spray_recommender.recommend(forecast_periods)

        # 6. Progression prediction
        progression_predictor = ProgressionPredictor(knowledge)
        progression = progression_predictor.predict(weather_analysis["risk_score"])

        # 7. Emergency recommendation
        emergency_recommender = EmergencyRecommender(knowledge)
        emergency_rec = emergency_recommender.recommend(spray_rec["spray_today"], weather_analysis["risk_score"])

        # 8. Risk score
        risk_calc = RiskScoreCalculator(knowledge)
        crop_health = risk_calc.calculate(confidence, weather_analysis["risk_score"], current, forecast_periods)

        # 9. Generate summary
        summary = generate_summary(location, current, forecast_agg, weather_analysis,
                                   spray_rec, crop_health, emergency_rec)

        # 10. Add progression
        summary["progression"] = progression

        # 11. Bonus features (if requested)
        # Confidence Validation
        validator = ConfidenceValidator(knowledge)
        validation = validator.validate(disease, current, forecast_periods)
        if validation["inconsistent"]:
            summary["confidence_validation"] = validation

        # Treatment Window Score
        window_scorer = TreatmentWindowScorer(knowledge)
        window_score = window_scorer.score(forecast_periods)
        summary["treatment_window_score"] = window_score

        # Recovery Probability
        recovery = RecoveryProbability(knowledge)
        recovery_prob = recovery.estimate(confidence, weather_analysis["risk_score"], spray_rec["spray_today"])
        summary["recovery_probability"] = recovery_prob

        return summary
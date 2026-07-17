from typing import Dict, Any, List
from ...current_weather import CurrentWeather
from ...forecast import ForecastPeriod

class ConfidenceValidator:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge

    def validate(self, disease: str, current: CurrentWeather, forecast: List[ForecastPeriod]) -> Dict:
        fav = self.knowledge["favorable_weather"]
        inconsistent = False
        reasons = []

        # Check if current weather does NOT match favorable conditions
        if not (fav["temperature_min"] <= current.temperature <= fav["temperature_max"]):
            inconsistent = True
            reasons.append("Current temperature is outside the favorable range for this disease.")
        if current.humidity < fav["humidity_min"]:
            inconsistent = True
            reasons.append("Current humidity is below the favorable threshold.")
        # Check forecast: if no favorable periods in next 48h, flag
        favorable_forecast = False
        for p in forecast:
            if (fav["temperature_min"] <= p.temperature <= fav["temperature_max"] and
                p.humidity >= fav["humidity_min"]):
                favorable_forecast = True
                break
        if not favorable_forecast:
            inconsistent = True
            reasons.append("No favorable weather conditions predicted in the next 48 hours.")

        return {
            "inconsistent": inconsistent,
            "reasons": reasons,
            "recommendation": "Consider capturing another image to verify disease identification." if inconsistent else None
        }
import json
from typing import Dict, Any, List
from ..current_weather import CurrentWeather
from ..forecast import ForecastPeriod

class DiseaseWeatherAnalyzer:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge

    def analyze(self, current: CurrentWeather, forecast_periods: List[ForecastPeriod]) -> Dict:
        # Determine if current weather favors disease
        fav = self.knowledge["favorable_weather"]
        unfavorable = self.knowledge.get("unfavorable_weather", {})
        risk_score = 0
        reasons = []

        # Check current conditions
        temp_ok = fav["temperature_min"] <= current.temperature <= fav["temperature_max"]
        hum_ok = current.humidity >= fav["humidity_min"]
        rain_ok = current.rainfall >= fav.get("rainfall_min", 0)
        if temp_ok and hum_ok and rain_ok:
            risk_score += 40
            reasons.append("Current temperature and humidity are within favorable range for disease.")
        else:
            # Check forecast for next 48h
            for p in forecast_periods:
                if (fav["temperature_min"] <= p.temperature <= fav["temperature_max"] and
                    p.humidity >= fav["humidity_min"]):
                    risk_score += 20  # each favorable forecast period adds risk
                    reasons.append(f"Forecast at {p.time.strftime('%H:%M')} shows favorable conditions.")
            if risk_score == 0:
                reasons.append("Current and forecast conditions are not favorable for disease spread.")
                risk_score = 10  # baseline

        # Apply penalties if unfavorable conditions exist
        if unfavorable:
            if current.temperature > unfavorable.get("temperature_above", 100):
                risk_score = max(0, risk_score - 30)
                reasons.append("Temperature is too high for disease development.")
            if current.humidity < unfavorable.get("humidity_below", 0):
                risk_score = max(0, risk_score - 30)
                reasons.append("Humidity is too low for disease development.")

        # Normalize risk score to 0-100
        risk_score = min(100, max(0, risk_score))
        # Determine risk category
        if risk_score >= 70:
            risk = "High"
        elif risk_score >= 40:
            risk = "Moderate"
        else:
            risk = "Low"

        return {
            "risk": risk,
            "risk_score": risk_score,
            "reasons": reasons[:3]  # limit to top reasons
        }
from typing import Any, Dict, List

from ..current_weather import CurrentWeather
from ..weather_client import ForecastPeriod


class RiskScoreCalculator:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge

    def calculate(self, disease_confidence: float, weather_risk_score: int,
                  current: CurrentWeather, forecast_periods: List[ForecastPeriod]) -> Dict:
        # Weighted combination
        weight_confidence = 0.3
        weight_weather = 0.4
        weight_forecast = 0.2
        weight_humidity = 0.1

        # Normalize confidence to 0-100
        conf_score = disease_confidence * 100

        # Forecast risk: average rain probability and temperature extremes
        forecast_risk = 0
        for p in forecast_periods[:16]:
            if p.rain_probability > 50:
                forecast_risk += 10
            if p.temperature > 30 or p.temperature < 10:
                forecast_risk += 5
        forecast_risk = min(100, forecast_risk)

        # Humidity impact
        hum_risk = min(100, current.humidity * 1.2)  # higher humidity => higher risk

        total = (weight_confidence * conf_score +
                 weight_weather * weather_risk_score +
                 weight_forecast * forecast_risk +
                 weight_humidity * hum_risk)
        risk_score = min(100, max(0, int(total)))

        if risk_score >= 80:
            category = "Very High"
        elif risk_score >= 60:
            category = "High"
        elif risk_score >= 40:
            category = "Moderate"
        elif risk_score >= 20:
            category = "Low"
        else:
            category = "Very Low"

        return {"score": risk_score, "category": category}
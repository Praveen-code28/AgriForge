from typing import List, Dict, Any
from ...weather_client import ForecastPeriod

class TreatmentWindowScorer:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge
        self.ideal = knowledge.get("treatment_window", {}).get("ideal_conditions", {})

    def score(self, forecast_periods: List[ForecastPeriod]) -> Dict:
        # Compute a score for each 3-hour window and return the best score and time.
        best_score = 0
        best_time = None
        for p in forecast_periods[:16]:
            score = 0
            temp_ok = self.ideal.get("temperature", [0, 100])
            if temp_ok[0] <= p.temperature <= temp_ok[1]:
                score += 25
            hum_ok = self.ideal.get("humidity", [0, 100])
            if hum_ok[0] <= p.humidity <= hum_ok[1]:
                score += 25
            if p.wind_speed < 10:  # from ideal wind "<10" maybe in km/h
                score += 25
            if p.rain_probability < 30:
                score += 25
            if score > best_score:
                best_score = score
                best_time = p.time
        return {
            "best_window_score": best_score,
            "best_window_time": best_time.strftime("%Y-%m-%d %H:%M") if best_time else "None",
            "suitability": "High" if best_score >= 80 else "Moderate" if best_score >= 50 else "Low"
        }
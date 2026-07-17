from typing import List, Dict, Any
from ..forecast import ForecastPeriod
from datetime import datetime, timedelta

class SprayTimingRecommender:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge
        self.spray_rules = knowledge["spray_rules"]

    def recommend(self, forecast_periods: List[ForecastPeriod]) -> Dict:
        # Determine if spraying today is feasible based on current conditions (we assume current is known)
        # For simplicity, we'll use the first forecast period as "current" if we don't have separate current.
        # We'll evaluate each forecast period for suitability.
        best_period = None
        best_score = -1
        spray_today = False
        reasons = []

        for p in forecast_periods[:16]:  # next 48h (approx 16 periods of 3h)
            score = 0
            # Temperature
            if self.spray_rules["min_temperature"] <= p.temperature <= self.spray_rules["max_temperature"]:
                score += 20
            else:
                continue
            # Wind
            if p.wind_speed <= self.spray_rules["max_wind_speed"]:
                score += 20
            else:
                continue
            # Humidity
            if self.spray_rules["optimal_humidity_range"][0] <= p.humidity <= self.spray_rules["optimal_humidity_range"][1]:
                score += 20
            # Rain probability
            if p.rain_probability < 30:
                score += 20
            # Time of day: prefer early morning or late evening
            hour = p.time.hour
            if 5 <= hour <= 8 or 17 <= hour <= 20:
                score += 20

            if score > best_score:
                best_score = score
                best_period = p

        if best_period:
            # Determine if today
            today_date = datetime.now().date()
            if best_period.time.date() == today_date:
                spray_today = True
                reasons.append("Best spray time is today within the recommended window.")
            else:
                spray_today = False
                reasons.append(f"Best spray time is {best_period.time.strftime('%A, %B %d')}.")
            # Construct best day/time string
            best_day = "Today" if spray_today else best_period.time.strftime("%A")
            best_time = f"{best_period.time.strftime('%I:%M %p')}"
        else:
            # No suitable period found
            spray_today = False
            best_day = "None"
            best_time = "None"
            reasons.append("No suitable spray time found in the next 48 hours due to adverse weather conditions.")

        return {
            "spray_today": spray_today,
            "best_day": best_day,
            "best_time": best_time,
            "reason": reasons[:3]
        }
from typing import Any, Dict


class RecoveryProbability:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge

    def estimate(self, confidence: float, weather_risk: int, spray_today: bool) -> Dict:
        base = 70
        if confidence > 0.9:
            base += 10
        elif confidence > 0.7:
            base += 5
        if weather_risk < 30:
            base += 10
        elif weather_risk > 70:
            base -= 20
        if spray_today:
            base += 15
        else:
            base -= 10
        prob = max(0, min(100, base))
        category = "High" if prob >= 70 else "Moderate" if prob >= 40 else "Low"
        return {"recovery_probability": prob, "category": category}

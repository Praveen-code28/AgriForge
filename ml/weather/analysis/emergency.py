from typing import Dict, Any

class EmergencyRecommender:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge
        self.prevention = knowledge.get("prevention", {})

    def recommend(self, spray_today: bool, risk_score: int) -> Dict:
        # If spraying today is not allowed but risk is high, suggest temporary measures.
        can_spray = spray_today
        if not spray_today and risk_score >= 60:
            can_spray = True  # emergency override? But we still provide solution.
            # Suggest using sticker/spreader, etc.
            solution = "Use a sticker/spreader adjuvant to improve rainfastness. Consider increasing spray interval if rain is expected."
            effectiveness = "60%"
        elif not spray_today:
            solution = "Monitor weather; apply as soon as conditions improve."
            effectiveness = "80% (if delayed < 48h)"
        else:
            solution = "Proceed with scheduled spraying as conditions are favorable."
            effectiveness = "95%"
        return {
            "can_spray": can_spray,
            "temporary_solution": solution,
            "expected_effectiveness": effectiveness
        }
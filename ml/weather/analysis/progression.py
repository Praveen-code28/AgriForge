class ProgressionPredictor:
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge
        self.spread_rules = knowledge.get("disease_spread", {})

    def predict(self, risk_score: int) -> Dict:
        # Simple model: if risk high, progression faster.
        # We'll produce a timeline.
        if risk_score >= 70:
            day2 = "Disease spreads significantly; lesions visible on new growth."
            day5 = "Yield loss risk becomes severe; consider immediate action."
            loss_risk = "High"
        elif risk_score >= 40:
            day2 = "Moderate spread; early lesions may appear."
            day5 = "Yield loss moderate; timely treatment recommended."
            loss_risk = "Moderate"
        else:
            day2 = "Minimal spread; disease remains contained."
            day5 = "Low yield loss risk; monitor conditions."
            loss_risk = "Low"
        return {
            "today": "Current infection level is based on disease prediction.",
            "day2": day2,
            "day5": day5,
            "yield_loss_risk": loss_risk
        }
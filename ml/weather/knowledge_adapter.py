"""Adapt teammate JSON knowledge schema to analyzer-expected keys."""

from typing import Any, Dict


def _parse_humidity_min(humidity_value: Any) -> int:
    if isinstance(humidity_value, (int, float)):
        return int(humidity_value)
    text = str(humidity_value).lower()
    if "high" in text:
        return 70
    if "moderate" in text:
        return 50
    if "low" in text:
        return 30
    return 50


def adapt_knowledge(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map new JSON schema to keys expected by weather analyzers."""
    adapted = dict(raw)
    favorable = raw.get("favorable_conditions", {})
    temp = favorable.get("temperature_celsius", {})

    adapted["favorable_weather"] = {
        "temperature_min": temp.get("min", 15),
        "temperature_max": temp.get("max", 35),
        "humidity_min": _parse_humidity_min(favorable.get("humidity", 50)),
        "rainfall_min": 0,
    }
    adapted["unfavorable_weather"] = {
        "temperature_above": temp.get("max", 35) + 5,
        "humidity_below": max(20, _parse_humidity_min(favorable.get("humidity", 50)) - 20),
    }
    adapted["spray_rules"] = {
        "min_temperature": max(10, temp.get("min", 15) - 5),
        "max_temperature": min(40, temp.get("max", 35) + 5),
        "max_wind_speed": 20,
        "optimal_humidity_range": [
            max(30, _parse_humidity_min(favorable.get("humidity", 50)) - 15),
            min(95, _parse_humidity_min(favorable.get("humidity", 50)) + 15),
        ],
    }
    adapted["treatment_window"] = {
        "ideal_conditions": {
            "temperature": [
                temp.get("min", 15),
                temp.get("max", 35),
            ],
            "humidity": [
                max(30, _parse_humidity_min(favorable.get("humidity", 50)) - 10),
                min(90, _parse_humidity_min(favorable.get("humidity", 50)) + 10),
            ],
        }
    }
    return adapted


def healthy_knowledge(crop: str) -> Dict[str, Any]:
    """Minimal knowledge for healthy plants (no disease-specific weather rules)."""
    return adapt_knowledge(
        {
            "disease_id": f"{crop}_healthy",
            "crop": crop.title(),
            "disease_name": "Healthy",
            "favorable_conditions": {
                "temperature_celsius": {"min": 15, "max": 32},
                "humidity": "Moderate",
            },
            "prevention": ["Maintain regular watering and nutrition", "Monitor for early symptoms"],
            "treatment": {
                "immediate_actions": ["No treatment required"],
                "cultural_control": ["Continue good agronomic practices"],
            },
        }
    )

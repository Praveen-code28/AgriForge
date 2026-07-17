# ml/weather/analysis/weather_summary.py

from typing import Dict, Any, Optional
from ..location import Location
from ..current_weather import CurrentWeather

def generate_summary(
    location: Location,
    current: CurrentWeather,
    forecast_agg: Dict[str, Any],
    weather_analysis: Dict[str, Any],
    spray_rec: Dict[str, Any],
    crop_health_score: Dict[str, Any],
    emergency_rec: Dict[str, Any],
    progression: Dict[str, Any],
    confidence_validation: Optional[Dict[str, Any]] = None,
    treatment_window_score: Optional[Dict[str, Any]] = None,
    recovery_probability: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble all intelligence into final JSON for CrewAI."""
    summary = {
        "location": {
            "district": location.district,
            "state": location.state,
            "lat": location.lat,
            "lon": location.lon
        },
        "current_weather": {
            "temperature": current.temperature,
            "humidity": current.humidity,
            "rainfall": current.rainfall,
            "rain_probability": current.rain_probability,
            "wind_speed": current.wind_speed,
            "pressure": current.pressure,
            "cloud_cover": current.cloud_cover,
            "condition": current.condition,
            "uv_index": current.uv_index
        },
        "forecast": forecast_agg,
        "weather_analysis": weather_analysis,
        "spray_recommendation": spray_rec,
        "emergency_recommendation": emergency_rec,
        "crop_health_score": crop_health_score,
        "progression": progression
    }
    # Optional bonuses
    if confidence_validation:
        summary["confidence_validation"] = confidence_validation
    if treatment_window_score:
        summary["treatment_window_score"] = treatment_window_score
    if recovery_probability:
        summary["recovery_probability"] = recovery_probability
    return summary
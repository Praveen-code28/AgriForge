# ml/weather/utils/__init__.py

from .exceptions import (
    WeatherIntelligenceError,
    WeatherAPIFailure,
    KnowledgeNotFoundError,
    LocationResolutionError,
    InvalidWeatherDataError,
    ConfigurationError,
)

from .helpers import (
    safe_avg,
    safe_clamp,
    format_datetime,
    celsius_to_fahrenheit,
    mm_to_inches,
    kmh_to_ms,
    safe_round,
    deep_merge,
    to_json_safe,
)

__all__ = [
    # Exceptions
    "WeatherIntelligenceError",
    "WeatherAPIFailure",
    "KnowledgeNotFoundError",
    "LocationResolutionError",
    "InvalidWeatherDataError",
    "ConfigurationError",
    # Helpers
    "safe_avg",
    "safe_clamp",
    "format_datetime",
    "celsius_to_fahrenheit",
    "mm_to_inches",
    "kmh_to_ms",
    "safe_round",
    "deep_merge",
    "to_json_safe",
]
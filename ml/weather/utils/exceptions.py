# ml/weather/utils/exceptions.py

class WeatherIntelligenceError(Exception):
    """Base exception for the Weather Intelligence Module."""
    pass


class WeatherAPIFailure(WeatherIntelligenceError):
    """Raised when the external weather API fails (network, auth, invalid response)."""
    pass


class KnowledgeNotFoundError(WeatherIntelligenceError):
    """Raised when the knowledge JSON file for a specific crop/disease is missing."""
    pass


class LocationResolutionError(WeatherIntelligenceError):
    """Raised when GPS or address cannot be geocoded to a valid location."""
    pass


class InvalidWeatherDataError(WeatherIntelligenceError):
    """Raised when weather data is malformed, null, or outside realistic ranges."""
    pass


class ConfigurationError(WeatherIntelligenceError):
    """Raised when required environment variables or configs are missing."""
    pass
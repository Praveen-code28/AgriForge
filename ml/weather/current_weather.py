from .weather_client import WeatherClient, CurrentWeather


def get_current_weather(client: WeatherClient, lat: float, lon: float) -> CurrentWeather:
    return client.get_current(lat, lon)

from collections import defaultdict
from typing import List

from .weather_client import ForecastPeriod, WeatherClient


def get_forecast(client: WeatherClient, lat: float, lon: float, hours: int = 48) -> List[ForecastPeriod]:
    return client.get_forecast(lat, lon, hours)


def aggregate_forecast_by_day(periods: List[ForecastPeriod]) -> dict:
    """Group forecast periods into day1/day2 aggregates."""
    days = defaultdict(list)
    for period in periods:
        day_key = period.time.strftime("%Y-%m-%d")
        days[day_key].append(period)

    result = {}
    for i, (_, periods_list) in enumerate(sorted(days.items())[:2], 1):
        temps = [p.temperature for p in periods_list]
        hums = [p.humidity for p in periods_list]
        rain_probs = [p.rain_probability for p in periods_list]
        wind = [p.wind_speed for p in periods_list]
        cloud = [p.cloud_cover for p in periods_list]
        result[f"day{i}"] = {
            "avg_temperature": round(sum(temps) / len(temps), 1),
            "avg_humidity": round(sum(hums) / len(hums)),
            "avg_rain_probability": round(sum(rain_probs) / len(rain_probs)),
            "avg_wind_speed": round(sum(wind) / len(wind), 1),
            "avg_cloud_cover": round(sum(cloud) / len(cloud)),
        }
    return result

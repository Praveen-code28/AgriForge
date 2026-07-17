# current_weather.py
from .weather_client import WeatherClient, CurrentWeather

def get_current_weather(client: WeatherClient, lat: float, lon: float) -> CurrentWeather:
    return client.get_current(lat, lon)

# forecast.py
from .weather_client import WeatherClient, ForecastPeriod
from typing import List

def get_forecast(client: WeatherClient, lat: float, lon: float, hours: int = 48) -> List[ForecastPeriod]:
    return client.get_forecast(lat, lon, hours)

def aggregate_forecast_by_day(periods: List[ForecastPeriod]) -> dict:
    """Group forecast periods into morning, afternoon, evening, night."""
    # This is a simplification; real grouping may require time-of-day logic.
    # We'll return a dict with keys 'day1', 'day2' each containing periods.
    # For production, we'd produce a more sophisticated aggregation.
    from collections import defaultdict
    days = defaultdict(list)
    for p in periods:
        day_key = p.time.strftime("%Y-%m-%d")
        days[day_key].append(p)
    result = {}
    for i, (day, periods_list) in enumerate(sorted(days.items())[:2], 1):
        # For each day, we can compute average or select representative periods.
        # Here we pick the first period of each day (or we can compute averages)
        # Better: compute average for each variable.
        temps = [p.temperature for p in periods_list]
        hums = [p.humidity for p in periods_list]
        rain_probs = [p.rain_probability for p in periods_list]
        wind = [p.wind_speed for p in periods_list]
        cloud = [p.cloud_cover for p in periods_list]
        result[f"day{i}"] = {
            "avg_temperature": round(sum(temps)/len(temps), 1),
            "avg_humidity": round(sum(hums)/len(hums)),
            "avg_rain_probability": round(sum(rain_probs)/len(rain_probs)),
            "avg_wind_speed": round(sum(wind)/len(wind), 1),
            "avg_cloud_cover": round(sum(cloud)/len(cloud))
        }
    return result
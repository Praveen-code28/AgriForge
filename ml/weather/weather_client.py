from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import requests
import os
from datetime import datetime, timedelta

@dataclass
class CurrentWeather:
    temperature: float       # Celsius
    humidity: int            # %
    rainfall: float          # mm (last hour or today)
    rain_probability: int    # %
    wind_speed: float        # km/h
    pressure: float          # hPa
    cloud_cover: int         # %
    condition: str           # e.g., "Clear", "Rain"
    uv_index: Optional[float] = None
    timestamp: Optional[datetime] = None

@dataclass
class ForecastPeriod:
    time: datetime
    temperature: float
    humidity: int
    rain_probability: int
    wind_speed: float
    cloud_cover: int
    condition: str

class WeatherClient(ABC):
    @abstractmethod
    def get_current(self, lat: float, lon: float) -> CurrentWeather:
        pass

    @abstractmethod
    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> List[ForecastPeriod]:
        pass

class OpenWeatherMapClient(WeatherClient):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key missing")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current(self, lat: float, lon: float) -> CurrentWeather:
        url = f"{self.base_url}/weather"
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        main = data["main"]
        weather = data["weather"][0]
        rain = data.get("rain", {}).get("1h", 0.0)  # rain in last hour
        return CurrentWeather(
            temperature=main["temp"],
            humidity=main["humidity"],
            rainfall=rain,
            rain_probability=0,  # not provided in current
            wind_speed=data["wind"]["speed"] * 3.6,  # m/s to km/h
            pressure=main["pressure"],
            cloud_cover=data["clouds"]["all"],
            condition=weather["description"],
            uv_index=None,
            timestamp=datetime.now()
        )

    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> List[ForecastPeriod]:
        # Use 5-day / 3-hour forecast; we'll extract next 48h
        url = f"{self.base_url}/forecast"
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        periods = []
        now = datetime.now()
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            if dt <= now + timedelta(hours=hours):
                main = item["main"]
                rain = item.get("rain", {}).get("3h", 0.0)  # rain over 3h
                # Convert to probability? Not directly; we can use rain volume as indicator.
                # For probability we might derive from cloud cover or use another source.
                prob = min(100, int(rain * 10))  # dummy conversion
                periods.append(ForecastPeriod(
                    time=dt,
                    temperature=main["temp"],
                    humidity=main["humidity"],
                    rain_probability=prob,
                    wind_speed=item["wind"]["speed"] * 3.6,
                    cloud_cover=item["clouds"]["all"],
                    condition=item["weather"][0]["description"]
                ))
        return periods[:hours//3]  # approx 3h intervals
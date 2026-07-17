# ml/weather/utils/helpers.py

from datetime import datetime
from typing import List, Union, Any, Optional
import json


def safe_avg(values: List[Union[int, float]]) -> float:
    """Calculate average safely, returning 0.0 if the list is empty."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def safe_clamp(value: Union[int, float], 
               min_val: Union[int, float], 
               max_val: Union[int, float]) -> Union[int, float]:
    """Clamp a value between a minimum and maximum."""
    return max(min_val, min(max_val, value))


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert datetime to an ISO‑like string for JSON serialization."""
    return dt.strftime(fmt)


def celsius_to_fahrenheit(c: float) -> float:
    """Convert Celsius to Fahrenheit (if your downstream needs imperial)."""
    return (c * 9/5) + 32


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm * 0.0393701


def kmh_to_ms(kmh: float) -> float:
    """Convert km/h to m/s (some APIs use m/s)."""
    return kmh / 3.6


def safe_round(value: Optional[float], decimals: int = 1) -> Union[float, None]:
    """Safely round a number, returning None if input is None."""
    if value is None:
        return None
    return round(value, decimals)


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merge dict2 into dict1 (dict2 takes precedence)."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def to_json_safe(obj: Any) -> Any:
    """Convert an object to a JSON‑serializable type (handle datetimes, etc.)."""
    if hasattr(obj, "__dataclass_fields__"):  # simple dataclass check
        return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, datetime):
        return format_datetime(obj)
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    return obj
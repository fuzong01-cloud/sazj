from typing import Any

import httpx

from app.schemas.weather import WeatherContext


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherServiceError(RuntimeError):
    pass


async def fetch_weather_context(
    latitude: float,
    longitude: float,
    location_label: str | None = None,
) -> WeatherContext:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": "auto",
        "forecast_days": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(OPEN_METEO_FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise WeatherServiceError(f"天气服务返回错误：HTTP {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise WeatherServiceError(f"天气服务调用失败：{exc}") from exc
    except ValueError as exc:
        raise WeatherServiceError(f"天气服务响应不是合法 JSON：{exc}") from exc

    return build_weather_context(
        latitude=latitude,
        longitude=longitude,
        location_label=location_label,
        current=data.get("current") or data.get("current_weather") or {},
    )


def build_weather_context(
    latitude: float,
    longitude: float,
    location_label: str | None = None,
    current: dict[str, Any] | None = None,
) -> WeatherContext:
    current = current or {}
    weather_code = _to_int(current.get("weather_code") if "weather_code" in current else current.get("weathercode"))
    return WeatherContext(
        latitude=round(latitude, 6),
        longitude=round(longitude, 6),
        location_label=location_label,
        climate_zone=classify_climate_zone(latitude),
        climate_basis="按纬度粗分：热带 <23.5°，亚热带 23.5-35°，温带 35-55°，高纬/寒温带 >55°。",
        temperature_c=_to_float(current.get("temperature_2m") if "temperature_2m" in current else current.get("temperature")),
        relative_humidity_percent=_to_float(current.get("relative_humidity_2m")),
        precipitation_mm=_to_float(current.get("precipitation")),
        wind_speed_kmh=_to_float(current.get("wind_speed_10m") if "wind_speed_10m" in current else current.get("windspeed")),
        weather_code=weather_code,
        weather_text=weather_code_to_text(weather_code),
        observed_at=current.get("time"),
    )


def classify_climate_zone(latitude: float) -> str:
    abs_lat = abs(latitude)
    if abs_lat < 23.5:
        return "热带"
    if abs_lat < 35:
        return "亚热带"
    if abs_lat < 55:
        return "温带"
    return "高纬/寒温带"


def weather_code_to_text(code: int | None) -> str | None:
    if code is None:
        return None
    mapping = {
        0: "晴朗",
        1: "大部晴朗",
        2: "局部多云",
        3: "阴天",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中等毛毛雨",
        55: "强毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        80: "小阵雨",
        81: "中等阵雨",
        82: "强阵雨",
        95: "雷暴",
    }
    if code in mapping:
        return mapping[code]
    if 71 <= code <= 77:
        return "降雪"
    if 85 <= code <= 86:
        return "阵雪"
    if 96 <= code <= 99:
        return "雷暴伴冰雹"
    return f"天气代码 {code}"


def format_weather_for_prompt(weather: WeatherContext | None) -> str:
    if weather is None:
        return "未提供定位和天气上下文。"
    parts = [
        f"位置：{weather.location_label or '浏览器定位'}（纬度 {weather.latitude}，经度 {weather.longitude}）",
        f"气候带：{weather.climate_zone}（{weather.climate_basis}）",
    ]
    if weather.temperature_c is not None:
        parts.append(f"当前气温：{weather.temperature_c}°C")
    if weather.relative_humidity_percent is not None:
        parts.append(f"相对湿度：{weather.relative_humidity_percent}%")
    if weather.precipitation_mm is not None:
        parts.append(f"当前降水：{weather.precipitation_mm} mm")
    if weather.wind_speed_kmh is not None:
        parts.append(f"风速：{weather.wind_speed_kmh} km/h")
    if weather.weather_text:
        parts.append(f"天气现象：{weather.weather_text}")
    if weather.observed_at:
        parts.append(f"观测时间：{weather.observed_at}")
    return "\n".join(parts)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

from pydantic import BaseModel, Field


class WeatherContext(BaseModel):
    latitude: float
    longitude: float
    location_label: str | None = None
    climate_zone: str
    climate_basis: str
    temperature_c: float | None = None
    relative_humidity_percent: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    weather_code: int | None = None
    weather_text: str | None = None
    observed_at: str | None = None
    source: str = "Open-Meteo"


class WeatherQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_label: str | None = None


class WeatherResponse(BaseModel):
    ok: bool = True
    weather: WeatherContext

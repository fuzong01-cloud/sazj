from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherServiceError, fetch_weather_context


router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherResponse)
async def get_weather(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    location_label: str | None = None,
) -> WeatherResponse:
    try:
        weather = await fetch_weather_context(
            latitude=latitude,
            longitude=longitude,
            location_label=location_label,
        )
    except WeatherServiceError as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "message": str(exc)}) from exc
    return WeatherResponse(weather=weather)

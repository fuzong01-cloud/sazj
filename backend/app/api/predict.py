from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.auth import get_optional_current_user
from app.providers.vision_provider import ProviderNotConfiguredError, VisionProviderError
from app.schemas.auth import UserPublic
from app.schemas.predict import PredictResponse
from app.services.weather_service import WeatherServiceError, fetch_weather_context
from app.services.predict_service import (
    InvalidImageError,
    get_prediction_service,
)

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
async def predict_image(
    file: UploadFile = File(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    location_label: str | None = Form(default=None),
    provider_id: int | None = Form(default=None),
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> PredictResponse:
    image_bytes = await file.read()
    service = get_prediction_service()

    try:
        weather = None
        if latitude is not None and longitude is not None:
            weather = await fetch_weather_context(
                latitude=latitude,
                longitude=longitude,
                location_label=location_label,
            )
        return await service.predict(
            image_bytes=image_bytes,
            filename=file.filename or "",
            content_type=file.content_type or "",
            user_id=current_user.id if current_user else None,
            weather=weather,
            provider_id=provider_id,
        )
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "message": str(exc)},
        ) from exc
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=409,
            detail={"ok": False, "message": str(exc)},
        ) from exc
    except VisionProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "message": str(exc)},
        ) from exc
    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "message": str(exc)},
        ) from exc

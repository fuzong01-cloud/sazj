from fastapi import APIRouter, File, HTTPException, UploadFile

from app.providers.vision_provider import ProviderNotConfiguredError, VisionProviderError
from app.schemas.predict import PredictResponse
from app.services.predict_service import (
    InvalidImageError,
    get_prediction_service,
)

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
async def predict_image(file: UploadFile = File(...)) -> PredictResponse:
    image_bytes = await file.read()
    service = get_prediction_service()

    try:
        return await service.predict(
            image_bytes=image_bytes,
            filename=file.filename or "",
            content_type=file.content_type or "",
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

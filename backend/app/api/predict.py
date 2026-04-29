from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.auth import get_current_user
from app.providers.vision_provider import ProviderNotConfiguredError, VisionProviderError
from app.repositories.conversation_repository import add_message, ensure_conversation
from app.schemas.auth import UserPublic
from app.schemas.conversation import ConversationMessageCreate
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
    conversation_id: int | None = Form(default=None),
    prompt: str | None = Form(default=None),
    current_user: UserPublic = Depends(get_current_user),
) -> PredictResponse:
    image_bytes = await file.read()
    service = get_prediction_service()
    user_prompt = prompt or "请识别这张马铃薯叶片图片，并结合环境给出防治建议。"
    conversation = ensure_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
        title=user_prompt,
    )
    add_message(
        ConversationMessageCreate(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="user",
            message_type="image",
            content=user_prompt,
            payload={
                "filename": file.filename or "",
                "content_type": file.content_type or "",
                "has_weather": latitude is not None and longitude is not None,
            },
        )
    )

    try:
        weather = None
        if latitude is not None and longitude is not None:
            weather = await fetch_weather_context(
                latitude=latitude,
                longitude=longitude,
                location_label=location_label,
            )
        result = await service.predict(
            image_bytes=image_bytes,
            filename=file.filename or "",
            content_type=file.content_type or "",
            user_id=current_user.id,
            prompt=user_prompt,
            weather=weather,
            provider_id=provider_id,
        )
        result = result.model_copy(update={"conversation_id": conversation.id})
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="prediction",
                content=result.content or result.raw_text or result.summary,
                provider_name=result.provider_name,
                model_name=result.model_name,
                payload=result.model_dump(mode="json"),
            )
        )
        return result
    except InvalidImageError as exc:
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="error",
                content=str(exc),
                payload={"error": True},
            )
        )
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "message": str(exc), "conversation_id": conversation.id},
        ) from exc
    except ProviderNotConfiguredError as exc:
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="error",
                content=str(exc),
                payload={"error": True},
            )
        )
        raise HTTPException(
            status_code=409,
            detail={"ok": False, "message": str(exc), "conversation_id": conversation.id},
        ) from exc
    except VisionProviderError as exc:
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="error",
                content=str(exc),
                payload={"error": True},
            )
        )
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "message": str(exc), "conversation_id": conversation.id},
        ) from exc
    except WeatherServiceError as exc:
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="error",
                content=str(exc),
                payload={"error": True},
            )
        )
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "message": str(exc), "conversation_id": conversation.id},
        ) from exc

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.auth import get_current_user
from app.providers.vision_provider import ProviderNotConfiguredError, VisionProviderError, get_enabled_vision_provider
from app.repositories.conversation_repository import add_message, ensure_conversation
from app.repositories.prediction_record_repository import create_prediction_record
from app.schemas.auth import UserPublic
from app.schemas.conversation import ConversationMessageCreate
from app.schemas.predict import PredictResponse
from app.schemas.prediction_record import PredictionRecordCreate
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
    deep_thinking: bool = Form(default=False),
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
                "deep_thinking": deep_thinking,
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
            deep_thinking=deep_thinking,
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


@router.post("/predict/stream")
async def predict_image_stream(
    file: UploadFile = File(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    location_label: str | None = Form(default=None),
    provider_id: int | None = Form(default=None),
    conversation_id: int | None = Form(default=None),
    prompt: str | None = Form(default=None),
    deep_thinking: bool = Form(default=False),
    current_user: UserPublic = Depends(get_current_user),
) -> StreamingResponse:
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail={"ok": False, "message": "请上传一张图片"})

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
                "deep_thinking": deep_thinking,
            },
        )
    )

    async def event_stream() -> AsyncIterator[str]:
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        provider_name = ""
        model_name = ""
        try:
            weather = None
            if latitude is not None and longitude is not None:
                weather = await fetch_weather_context(
                    latitude=latitude,
                    longitude=longitude,
                    location_label=location_label,
                )
            provider = get_enabled_vision_provider(provider_id, deep_thinking=deep_thinking)
            provider_name = provider.config.provider_name
            model_name = provider.config.model_name
            yield _sse(
                {
                    "type": "meta",
                    "conversation_id": conversation.id,
                    "provider_name": provider_name,
                    "model_name": model_name,
                }
            )
            async for event in provider.stream_predict(
                image_bytes=image_bytes,
                content_type=file.content_type or "",
                user_prompt=user_prompt,
                deep_thinking=deep_thinking,
                weather=weather,
            ):
                event_type = event.get("type")
                text = event.get("text", "")
                if event_type == "reasoning":
                    reasoning_parts.append(text)
                    yield _sse({"type": "reasoning", "text": text})
                elif event_type == "content":
                    content_parts.append(text)
                    yield _sse({"type": "content", "text": text})

            final_content = "".join(content_parts).strip()
            final_reasoning = "".join(reasoning_parts).strip()
            if not final_content and final_reasoning:
                final_content = "模型已返回推理过程，但尚未生成最终识别结论。请增大后台输出长度、关闭深度思考，或稍后重试。"
                yield _sse({"type": "content", "text": final_content})

            result = provider.response_from_text(
                text=final_content,
                reasoning_content=final_reasoning,
                weather=weather,
            )
            record = create_prediction_record(
                PredictionRecordCreate(
                    user_id=current_user.id,
                    provider_name=result.provider_name,
                    model_name=result.model_name,
                    disease_name=result.disease_name,
                    risk_level=result.risk_level,
                    confidence=result.confidence,
                    confidence_percent=result.confidence_percent,
                    summary=result.summary,
                    suggestions=result.suggestions,
                    raw_text=result.raw_text,
                    image_filename=file.filename or None,
                    image_content_type=file.content_type or None,
                )
            )
            result = result.model_copy(update={"record_id": record.id, "conversation_id": conversation.id})
            add_message(
                ConversationMessageCreate(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    role="assistant",
                    message_type="prediction",
                    content=result.content or result.raw_text or result.summary,
                    provider_name=provider_name,
                    model_name=model_name,
                    payload=result.model_dump(mode="json"),
                )
            )
            yield _sse({"type": "result", "result": result.model_dump(mode="json")})
            yield _sse({"type": "done", "conversation_id": conversation.id})
        except (ProviderNotConfiguredError, VisionProviderError, WeatherServiceError) as exc:
            message = str(exc)
            add_message(
                ConversationMessageCreate(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    role="assistant",
                    message_type="error",
                    content=message,
                    payload={"error": True},
                )
            )
            yield _sse({"type": "error", "message": message, "conversation_id": conversation.id})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

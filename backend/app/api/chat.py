from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_optional_current_user
from app.providers.text_provider import (
    TextProviderError,
    TextProviderNotConfiguredError,
    get_enabled_text_provider,
)
from app.schemas.text_tasks import ChatRequest, ChatResponse
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> ChatResponse:
    try:
        provider = get_enabled_text_provider(user_id=current_user.id if current_user else None)
        user_prompt = (
            f"上下文：{payload.context or '无'}\n"
            f"用户问题：{payload.question}\n"
            "请结合马铃薯病虫害识别和防治场景回答。"
        )
        answer = await provider.generate(
            system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
            user_prompt=user_prompt,
        )
        return ChatResponse(
            provider_name=provider.config.provider_name,
            model_name=provider.config.model_name,
            answer=answer,
        )
    except TextProviderNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail={"ok": False, "message": str(exc)}) from exc
    except TextProviderError as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "message": str(exc)}) from exc

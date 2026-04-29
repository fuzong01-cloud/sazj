from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.providers.text_provider import (
    TextProviderError,
    TextProviderNotConfiguredError,
    get_enabled_text_provider,
)
from app.repositories.conversation_repository import add_message, ensure_conversation
from app.schemas.conversation import ConversationMessageCreate
from app.schemas.text_tasks import ChatRequest, ChatResponse
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> ChatResponse:
    conversation = ensure_conversation(
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        title=payload.question,
    )
    add_message(
        ConversationMessageCreate(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="user",
            message_type="text",
            content=payload.question,
            payload={"context": payload.context},
        )
    )

    try:
        provider = get_enabled_text_provider(payload.provider_id)
        user_prompt = (
            f"上下文：{payload.context or '无'}\n"
            f"用户问题：{payload.question}\n"
            "请结合马铃薯病虫害识别和防治场景回答。"
        )
        answer = await provider.generate(
            system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
            user_prompt=user_prompt,
        )
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="text",
                content=answer,
                provider_name=provider.config.provider_name,
                model_name=provider.config.model_name,
            )
        )
        return ChatResponse(
            provider_name=provider.config.provider_name,
            model_name=provider.config.model_name,
            answer=answer,
            conversation_id=conversation.id,
        )
    except TextProviderNotConfiguredError as exc:
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
    except TextProviderError as exc:
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

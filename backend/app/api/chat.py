import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

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
            payload={"context": payload.context, "deep_thinking": payload.deep_thinking},
        )
    )

    try:
        provider = get_enabled_text_provider(payload.provider_id, deep_thinking=payload.deep_thinking)
        user_prompt = (
            f"上下文：{payload.context or '无'}\n"
            f"用户问题：{payload.question}\n"
            "请结合马铃薯病虫害识别和防治场景回答。"
        )
        result = await provider.generate(
            system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
            user_prompt=user_prompt,
            deep_thinking=payload.deep_thinking,
        )
        add_message(
            ConversationMessageCreate(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="assistant",
                message_type="text",
                content=result.content,
                provider_name=provider.config.provider_name,
                model_name=provider.config.model_name,
                payload={"reasoning_content": result.reasoning_content},
            )
        )
        return ChatResponse(
            provider_name=provider.config.provider_name,
            model_name=provider.config.model_name,
            answer=result.content,
            reasoning_content=result.reasoning_content,
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


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> StreamingResponse:
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
            payload={"context": payload.context, "deep_thinking": payload.deep_thinking},
        )
    )

    async def event_stream() -> AsyncIterator[str]:
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        provider_name = ""
        model_name = ""
        try:
            provider = get_enabled_text_provider(payload.provider_id, deep_thinking=payload.deep_thinking)
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
            user_prompt = (
                f"上下文：{payload.context or '无'}\n"
                f"用户问题：{payload.question}\n"
                "请结合马铃薯病虫害识别和防治场景回答。"
            )
            async for event in provider.stream_generate(
                system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
                user_prompt=user_prompt,
                deep_thinking=payload.deep_thinking,
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
                final_content = "模型已返回推理过程，但尚未生成最终答案。请增大后台输出长度、关闭深度思考，或稍后重试。"
                yield _sse({"type": "content", "text": final_content})
            add_message(
                ConversationMessageCreate(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    role="assistant",
                    message_type="text",
                    content=final_content,
                    provider_name=provider_name,
                    model_name=model_name,
                    payload={"reasoning_content": final_reasoning},
                )
            )
            yield _sse({"type": "done", "conversation_id": conversation.id})
        except (TextProviderNotConfiguredError, TextProviderError) as exc:
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

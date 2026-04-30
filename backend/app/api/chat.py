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
from app.schemas.auth import UserPublic
from app.schemas.conversation import ConversationMessageCreate
from app.schemas.text_tasks import ChatRequest, ChatResponse
from app.schemas.web_search import WebSearchResult
from app.services.web_search_service import WebSearchError, format_search_context, search_web

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
            payload=_request_payload(payload),
        )
    )

    try:
        provider = get_enabled_text_provider(payload.provider_id, deep_thinking=payload.deep_thinking)
        search_context, search_results = await _search_context(payload)
        result = await provider.generate(
            system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
            user_prompt=_build_user_prompt(payload, search_context),
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
                payload={
                    "reasoning_content": result.reasoning_content,
                    "web_search": payload.web_search,
                    "web_search_results": _dump_search_results(search_results),
                },
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
        _save_error(conversation.id, current_user.id, str(exc))
        raise HTTPException(
            status_code=409,
            detail={"ok": False, "message": str(exc), "conversation_id": conversation.id},
        ) from exc
    except TextProviderError as exc:
        _save_error(conversation.id, current_user.id, str(exc))
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
            payload=_request_payload(payload),
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
            search_context, search_results = await _search_context(payload)
            yield _sse(
                {
                    "type": "meta",
                    "conversation_id": conversation.id,
                    "provider_name": provider_name,
                    "model_name": model_name,
                    "web_search": payload.web_search,
                    "web_search_results": _dump_search_results(search_results),
                }
            )
            async for event in provider.stream_generate(
                system_prompt="你是农业病害平台的网页 AI 助手，回答要简洁、谨慎、中文。",
                user_prompt=_build_user_prompt(payload, search_context),
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
                    payload={
                        "reasoning_content": final_reasoning,
                        "web_search": payload.web_search,
                        "web_search_results": _dump_search_results(search_results),
                    },
                )
            )
            yield _sse({"type": "done", "conversation_id": conversation.id})
        except (TextProviderNotConfiguredError, TextProviderError) as exc:
            message = str(exc)
            _save_error(conversation.id, current_user.id, message)
            yield _sse({"type": "error", "message": message, "conversation_id": conversation.id})

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=_stream_headers())


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


def _request_payload(payload: ChatRequest) -> dict:
    return {
        "context": payload.context,
        "deep_thinking": payload.deep_thinking,
        "web_search": payload.web_search,
    }


async def _search_context(payload: ChatRequest) -> tuple[str, list[WebSearchResult]]:
    if not payload.web_search:
        return "", []
    try:
        results = await search_web(payload.question)
    except WebSearchError as exc:
        return f"网页搜索失败：{exc}", []
    return format_search_context(results), results


def _build_user_prompt(payload: ChatRequest, search_context: str = "") -> str:
    context_parts = [payload.context or "无"]
    if search_context:
        context_parts.append(search_context)
    return (
        f"上下文：{chr(10).join(context_parts)}\n"
        f"用户问题：{payload.question}\n"
        "请结合马铃薯病虫害识别和防治场景回答。"
    )


def _dump_search_results(results: list[WebSearchResult]) -> list[dict]:
    return [item.model_dump() for item in results]


def _save_error(conversation_id: int, user_id: int, message: str) -> None:
    add_message(
        ConversationMessageCreate(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            message_type="error",
            content=message,
            payload={"error": True},
        )
    )

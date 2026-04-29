from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_optional_current_user
from app.providers.text_provider import (
    TextProviderError,
    TextProviderNotConfiguredError,
    get_enabled_text_provider,
)
from app.schemas.text_tasks import AdviceRequest, AdviceResponse
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/advice", tags=["advice"])


@router.post("/generate", response_model=AdviceResponse)
async def generate_advice(
    payload: AdviceRequest,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> AdviceResponse:
    try:
        provider = get_enabled_text_provider(user_id=current_user.id if current_user else None)
        user_prompt = (
            f"病害：{payload.disease_name}\n"
            f"风险等级：{payload.risk_level or '待确认'}\n"
            f"补充上下文：{payload.context or '无'}\n"
            "请给出面向马铃薯种植场景的防治建议，避免给出具体农药剂量。"
        )
        advice = await provider.generate(
            system_prompt="你是农业病虫害防治建议助手，回答要谨慎、实用、中文。",
            user_prompt=user_prompt,
        )
        return AdviceResponse(
            provider_name=provider.config.provider_name,
            model_name=provider.config.model_name,
            advice=advice,
        )
    except TextProviderNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail={"ok": False, "message": str(exc)}) from exc
    except TextProviderError as exc:
        raise HTTPException(status_code=502, detail={"ok": False, "message": str(exc)}) from exc

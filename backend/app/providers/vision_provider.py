import base64
import json
import logging
from typing import Any

from app.providers.chat_completions_runtime import (
    ChatCompletionsRuntimeError,
    extract_chat_content,
    post_chat_completions,
)
from app.repositories.model_config_repository import get_enabled_provider, get_enabled_provider_by_id
from app.schemas.model_config import ProviderType
from app.schemas.predict import PredictResponse
from app.schemas.weather import WeatherContext
from app.services.weather_service import format_weather_for_prompt

logger = logging.getLogger(__name__)


class ProviderNotConfiguredError(RuntimeError):
    pass


class VisionProviderError(RuntimeError):
    pass


class VisionProvider:
    def __init__(self, config) -> None:
        self.config = config

    async def predict(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        user_prompt: str | None = None,
        weather: WeatherContext | None = None,
    ) -> PredictResponse:
        mime_type = content_type if content_type.startswith("image/") else "image/png"
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{mime_type};base64,{image_base64}"
        prompt = (
            f"{user_prompt or '请识别这张马铃薯叶片图片，并结合环境给出防治建议。'}\n"
            "请只返回 JSON，不要返回 Markdown。字段包括："
            "disease_name、confidence、risk_level、summary、suggestions。"
            "confidence 为 0 到 1。\n"
            f"{format_weather_for_prompt(weather)}"
        )

        # Kimi/OpenAI-compatible multimodal chat/completions payload.
        # Do not send temperature/top_p/response_format/modalities/input/stream/etc.
        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            "max_tokens": 512,
        }

        try:
            data = await post_chat_completions(self.config, payload)
            text = extract_chat_content(data)
        except ChatCompletionsRuntimeError as exc:
            raise VisionProviderError(f"视觉模型接口返回错误：{exc}") from exc

        logger.info(
            "vision provider parsed content provider=%s model=%s content=%s",
            self.config.provider_name,
            self.config.model_name,
            text[:3000],
        )
        parsed = self._parse_json(text)
        confidence = self._normalize_confidence(parsed.get("confidence"))
        confidence_percent = round(confidence * 100, 2) if confidence is not None else None
        suggestions = self._normalize_suggestions(parsed.get("suggestions", []))
        disease_name = str(parsed.get("disease_name") or parsed.get("title") or "模型回复")
        risk_level = str(parsed.get("risk_level") or parsed.get("status") or "未结构化")
        summary = str(parsed.get("summary") or text or "模型未返回有效内容")

        response = PredictResponse(
            provider_name=self.config.provider_name,
            model_name=self.config.model_name,
            disease_name=disease_name,
            confidence=confidence,
            confidence_percent=confidence_percent,
            risk_level=risk_level,
            summary=summary,
            suggestions=suggestions,
            content=text,
            raw_text=text,
            weather=weather,
        )
        logger.info("vision provider final response=%s", response.model_dump(mode="json"))
        return response

    def _parse_json(self, text: str) -> dict[str, Any]:
        if not text:
            return {}

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]

        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _normalize_confidence(self, value) -> float | None:
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                return None
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        return None

    def _normalize_suggestions(self, value) -> list[str]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]


def get_enabled_vision_provider(config_id: int | None = None) -> VisionProvider:
    if config_id is not None:
        config = get_enabled_provider_by_id(config_id, None, user_id=None)
    else:
        config = get_enabled_provider(ProviderType.vision, user_id=None)
    if config is None:
        raise ProviderNotConfiguredError("平台尚未配置启用的通用模型，请联系管理员在 /admin/providers 配置")
    return VisionProvider(config)

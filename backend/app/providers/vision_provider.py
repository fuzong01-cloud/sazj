import base64
import json
import logging
from typing import Any, AsyncIterator

from app.providers.chat_completions_runtime import (
    ChatCompletionsRuntimeError,
    extract_chat_message,
    post_chat_completions,
    stream_chat_completions,
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
        deep_thinking: bool = False,
        weather: WeatherContext | None = None,
    ) -> PredictResponse:
        payload = self._build_payload(image_bytes, content_type, user_prompt, deep_thinking, weather)

        try:
            data = await post_chat_completions(self.config, payload)
            message = extract_chat_message(data)
            text = message.content
            if not text and message.reasoning_content:
                text = "模型已返回推理过程，但尚未生成最终识别结论。请增大后台输出长度、关闭深度思考，或稍后重试。"
        except ChatCompletionsRuntimeError as exc:
            raise VisionProviderError(f"视觉模型接口返回错误：{exc}") from exc

        logger.info(
            "vision provider parsed content provider=%s model=%s content=%s",
            self.config.provider_name,
            self.config.model_name,
            text[:3000],
        )
        response = self.response_from_text(text=text, reasoning_content=message.reasoning_content, weather=weather)
        logger.info("vision provider final response=%s", response.model_dump(mode="json"))
        return response

    async def stream_predict(
        self,
        image_bytes: bytes,
        content_type: str,
        user_prompt: str | None = None,
        deep_thinking: bool = False,
        weather: WeatherContext | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        payload = self._build_payload(image_bytes, content_type, user_prompt, deep_thinking, weather)
        try:
            async for event in stream_chat_completions(self.config, payload):
                yield event
        except ChatCompletionsRuntimeError as exc:
            raise VisionProviderError(f"视觉模型接口返回错误：{exc}") from exc

    def response_from_text(
        self,
        text: str,
        reasoning_content: str = "",
        weather: WeatherContext | None = None,
    ) -> PredictResponse:
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
            reasoning_content=reasoning_content,
            weather=weather,
        )
        return response

    def _build_payload(
        self,
        image_bytes: bytes,
        content_type: str,
        user_prompt: str | None,
        deep_thinking: bool,
        weather: WeatherContext | None,
    ) -> dict[str, Any]:
        mime_type = content_type if content_type.startswith("image/") else "image/png"
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{mime_type};base64,{image_base64}"
        thinking_instruction = (
            "可以进行深度思考，但最终必须在 message.content 中输出 JSON。"
            if deep_thinking
            else "请直接输出最终 JSON，不要输出推理过程，不要返回 Markdown。"
        )
        prompt = (
            f"{user_prompt or '请识别这张马铃薯叶片图片，并结合环境给出防治建议。'}\n"
            f"{thinking_instruction}"
            "字段：disease_name、confidence、risk_level、summary、suggestions。"
            "confidence 为 0 到 1；summary 不超过 120 字；suggestions 最多 4 条。\n"
            f"{format_weather_for_prompt(weather)}"
        )
        prompt = self._truncate_for_context(prompt)
        return {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            "max_tokens": self.config.max_output_tokens or (3072 if deep_thinking else 2048),
        }

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

    def _truncate_for_context(self, text: str) -> str:
        if not self.config.max_context_tokens:
            return text
        char_limit = max(512, self.config.max_context_tokens * 4)
        if len(text) <= char_limit:
            return text
        return text[-char_limit:]


def get_enabled_vision_provider(config_id: int | None = None, deep_thinking: bool = False) -> VisionProvider:
    if config_id is not None:
        config = get_enabled_provider_by_id(config_id, None, user_id=None)
    else:
        config = get_enabled_provider(ProviderType.vision, user_id=None, prefer_reasoning=deep_thinking)
    if config is None:
        raise ProviderNotConfiguredError("平台尚未配置启用的通用模型，请联系管理员在 /admin/providers 配置")
    return VisionProvider(config)

import base64
import json
from typing import Any

import httpx

from app.repositories.model_config_repository import get_enabled_provider, get_enabled_provider_by_id
from app.schemas.model_config import ProviderType
from app.schemas.predict import PredictResponse
from app.schemas.weather import WeatherContext
from app.services.weather_service import format_weather_for_prompt


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
        weather: WeatherContext | None = None,
    ) -> PredictResponse:
        mime_type = content_type if content_type.startswith("image/") else "image/png"
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{mime_type};base64,{image_base64}"

        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是马铃薯病虫害识别助手。请根据图片判断可能的病害，"
                        "并结合定位、天气、气候带给出专业防治建议。仅返回 JSON，"
                        "不要返回 Markdown。字段包括 disease_name、confidence、"
                        "risk_level、summary、suggestions。confidence 为 0 到 1。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请识别这张马铃薯叶片图片，并结合以下环境上下文给出专业防治建议。\n"
                                f"{format_weather_for_prompt(weather)}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                },
            ],
            "temperature": 0.2,
        }

        data = await self._post_chat_completions(payload)
        text = self._extract_text(data)
        parsed = self._parse_json(text)

        confidence = parsed.get("confidence")
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = None
        if isinstance(confidence, (int, float)):
            confidence = max(0.0, min(1.0, float(confidence)))
            confidence_percent = round(confidence * 100, 2)
        else:
            confidence = None
            confidence_percent = None

        suggestions = parsed.get("suggestions", [])
        if isinstance(suggestions, str):
            suggestions = [suggestions]
        if not isinstance(suggestions, list):
            suggestions = []

        return PredictResponse(
            provider_name=self.config.provider_name,
            model_name=self.config.model_name,
            disease_name=str(parsed.get("disease_name") or "待确认"),
            confidence=confidence,
            confidence_percent=confidence_percent,
            risk_level=str(parsed.get("risk_level") or "待确认"),
            summary=str(parsed.get("summary") or text or "视觉模型未返回有效摘要"),
            suggestions=[str(item) for item in suggestions if str(item).strip()],
            raw_text=text,
            weather=weather,
        )

    async def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise VisionProviderError(f"视觉模型接口返回错误：HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise VisionProviderError(f"视觉模型接口调用失败：{exc}") from exc

    def _extract_text(self, data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VisionProviderError("视觉模型响应格式不符合 OpenAI-compatible chat/completions") from exc

        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()
        return str(content).strip()

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


def get_enabled_vision_provider(config_id: int | None = None) -> VisionProvider:
    if config_id is not None:
        config = get_enabled_provider_by_id(config_id, ProviderType.vision, user_id=None)
    else:
        config = get_enabled_provider(ProviderType.vision, user_id=None)
    if config is None:
        raise ProviderNotConfiguredError("平台尚未配置启用的视觉模型提供商，请联系管理员在 /admin/providers 配置")
    return VisionProvider(config)

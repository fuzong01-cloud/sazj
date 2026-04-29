from typing import Any

import httpx

from app.repositories.model_config_repository import get_enabled_provider
from app.schemas.model_config import ProviderType


class TextProviderError(RuntimeError):
    pass


class TextProviderNotConfiguredError(RuntimeError):
    pass


class TextProvider:
    def __init__(self, config) -> None:
        self.config = config

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
        }
        data = await self._post_chat_completions(payload)
        return self._extract_text(data)

    async def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise TextProviderError(f"文本模型接口返回错误：HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise TextProviderError(f"文本模型接口调用失败：{exc}") from exc

    def _extract_text(self, data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise TextProviderError("文本模型响应格式不符合 OpenAI-compatible chat/completions") from exc

        if isinstance(content, str):
            return content.strip()
        return str(content).strip()


def get_enabled_text_provider() -> TextProvider:
    config = get_enabled_provider(ProviderType.text)
    if config is None:
        raise TextProviderNotConfiguredError("未配置启用的文本模型提供商，请先创建 provider_type=text 的模型配置")
    return TextProvider(config)

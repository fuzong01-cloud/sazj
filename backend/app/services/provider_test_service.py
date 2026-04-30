import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.providers.chat_completions_runtime import (
    build_chat_completions_url,
    extract_upstream_error_message,
)
from app.schemas.model_config import ModelConfigStored

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


def test_provider_config(config: ModelConfigStored) -> ProviderTestResult:
    url = build_chat_completions_url(config.base_url)
    payload: dict[str, Any] = {
        "model": config.model_name,
        "messages": [
            {
                "role": "user",
                "content": "你好，请只回复 OK",
            }
        ],
        "max_tokens": 128,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    logger.info("provider test request url=%s", url)
    logger.info("provider test request payload=%s", payload)

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=headers, json=payload)
            response_text = response.text
            logger.info("provider test upstream status=%s", response.status_code)
            logger.info("provider test upstream response=%s", response_text[:3000])
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        message = extract_upstream_error_message(exc.response.text)
        return ProviderTestResult(
            ok=False,
            message=f"HTTP {exc.response.status_code}: {message}",
        )
    except httpx.HTTPError as exc:
        return ProviderTestResult(ok=False, message=f"连接失败：{exc}")
    except ValueError as exc:
        return ProviderTestResult(ok=False, message=f"响应不是合法 JSON：{exc}")

    if not _has_chat_completion_content(data):
        return ProviderTestResult(
            ok=False,
            message="接口可访问，但响应格式不是 OpenAI-compatible chat/completions。",
        )

    return ProviderTestResult(
        ok=True,
        message="连接成功。已通过 chat/completions 最小请求验证 Base URL、API Key 和模型名。",
    )


def _has_chat_completion_content(data: dict[str, Any]) -> bool:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return False
    return content is not None

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.schemas.model_config import ModelConfigStored

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


def test_provider_config(config: ModelConfigStored) -> ProviderTestResult:
    url = _build_chat_completions_url(config.base_url)
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
        message = _extract_upstream_error_message(exc.response.text)
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


def _build_chat_completions_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def _extract_upstream_error_message(response_text: str) -> str:
    try:
        data = httpx.Response(200, text=response_text).json()
    except ValueError:
        return response_text[:3000] or "上游没有返回错误正文"

    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    if isinstance(data, dict) and data.get("message"):
        return str(data["message"])
    return response_text[:3000] or "上游没有返回错误正文"


def _has_chat_completion_content(data: dict[str, Any]) -> bool:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return False
    return content is not None

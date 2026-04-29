from dataclasses import dataclass
from typing import Any

import httpx

from app.schemas.model_config import ModelConfigStored


@dataclass(frozen=True)
class ProviderTestResult:
    ok: bool
    message: str


def test_provider_config(config: ModelConfigStored) -> ProviderTestResult:
    url = config.base_url.rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": config.model_name,
        "messages": [
            {
                "role": "user",
                "content": "请只回复 ok，用于测试模型接口连通性。",
            }
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {config.api_key}"}

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return ProviderTestResult(
            ok=False,
            message=f"HTTP {exc.response.status_code}：请检查 Base URL、API Key、模型名或额度。",
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
        message="连接成功。该测试验证基础 chat/completions 连通性；视觉图片能力仍需通过识别接口验证。",
    )


def _has_chat_completion_content(data: dict[str, Any]) -> bool:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return False
    return content is not None

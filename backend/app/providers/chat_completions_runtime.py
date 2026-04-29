import copy
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ChatCompletionsRuntimeError(RuntimeError):
    pass


async def post_chat_completions(config, payload: dict[str, Any], *, timeout: int = 60) -> dict[str, Any]:
    url = build_chat_completions_url(config.base_url)
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    logger.info("runtime model request url=%s", url)
    logger.info("runtime model request model=%s", payload.get("model"))
    logger.info("runtime model request payload=%s", sanitize_payload_for_log(payload))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response_text = response.text
            logger.info("runtime model upstream status=%s", response.status_code)
            logger.info("runtime model upstream response=%s", response_text[:3000])
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        message = extract_upstream_error_message(exc.response.text)
        raise ChatCompletionsRuntimeError(f"HTTP {exc.response.status_code}: {message}") from exc
    except httpx.HTTPError as exc:
        raise ChatCompletionsRuntimeError(f"连接失败：{exc}") from exc
    except ValueError as exc:
        raise ChatCompletionsRuntimeError(f"响应不是合法 JSON：{exc}") from exc


def build_chat_completions_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def extract_upstream_error_message(response_text: str) -> str:
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


def extract_chat_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ChatCompletionsRuntimeError("响应格式不符合 OpenAI-compatible chat/completions") from exc

    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()
    return str(content).strip()


def sanitize_payload_for_log(payload: dict[str, Any]) -> dict[str, Any]:
    safe = copy.deepcopy(payload)
    for message in safe.get("messages", []):
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                image_url = item.get("image_url")
                if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                    url = image_url["url"]
                    if url.startswith("data:image/"):
                        image_url["url"] = url[:120] + "...<base64 truncated>"
    return safe

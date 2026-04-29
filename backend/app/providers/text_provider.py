import logging
from dataclasses import dataclass
from typing import AsyncIterator

from app.providers.chat_completions_runtime import (
    ChatCompletionsRuntimeError,
    extract_chat_message,
    post_chat_completions,
    stream_chat_completions,
)
from app.repositories.model_config_repository import get_enabled_provider, get_enabled_provider_by_id
from app.schemas.model_config import ProviderType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextGenerationResult:
    content: str
    reasoning_content: str = ""


class TextProviderError(RuntimeError):
    pass


class TextProviderNotConfiguredError(RuntimeError):
    pass


class TextProvider:
    def __init__(self, config) -> None:
        self.config = config

    async def generate(self, system_prompt: str, user_prompt: str, deep_thinking: bool = False) -> TextGenerationResult:
        payload = self._build_payload(system_prompt, user_prompt, deep_thinking)

        try:
            data = await post_chat_completions(self.config, payload)
            message = extract_chat_message(data)
            content = message.content
            if not content and message.reasoning_content:
                content = "模型已返回推理过程，但尚未生成最终答案。请增大后台输出长度、关闭深度思考，或稍后重试。"
            logger.info(
                "text provider parsed content provider=%s model=%s content=%s",
                self.config.provider_name,
                self.config.model_name,
                content[:3000],
            )
            return TextGenerationResult(
                content=content,
                reasoning_content=message.reasoning_content,
            )
        except ChatCompletionsRuntimeError as exc:
            raise TextProviderError(f"文本模型接口返回错误：{exc}") from exc

    async def stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        deep_thinking: bool = False,
    ) -> AsyncIterator[dict[str, str]]:
        payload = self._build_payload(system_prompt, user_prompt, deep_thinking)
        try:
            async for event in stream_chat_completions(self.config, payload):
                yield event
        except ChatCompletionsRuntimeError as exc:
            raise TextProviderError(f"文本模型接口返回错误：{exc}") from exc

    def _build_payload(self, system_prompt: str, user_prompt: str, deep_thinking: bool) -> dict:
        # Keep runtime payload close to the Kimi-verified minimal chat/completions shape:
        # model + single user message + max_tokens, no temperature/top_p/response_format/etc.
        thinking_instruction = (
            "可以进行深度思考，但最终必须在 message.content 中输出答案。"
            if deep_thinking
            else "请直接输出最终答案，不要展示推理过程。"
        )
        content = self._truncate_for_context(f"{system_prompt}\n{thinking_instruction}\n\n{user_prompt}".strip())
        return {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "max_tokens": self.config.max_output_tokens or (1536 if deep_thinking else 768),
        }

    def _truncate_for_context(self, text: str) -> str:
        if not self.config.max_context_tokens:
            return text
        # Chinese/English mixed prompt rough approximation: 1 token ~= 4 chars.
        char_limit = max(512, self.config.max_context_tokens * 4)
        if len(text) <= char_limit:
            return text
        return text[-char_limit:]


def get_enabled_text_provider(config_id: int | None = None, deep_thinking: bool = False) -> TextProvider:
    if config_id is not None:
        config = get_enabled_provider_by_id(config_id, None, user_id=None)
    else:
        config = get_enabled_provider(ProviderType.text, user_id=None, prefer_reasoning=deep_thinking)
    if config is None:
        raise TextProviderNotConfiguredError("平台尚未配置启用的通用模型，请联系管理员在 /admin/providers 配置")
    return TextProvider(config)

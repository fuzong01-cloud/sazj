import logging

from app.providers.chat_completions_runtime import (
    ChatCompletionsRuntimeError,
    extract_chat_content,
    post_chat_completions,
)
from app.repositories.model_config_repository import get_enabled_provider, get_enabled_provider_by_id
from app.schemas.model_config import ProviderType

logger = logging.getLogger(__name__)


class TextProviderError(RuntimeError):
    pass


class TextProviderNotConfiguredError(RuntimeError):
    pass


class TextProvider:
    def __init__(self, config) -> None:
        self.config = config

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Keep runtime payload close to the Kimi-verified minimal chat/completions shape:
        # model + single user message + max_tokens, no temperature/top_p/response_format/etc.
        content = f"{system_prompt}\n\n{user_prompt}".strip()
        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "max_tokens": 128,
        }

        try:
            data = await post_chat_completions(self.config, payload)
            content = extract_chat_content(data)
            logger.info(
                "text provider parsed content provider=%s model=%s content=%s",
                self.config.provider_name,
                self.config.model_name,
                content[:3000],
            )
            return content
        except ChatCompletionsRuntimeError as exc:
            raise TextProviderError(f"文本模型接口返回错误：{exc}") from exc


def get_enabled_text_provider(config_id: int | None = None) -> TextProvider:
    if config_id is not None:
        config = get_enabled_provider_by_id(config_id, None, user_id=None)
    else:
        config = get_enabled_provider(ProviderType.text, user_id=None)
    if config is None:
        raise TextProviderNotConfiguredError("平台尚未配置启用的通用模型，请联系管理员在 /admin/providers 配置")
    return TextProvider(config)

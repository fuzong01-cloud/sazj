from enum import Enum
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    vision = "vision"
    text = "text"


class ModelConfigBase(BaseModel):
    provider_name: str = Field(min_length=1, max_length=80)
    provider_type: ProviderType
    base_url: str = Field(min_length=1)
    model_name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    supports_reasoning: bool = False
    max_context_tokens: int | None = Field(default=None, ge=256, le=2_000_000)
    max_output_tokens: int | None = Field(default=None, ge=16, le=65_536)


class ModelConfigCreate(ModelConfigBase):
    api_key: str = Field(min_length=1)


class ModelConfigUpdate(BaseModel):
    provider_name: str | None = Field(default=None, min_length=1, max_length=80)
    provider_type: ProviderType | None = None
    base_url: str | None = Field(default=None, min_length=1)
    api_key: str | None = Field(default=None, min_length=1)
    model_name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None
    supports_reasoning: bool | None = None
    max_context_tokens: int | None = Field(default=None, ge=256, le=2_000_000)
    max_output_tokens: int | None = Field(default=None, ge=16, le=65_536)


class ModelConfigStored(ModelConfigBase):
    id: int
    user_id: int | None = None
    api_key: str


class ModelConfigPublic(ModelConfigBase):
    id: int
    user_id: int | None = None
    api_key_masked: str


class ModelConfigChoice(BaseModel):
    id: int
    provider_name: str
    provider_type: ProviderType
    model_name: str
    supports_reasoning: bool = False
    max_context_tokens: int | None = None
    max_output_tokens: int | None = None


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


def to_public(config: ModelConfigStored) -> ModelConfigPublic:
    return ModelConfigPublic(
        id=config.id,
        user_id=config.user_id,
        provider_name=config.provider_name,
        provider_type=config.provider_type,
        base_url=config.base_url,
        model_name=config.model_name,
        enabled=config.enabled,
        supports_reasoning=config.supports_reasoning,
        max_context_tokens=config.max_context_tokens,
        max_output_tokens=config.max_output_tokens,
        api_key_masked=mask_api_key(config.api_key),
    )

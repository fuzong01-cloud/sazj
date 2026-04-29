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


class ModelConfigCreate(ModelConfigBase):
    api_key: str = Field(min_length=1)


class ModelConfigUpdate(BaseModel):
    provider_name: str | None = Field(default=None, min_length=1, max_length=80)
    provider_type: ProviderType | None = None
    base_url: str | None = Field(default=None, min_length=1)
    api_key: str | None = Field(default=None, min_length=1)
    model_name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None


class ModelConfigStored(ModelConfigBase):
    id: int
    api_key: str


class ModelConfigPublic(ModelConfigBase):
    id: int
    api_key_masked: str


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


def to_public(config: ModelConfigStored) -> ModelConfigPublic:
    return ModelConfigPublic(
        id=config.id,
        provider_name=config.provider_name,
        provider_type=config.provider_type,
        base_url=config.base_url,
        model_name=config.model_name,
        enabled=config.enabled,
        api_key_masked=mask_api_key(config.api_key),
    )

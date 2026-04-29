from itertools import count

from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigStored,
    ModelConfigUpdate,
    ProviderType,
)


_id_counter = count(1)
_configs: dict[int, ModelConfigStored] = {}


def list_configs() -> list[ModelConfigStored]:
    return list(_configs.values())


def get_config(config_id: int) -> ModelConfigStored | None:
    return _configs.get(config_id)


def create_config(payload: ModelConfigCreate) -> ModelConfigStored:
    config = ModelConfigStored(id=next(_id_counter), **payload.model_dump())
    _configs[config.id] = config
    return config


def update_config(config_id: int, payload: ModelConfigUpdate) -> ModelConfigStored | None:
    current = _configs.get(config_id)
    if current is None:
        return None

    values = current.model_dump()
    for key, value in payload.model_dump(exclude_unset=True).items():
        values[key] = value

    updated = ModelConfigStored(**values)
    _configs[config_id] = updated
    return updated


def delete_config(config_id: int) -> bool:
    return _configs.pop(config_id, None) is not None


def get_enabled_provider(provider_type: ProviderType) -> ModelConfigStored | None:
    for config in _configs.values():
        if config.provider_type == provider_type and config.enabled:
            return config
    return None

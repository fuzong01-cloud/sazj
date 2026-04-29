from fastapi import APIRouter, Query

from app.repositories.model_config_repository import list_enabled_configs
from app.schemas.model_config import ModelConfigChoice, ProviderType

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/enabled", response_model=list[ModelConfigChoice])
def list_enabled_providers(
    provider_type: ProviderType | None = Query(default=None),
) -> list[ModelConfigChoice]:
    return [
        ModelConfigChoice(
            id=config.id,
            provider_name=config.provider_name,
            provider_type=config.provider_type,
            model_name=config.model_name,
        )
        for config in list_enabled_configs(provider_type=provider_type, user_id=None)
    ]

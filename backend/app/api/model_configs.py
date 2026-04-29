from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import require_admin_header
from app.repositories.model_config_repository import (
    create_config,
    delete_config,
    get_config,
    list_configs,
    update_config,
)
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigPublic,
    ModelConfigUpdate,
    to_public,
)

router = APIRouter(
    prefix="/model-configs",
    tags=["model-configs"],
    dependencies=[Depends(require_admin_header)],
)


@router.get("", response_model=list[ModelConfigPublic])
def list_model_configs() -> list[ModelConfigPublic]:
    return [to_public(config) for config in list_configs(user_id=None)]


@router.post("", response_model=ModelConfigPublic, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreate,
) -> ModelConfigPublic:
    return to_public(create_config(payload, user_id=None))


@router.get("/{config_id}", response_model=ModelConfigPublic)
def get_model_config(
    config_id: int,
) -> ModelConfigPublic:
    config = get_config(config_id, user_id=None)
    if config is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return to_public(config)


@router.put("/{config_id}", response_model=ModelConfigPublic)
def update_model_config(
    config_id: int,
    payload: ModelConfigUpdate,
) -> ModelConfigPublic:
    config = update_config(config_id, payload, user_id=None)
    if config is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return to_public(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    config_id: int,
) -> None:
    if not delete_config(config_id, user_id=None):
        raise HTTPException(status_code=404, detail="模型配置不存在")

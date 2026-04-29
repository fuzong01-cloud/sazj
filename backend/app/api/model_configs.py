from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_optional_current_user
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
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/model-configs", tags=["model-configs"])


@router.get("", response_model=list[ModelConfigPublic])
def list_model_configs(
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> list[ModelConfigPublic]:
    return [to_public(config) for config in list_configs(user_id=current_user.id if current_user else None)]


@router.post("", response_model=ModelConfigPublic, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreate,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> ModelConfigPublic:
    return to_public(create_config(payload, user_id=current_user.id if current_user else None))


@router.get("/{config_id}", response_model=ModelConfigPublic)
def get_model_config(
    config_id: int,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> ModelConfigPublic:
    config = get_config(config_id, user_id=current_user.id if current_user else None)
    if config is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return to_public(config)


@router.put("/{config_id}", response_model=ModelConfigPublic)
def update_model_config(
    config_id: int,
    payload: ModelConfigUpdate,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> ModelConfigPublic:
    config = update_config(config_id, payload, user_id=current_user.id if current_user else None)
    if config is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return to_public(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    config_id: int,
    current_user: UserPublic | None = Depends(get_optional_current_user),
) -> None:
    if not delete_config(config_id, user_id=current_user.id if current_user else None):
        raise HTTPException(status_code=404, detail="模型配置不存在")

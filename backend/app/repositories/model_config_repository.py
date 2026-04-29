from sqlalchemy import select

from app.core.crypto import decrypt_provider_secret, encrypt_provider_secret
from app.db.session import SessionLocal
from app.models.model_config import ModelConfig
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigStored,
    ModelConfigUpdate,
    ProviderType,
)


def _to_schema(row: ModelConfig) -> ModelConfigStored:
    return ModelConfigStored(
        id=row.id,
        user_id=row.user_id,
        provider_name=row.provider_name,
        provider_type=ProviderType(row.provider_type),
        base_url=row.base_url,
        api_key=decrypt_provider_secret(row.api_key),
        model_name=row.model_name,
        enabled=row.enabled,
    )


def list_configs(user_id: int | None = None) -> list[ModelConfigStored]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(ModelConfig).where(_user_filter(user_id)).order_by(ModelConfig.id.asc())
        ).all()
        return [_to_schema(row) for row in rows]


def get_config(config_id: int, user_id: int | None = None) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if row is not None and row.user_id != user_id:
            return None
        return _to_schema(row) if row else None


def create_config(payload: ModelConfigCreate, user_id: int | None = None) -> ModelConfigStored:
    with SessionLocal() as session:
        values = payload.model_dump(mode="json")
        values["user_id"] = user_id
        values["api_key"] = encrypt_provider_secret(values["api_key"])
        row = ModelConfig(**values)
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_schema(row)


def update_config(
    config_id: int,
    payload: ModelConfigUpdate,
    user_id: int | None = None,
) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if row is None or row.user_id != user_id:
            return None

        for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
            if key == "api_key":
                value = encrypt_provider_secret(value)
            setattr(row, key, value)

        session.commit()
        session.refresh(row)
        return _to_schema(row)


def delete_config(config_id: int, user_id: int | None = None) -> bool:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if row is None or row.user_id != user_id:
            return False

        session.delete(row)
        session.commit()
        return True


def get_enabled_provider(
    provider_type: ProviderType,
    user_id: int | None = None,
) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.scalars(
            select(ModelConfig)
            .where(
                _user_filter(user_id),
                ModelConfig.provider_type == provider_type.value,
                ModelConfig.enabled.is_(True),
            )
            .order_by(ModelConfig.id.asc())
        ).first()
        return _to_schema(row) if row else None


def list_enabled_configs(
    provider_type: ProviderType | None = None,
    user_id: int | None = None,
) -> list[ModelConfigStored]:
    filters = [_user_filter(user_id), ModelConfig.enabled.is_(True)]
    if provider_type is not None:
        filters.append(ModelConfig.provider_type == provider_type.value)

    with SessionLocal() as session:
        rows = session.scalars(
            select(ModelConfig)
            .where(*filters)
            .order_by(ModelConfig.provider_type.asc(), ModelConfig.id.asc())
        ).all()
        return [_to_schema(row) for row in rows]


def get_enabled_provider_by_id(
    config_id: int,
    provider_type: ProviderType,
    user_id: int | None = None,
) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if (
            row is None
            or row.user_id != user_id
            or row.provider_type != provider_type.value
            or not row.enabled
        ):
            return None
        return _to_schema(row)


def _user_filter(user_id: int | None):
    if user_id is None:
        return ModelConfig.user_id.is_(None)
    return ModelConfig.user_id == user_id

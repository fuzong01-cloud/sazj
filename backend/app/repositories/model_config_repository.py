from sqlalchemy import select

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
        provider_name=row.provider_name,
        provider_type=ProviderType(row.provider_type),
        base_url=row.base_url,
        api_key=row.api_key,
        model_name=row.model_name,
        enabled=row.enabled,
    )


def list_configs() -> list[ModelConfigStored]:
    with SessionLocal() as session:
        rows = session.scalars(select(ModelConfig).order_by(ModelConfig.id.asc())).all()
        return [_to_schema(row) for row in rows]


def get_config(config_id: int) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        return _to_schema(row) if row else None


def create_config(payload: ModelConfigCreate) -> ModelConfigStored:
    with SessionLocal() as session:
        row = ModelConfig(**payload.model_dump(mode="json"))
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_schema(row)


def update_config(config_id: int, payload: ModelConfigUpdate) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if row is None:
            return None

        for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(row, key, value)

        session.commit()
        session.refresh(row)
        return _to_schema(row)


def delete_config(config_id: int) -> bool:
    with SessionLocal() as session:
        row = session.get(ModelConfig, config_id)
        if row is None:
            return False

        session.delete(row)
        session.commit()
        return True


def get_enabled_provider(provider_type: ProviderType) -> ModelConfigStored | None:
    with SessionLocal() as session:
        row = session.scalars(
            select(ModelConfig)
            .where(
                ModelConfig.provider_type == provider_type.value,
                ModelConfig.enabled.is_(True),
            )
            .order_by(ModelConfig.id.asc())
        ).first()
        return _to_schema(row) if row else None

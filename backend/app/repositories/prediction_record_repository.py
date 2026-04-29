from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.prediction_record import PredictionRecord
from app.schemas.prediction_record import PredictionRecordCreate, PredictionRecordStored


def _to_schema(row: PredictionRecord) -> PredictionRecordStored:
    return PredictionRecordStored(
        id=row.id,
        user_id=row.user_id,
        provider_name=row.provider_name,
        model_name=row.model_name,
        disease_name=row.disease_name,
        risk_level=row.risk_level,
        confidence=row.confidence,
        confidence_percent=row.confidence_percent,
        summary=row.summary,
        suggestions=row.suggestions or [],
        raw_text=row.raw_text,
        image_filename=row.image_filename,
        image_content_type=row.image_content_type,
        created_at=row.created_at,
    )


def create_prediction_record(payload: PredictionRecordCreate) -> PredictionRecordStored:
    with SessionLocal() as session:
        row = PredictionRecord(**payload.model_dump(mode="json"))
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_schema(row)


def get_prediction_record(record_id: int, user_id: int | None = None) -> PredictionRecordStored | None:
    with SessionLocal() as session:
        row = session.get(PredictionRecord, record_id)
        if row is not None and user_id is not None and row.user_id != user_id:
            return None
        return _to_schema(row) if row else None


def list_prediction_records(limit: int = 20) -> list[PredictionRecordStored]:
    safe_limit = max(1, min(limit, 100))
    with SessionLocal() as session:
        rows = session.scalars(
            select(PredictionRecord)
            .order_by(PredictionRecord.created_at.desc(), PredictionRecord.id.desc())
            .limit(safe_limit)
        ).all()
        return [_to_schema(row) for row in rows]


def count_prediction_records(user_id: int | None = None) -> int:
    with SessionLocal() as session:
        statement = select(func.count(PredictionRecord.id))
        if user_id is not None:
            statement = statement.where(PredictionRecord.user_id == user_id)
        return session.scalar(statement) or 0


def list_prediction_records_page(
    limit: int = 20,
    offset: int = 0,
    user_id: int | None = None,
) -> list[PredictionRecordStored]:
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    with SessionLocal() as session:
        statement = select(PredictionRecord)
        if user_id is not None:
            statement = statement.where(PredictionRecord.user_id == user_id)
        rows = session.scalars(
            statement.order_by(PredictionRecord.created_at.desc(), PredictionRecord.id.desc())
            .offset(safe_offset)
            .limit(safe_limit)
        ).all()
        return [_to_schema(row) for row in rows]


def delete_prediction_record(record_id: int, user_id: int | None = None) -> bool:
    with SessionLocal() as session:
        row = session.get(PredictionRecord, record_id)
        if row is None:
            return False
        if user_id is not None and row.user_id != user_id:
            return False
        session.delete(row)
        session.commit()
        return True

from fastapi import APIRouter, HTTPException, Query

from app.repositories.prediction_record_repository import (
    get_prediction_record,
    list_prediction_records,
)
from app.schemas.prediction_record import PredictionRecordStored

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[PredictionRecordStored])
def list_history(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[PredictionRecordStored]:
    return list_prediction_records(limit=limit)


@router.get("/{record_id}", response_model=PredictionRecordStored)
def get_history_record(record_id: int) -> PredictionRecordStored:
    record = get_prediction_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="识别记录不存在")
    return record

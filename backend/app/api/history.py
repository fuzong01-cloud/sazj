from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.prediction_record_repository import (
    count_prediction_records,
    delete_prediction_record,
    get_prediction_record,
    list_prediction_records_page,
)
from app.schemas.prediction_record import PredictionRecordPage, PredictionRecordStored

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=PredictionRecordPage)
def list_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PredictionRecordPage:
    return PredictionRecordPage(
        items=list_prediction_records_page(limit=limit, offset=offset),
        total=count_prediction_records(),
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=PredictionRecordStored)
def get_history_record(record_id: int) -> PredictionRecordStored:
    record = get_prediction_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="识别记录不存在")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_record(record_id: int) -> None:
    if not delete_prediction_record(record_id):
        raise HTTPException(status_code=404, detail="识别记录不存在")

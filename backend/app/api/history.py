from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth import get_current_user
from app.repositories.prediction_record_repository import (
    count_prediction_records,
    delete_prediction_record,
    get_prediction_record,
    list_prediction_records_page,
)
from app.schemas.prediction_record import PredictionRecordPage, PredictionRecordStored
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=PredictionRecordPage)
def list_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPublic = Depends(get_current_user),
) -> PredictionRecordPage:
    user_id = current_user.id
    return PredictionRecordPage(
        items=list_prediction_records_page(limit=limit, offset=offset, user_id=user_id),
        total=count_prediction_records(user_id=user_id),
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=PredictionRecordStored)
def get_history_record(
    record_id: int,
    current_user: UserPublic = Depends(get_current_user),
) -> PredictionRecordStored:
    record = get_prediction_record(record_id, user_id=current_user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="识别记录不存在")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_record(
    record_id: int,
    current_user: UserPublic = Depends(get_current_user),
) -> None:
    if not delete_prediction_record(record_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="识别记录不存在")

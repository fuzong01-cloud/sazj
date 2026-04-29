from fastapi import APIRouter

from app.schemas.common import ModelStatusResponse
from app.services.model_registry import get_model_status

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/status", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    return get_model_status()

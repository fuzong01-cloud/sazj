from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        ok=True,
        app=settings.app_name,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
    )

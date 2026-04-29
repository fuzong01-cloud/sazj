from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool
    app: str
    environment: str
    timestamp: datetime


class ModelStatusResponse(BaseModel):
    ok: bool
    model_path: str
    exists: bool
    size_bytes: int | None = None
    message: str

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRecordCreate(BaseModel):
    provider_name: str = Field(min_length=1, max_length=80)
    model_name: str = Field(min_length=1, max_length=120)
    disease_name: str = Field(min_length=1, max_length=120)
    risk_level: str = Field(min_length=1, max_length=40)
    confidence: float | None = None
    confidence_percent: float | None = None
    summary: str = Field(min_length=1)
    suggestions: list[str] = Field(default_factory=list)
    raw_text: str | None = None
    image_filename: str | None = Field(default=None, max_length=255)
    image_content_type: str | None = Field(default=None, max_length=80)


class PredictionRecordStored(PredictionRecordCreate):
    id: int
    created_at: datetime


class PredictionRecordPage(BaseModel):
    items: list[PredictionRecordStored]
    total: int
    limit: int
    offset: int

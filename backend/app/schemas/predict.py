from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    ok: bool = True
    record_id: int | None = None
    provider_name: str
    model_name: str
    disease_name: str = Field(default="待确认")
    confidence: float | None = None
    confidence_percent: float | None = None
    risk_level: str = Field(default="待确认")
    summary: str
    suggestions: list[str] = Field(default_factory=list)
    raw_text: str | None = None

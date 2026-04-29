from pydantic import BaseModel, Field

from app.schemas.weather import WeatherContext


class PredictResponse(BaseModel):
    ok: bool = True
    record_id: int | None = None
    conversation_id: int | None = None
    provider_name: str
    model_name: str
    disease_name: str = Field(default="模型回复")
    confidence: float | None = None
    confidence_percent: float | None = None
    risk_level: str = Field(default="未结构化")
    summary: str
    suggestions: list[str] = Field(default_factory=list)
    content: str | None = None
    raw_text: str | None = None
    weather: WeatherContext | None = None

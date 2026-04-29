from pydantic import BaseModel, Field


class AdviceRequest(BaseModel):
    disease_name: str = Field(min_length=1)
    risk_level: str | None = None
    context: str | None = None


class AdviceResponse(BaseModel):
    ok: bool = True
    provider_name: str
    model_name: str
    advice: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    context: str | None = None


class ChatResponse(BaseModel):
    ok: bool = True
    provider_name: str
    model_name: str
    answer: str

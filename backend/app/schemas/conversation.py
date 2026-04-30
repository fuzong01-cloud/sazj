from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationMessageCreate(BaseModel):
    conversation_id: int
    user_id: int
    role: str = Field(min_length=1, max_length=20)
    message_type: str = Field(default="text", min_length=1, max_length=20)
    content: str = ""
    provider_name: str | None = None
    model_name: str | None = None
    payload: dict[str, Any] | None = None


class ConversationMessageStored(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    role: str
    message_type: str
    content: str
    provider_name: str | None = None
    model_name: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime


class ConversationStored(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class ConversationDetail(ConversationStored):
    messages: list[ConversationMessageStored]


class ConversationPage(BaseModel):
    items: list[ConversationStored]
    total: int
    limit: int
    offset: int

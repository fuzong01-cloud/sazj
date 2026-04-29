from datetime import datetime, timezone

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.conversation import Conversation, ConversationMessage
from app.schemas.conversation import (
    ConversationDetail,
    ConversationMessageCreate,
    ConversationMessageStored,
    ConversationStored,
)


def create_conversation(user_id: int, title: str) -> ConversationStored:
    with SessionLocal() as session:
        row = Conversation(user_id=user_id, title=_normalize_title(title))
        session.add(row)
        session.commit()
        session.refresh(row)
        return _conversation_to_schema(row)


def ensure_conversation(user_id: int, conversation_id: int | None, title: str) -> ConversationStored:
    if conversation_id is not None:
        existing = get_conversation(conversation_id, user_id)
        if existing is not None:
            return existing
    return create_conversation(user_id=user_id, title=title)


def add_message(payload: ConversationMessageCreate) -> ConversationMessageStored:
    with SessionLocal() as session:
        row = ConversationMessage(**payload.model_dump(mode="json"))
        session.add(row)
        conversation = session.get(Conversation, payload.conversation_id)
        if conversation is not None:
            conversation.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
        return _message_to_schema(row)


def get_conversation(conversation_id: int, user_id: int) -> ConversationStored | None:
    with SessionLocal() as session:
        row = session.get(Conversation, conversation_id)
        if row is None or row.user_id != user_id:
            return None
        return _conversation_to_schema(row)


def get_conversation_detail(conversation_id: int, user_id: int) -> ConversationDetail | None:
    with SessionLocal() as session:
        row = session.get(Conversation, conversation_id)
        if row is None or row.user_id != user_id:
            return None
        messages = session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        ).all()
        return ConversationDetail(
            **_conversation_to_schema(row).model_dump(),
            messages=[_message_to_schema(message) for message in messages],
        )


def count_conversations(user_id: int) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        ) or 0


def list_conversations_page(user_id: int, limit: int, offset: int) -> list[ConversationStored]:
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    with SessionLocal() as session:
        rows = session.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .offset(safe_offset)
            .limit(safe_limit)
        ).all()
        return [_conversation_to_schema(row) for row in rows]


def delete_conversation(conversation_id: int, user_id: int) -> bool:
    with SessionLocal() as session:
        row = session.get(Conversation, conversation_id)
        if row is None or row.user_id != user_id:
            return False
        messages = session.scalars(
            select(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)
        ).all()
        for message in messages:
            session.delete(message)
        session.delete(row)
        session.commit()
        return True


def _conversation_to_schema(row: Conversation) -> ConversationStored:
    return ConversationStored(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _message_to_schema(row: ConversationMessage) -> ConversationMessageStored:
    return ConversationMessageStored(
        id=row.id,
        conversation_id=row.conversation_id,
        user_id=row.user_id,
        role=row.role,
        message_type=row.message_type,
        content=row.content,
        provider_name=row.provider_name,
        model_name=row.model_name,
        payload=row.payload,
        created_at=row.created_at,
    )


def _normalize_title(value: str) -> str:
    title = " ".join((value or "").strip().split())
    if not title:
        return "新会话"
    return title[:20]

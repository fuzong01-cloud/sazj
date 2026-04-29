from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth import UserCreate, UserPublic


def _to_public(row: User) -> UserPublic:
    return UserPublic(
        id=row.id,
        username=row.username,
        enabled=row.enabled,
        created_at=row.created_at,
        last_login_at=row.last_login_at,
    )


def get_user_by_id(user_id: int) -> UserPublic | None:
    with SessionLocal() as session:
        row = session.get(User, user_id)
        return _to_public(row) if row else None


def get_user_row_by_username(username: str) -> User | None:
    with SessionLocal() as session:
        return session.scalars(select(User).where(User.username == username)).first()


def get_user_public_by_username(username: str) -> UserPublic | None:
    row = get_user_row_by_username(username)
    return _to_public(row) if row else None


def create_user(payload: UserCreate) -> UserPublic:
    with SessionLocal() as session:
        row = User(
            username=payload.username,
            password_hash=hash_password(payload.password),
            enabled=True,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_public(row)


def mark_user_login(user_id: int) -> UserPublic | None:
    with SessionLocal() as session:
        row = session.get(User, user_id)
        if row is None:
            return None
        row.last_login_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
        return _to_public(row)

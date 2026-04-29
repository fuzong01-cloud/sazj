from fastapi import Header, HTTPException, Query, status

from app.core.config import settings


def verify_admin_token(token: str | None) -> None:
    if not token or token != settings.admin_webui_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员令牌无效",
        )


def require_admin_header(x_admin_token: str | None = Header(default=None)) -> None:
    verify_admin_token(x_admin_token)


def require_admin_query(token: str | None = Query(default=None)) -> str:
    verify_admin_token(token)
    return token or ""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.security import AuthError, create_access_token, decode_access_token, verify_password
from app.repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_user_public_by_username,
    get_user_row_by_username,
    mark_user_login,
)
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(authorization: str | None = Header(default=None)) -> UserPublic:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少访问令牌")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (AuthError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = get_user_by_id(user_id)
    if user is None or not user.enabled:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> TokenResponse:
    if get_user_public_by_username(payload.username):
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = create_user(payload)
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin) -> TokenResponse:
    row = get_user_row_by_username(payload.username)
    if row is None or not verify_password(payload.password, row.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not row.enabled:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    user = mark_user_login(row.id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserPublic)
def read_me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.security import AuthError, create_access_token, decode_access_token, verify_password
from app.repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_user_public_by_username,
    get_user_row_by_id,
    get_user_row_by_username,
    mark_user_login,
    update_user_password,
    update_user_profile,
)
from app.schemas.auth import PasswordChangeRequest, TokenResponse, UserCreate, UserLogin, UserProfileUpdate, UserPublic

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


def get_optional_current_user(authorization: str | None = Header(default=None)) -> UserPublic | None:
    if not authorization:
        return None
    return get_current_user(authorization)


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


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserProfileUpdate,
    current_user: UserPublic = Depends(get_current_user),
) -> UserPublic:
    if payload.username and payload.username != current_user.username:
        existing = get_user_public_by_username(payload.username)
        if existing is not None and existing.id != current_user.id:
            raise HTTPException(status_code=409, detail="用户名已存在")

    user = update_user_profile(current_user.id, payload)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> None:
    row = get_user_row_by_id(current_user.id)
    if row is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(payload.current_password, row.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    if not update_user_password(current_user.id, payload.new_password):
        raise HTTPException(status_code=404, detail="用户不存在")


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserPublic = Depends(get_current_user),
) -> UserPublic:
    content_type = file.content_type or ""
    if content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="头像仅支持 PNG、JPG、WebP 图片")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="头像文件不能为空")
    if len(data) > min(settings.max_upload_bytes, 2 * 1024 * 1024):
        raise HTTPException(status_code=400, detail="头像文件不能超过 2MB")

    suffix = _avatar_suffix(file.filename or "", content_type)
    try:
        avatar_dir = settings.upload_dir / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        filename = f"user_{current_user.id}_{uuid4().hex}{suffix}"
        target = avatar_dir / filename
        target.write_bytes(data)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"头像目录不可写：{exc}") from exc

    user = update_user_profile(
        current_user.id,
        UserProfileUpdate(avatar_url=f"/uploads/avatars/{filename}"),
    )
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def _avatar_suffix(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return suffix
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }.get(content_type, ".png")

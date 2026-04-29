import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


class AuthError(RuntimeError):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 210_000)
    return f"pbkdf2_sha256$210000${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(payload: dict[str, Any]) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token_payload = {
        **payload,
        "exp": int(expires_at.timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64_json(header)}.{_b64_json(token_payload)}"
    signature = _sign(signing_input)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("无效的访问令牌") from exc

    signing_input = f"{header_part}.{payload_part}"
    if not hmac.compare_digest(_sign(signing_input), signature):
        raise AuthError("访问令牌签名无效")

    payload = _b64_decode_json(payload_part)
    expires_at = int(payload.get("exp", 0))
    if expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise AuthError("访问令牌已过期")

    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        value.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64_bytes(digest)


def _b64_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _b64_bytes(raw)


def _b64_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64_decode_json(value: str) -> dict[str, Any]:
    padded = value + "=" * (-len(value) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("访问令牌载荷无效") from exc
    if not isinstance(data, dict):
        raise AuthError("访问令牌载荷无效")
    return data

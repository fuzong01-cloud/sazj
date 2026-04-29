import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


ENCRYPTED_PREFIX = "fernet:v1:"


class CryptoError(RuntimeError):
    pass


def encrypt_provider_secret(value: str) -> str:
    if not value:
        raise CryptoError("待加密内容不能为空")
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_provider_secret(value: str) -> str:
    if not value:
        return value
    if not is_encrypted_provider_secret(value):
        return value

    token = value.removeprefix(ENCRYPTED_PREFIX)
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise CryptoError("Provider API Key 解密失败，请检查 PROVIDER_SECRET_KEY 是否正确") from exc


def is_encrypted_provider_secret(value: str) -> bool:
    return value.startswith(ENCRYPTED_PREFIX)


def _fernet() -> Fernet:
    secret = settings.provider_secret_key.strip()
    if len(secret) < 32:
        raise CryptoError("PROVIDER_SECRET_KEY 至少需要 32 个字符")

    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

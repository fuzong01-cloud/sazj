from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _split_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "薯安智检 API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sazj",
    )
    auto_create_tables: bool = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "2"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "1"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    model_path: Path = Path(os.getenv("MODEL_PATH", str(REPO_ROOT / "final_model.h5")))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", str(REPO_ROOT / "uploads")))
    log_dir: Path = Path(os.getenv("LOG_DIR", str(REPO_ROOT / "logs")))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_max_bytes: int = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "3"))
    provider_secret_key: str = os.getenv(
        "PROVIDER_SECRET_KEY",
        "development-provider-secret-key-change-me",
    )
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))
    frontend_origins: list[str] = None

    def __post_init__(self) -> None:
        origins = os.getenv(
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:5173,http://localhost:5173",
        )
        object.__setattr__(self, "frontend_origins", _split_origins(origins))
        if not self.model_path.is_absolute():
            object.__setattr__(self, "model_path", (BACKEND_DIR / self.model_path).resolve())
        if not self.upload_dir.is_absolute():
            object.__setattr__(self, "upload_dir", (BACKEND_DIR / self.upload_dir).resolve())
        if not self.log_dir.is_absolute():
            object.__setattr__(self, "log_dir", (BACKEND_DIR / self.log_dir).resolve())


settings = Settings()

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


def _split_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "薯安智检 API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    model_path: Path = Path(os.getenv("MODEL_PATH", str(REPO_ROOT / "final_model.h5")))
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


settings = Settings()

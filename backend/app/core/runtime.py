import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


def ensure_runtime_dirs() -> None:
    for path in (settings.upload_dir, settings.log_dir):
        Path(path).mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    ensure_runtime_dirs()

    log_file = settings.log_dir / "backend.log"
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    if not _has_file_handler(logger, log_file):
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                )
            )
            logger.addHandler(file_handler)
        except OSError as exc:
            logging.getLogger("app").warning("file logging disabled: %s", exc)

    logging.getLogger("app").info(
        "runtime initialized upload_dir=%s log_dir=%s",
        settings.upload_dir,
        settings.log_dir,
    )


def _has_file_handler(logger: logging.Logger, log_file: Path) -> bool:
    target = log_file.resolve()
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename).resolve() == target:
            return True
    return False

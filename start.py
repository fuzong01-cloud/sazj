from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_SQLITE_URL = f"sqlite:///{(BACKEND_DIR / 'sazj.sqlite3').as_posix()}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动薯安智检 FastAPI 后端")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--no-reload", action="store_true", help="关闭开发期热重载")
    parser.add_argument("--database-url", default=None, help="覆盖 DATABASE_URL")
    return parser.parse_args()


def configure_environment(database_url: str | None) -> None:
    os.environ.setdefault("DATABASE_URL", database_url or DEFAULT_SQLITE_URL)
    os.environ.setdefault("AUTO_CREATE_TABLES", "true")
    os.environ.setdefault("SQLITE_JOURNAL_MODE", "OFF")
    os.environ.setdefault("UPLOAD_DIR", str((ROOT_DIR / "uploads").resolve()))
    os.environ.setdefault("LOG_DIR", str((ROOT_DIR / "logs").resolve()))
    os.environ.setdefault(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )


def main() -> None:
    args = parse_args()
    configure_environment(args.database_url)

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("未安装 uvicorn，请先运行：python build.py --skip-frontend") from exc

    print(f"DATABASE_URL={os.environ['DATABASE_URL']}")
    print(f"UPLOAD_DIR={os.environ['UPLOAD_DIR']}")
    print(f"LOG_DIR={os.environ['LOG_DIR']}")
    print(f"API 文档：http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        app_dir=str(BACKEND_DIR),
    )


if __name__ == "__main__":
    main()

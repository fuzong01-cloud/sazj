from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建薯安智检本地开发环境")
    parser.add_argument("--skip-backend", action="store_true", help="跳过后端依赖安装")
    parser.add_argument("--skip-frontend", action="store_true", help="跳过前端依赖安装和构建")
    parser.add_argument("--no-frontend-build", action="store_true", help="只安装前端依赖，不执行 npm run build")
    return parser.parse_args()


def venv_python() -> str:
    candidates = [
        ROOT_DIR / ".venv" / "Scripts" / "python.exe",
        ROOT_DIR / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def npm_command() -> str:
    command = shutil.which("npm.cmd") or shutil.which("npm")
    if not command:
        raise SystemExit("未找到 npm，请先安装 Node.js。")
    return command


def run(command: list[str], cwd: Path) -> None:
    print(f"> {' '.join(command)}")
    subprocess.check_call(command, cwd=str(cwd))


def main() -> None:
    args = parse_args()

    if not args.skip_backend:
        run([venv_python(), "-m", "pip", "install", "-r", "requirements.txt"], BACKEND_DIR)

    if not args.skip_frontend:
        npm = npm_command()
        run([npm, "install"], FRONTEND_DIR)
        if not args.no_frontend_build:
            run([npm, "run", "build"], FRONTEND_DIR)

    print("构建完成。启动后端请运行：python start.py")


if __name__ == "__main__":
    main()

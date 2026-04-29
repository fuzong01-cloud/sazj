from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def npm_command() -> str:
    command = shutil.which("npm.cmd") or shutil.which("npm")
    if not command:
        raise SystemExit("未找到 npm，请先安装 Node.js。")
    return command


def main() -> None:
    print("前端开发服务：http://127.0.0.1:5173")
    subprocess.check_call([npm_command(), "run", "dev"], cwd=str(FRONTEND_DIR))


if __name__ == "__main__":
    main()

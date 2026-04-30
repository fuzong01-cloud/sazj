from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / "logs"
DEFAULT_REMOTE = "origin"
DEFAULT_BRANCH = "main"
DEFAULT_REPO_URL = "https://github.com/fuzong01-cloud/sazj.git"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 GitHub 更新并安全同步到本地部署目录")
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="Git remote 名称，默认 origin")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="远程分支，默认 main")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="期望的 GitHub 仓库地址")
    parser.add_argument("--check-only", action="store_true", help="只检查是否有更新，不执行拉取")
    parser.add_argument("--skip-build", action="store_true", help="只更新代码，不安装依赖或构建前端")
    parser.add_argument("--skip-frontend-build", action="store_true", help="跳过前端 npm install/build")
    parser.add_argument("--restart-service", action="store_true", help="更新成功后重启 Windows 服务")
    parser.add_argument("--service-name", default="sazj-backend", help="需要重启的 Windows 服务名")
    return parser.parse_args()


def log(message: str) -> None:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "auto_update.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    log("> " + " ".join(command))
    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        text=True,
        capture_output=True,
    )
    if result.stdout.strip():
        log(result.stdout.strip())
    if result.stderr.strip():
        log(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"命令执行失败：{' '.join(command)}")
    return result


def ensure_git() -> None:
    if not (ROOT_DIR / ".git").exists():
        raise RuntimeError(f"{ROOT_DIR} 不是 Git 仓库，无法自动更新")
    if shutil.which("git") is None:
        raise RuntimeError("未找到 git，请先在服务器安装 Git for Windows 并加入 PATH")


def ensure_remote(remote: str, repo_url: str) -> None:
    result = run(["git", "remote", "get-url", remote], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"未找到 remote：{remote}。请先执行 git remote add {remote} {repo_url}")

    current_url = result.stdout.strip()
    if current_url != repo_url:
        log(f"警告：当前 {remote} 地址为 {current_url}，期望地址为 {repo_url}")


def ensure_clean_worktree() -> None:
    result = run(["git", "status", "--porcelain"])
    if result.stdout.strip():
        raise RuntimeError(
            "检测到本地工作区存在未提交改动，已停止自动更新。"
            "请先提交、丢弃或手动处理这些改动。"
        )


def current_commit(ref: str) -> str:
    return run(["git", "rev-parse", ref]).stdout.strip()


def has_updates(remote: str, branch: str) -> bool:
    local_head = current_commit("HEAD")
    remote_head = current_commit(f"{remote}/{branch}")
    log(f"本地 HEAD：{local_head}")
    log(f"远程 HEAD：{remote_head}")
    return local_head != remote_head


def ensure_fast_forward_possible(remote: str, branch: str) -> None:
    result = run(["git", "merge-base", "--is-ancestor", "HEAD", f"{remote}/{branch}"], check=False)
    if result.returncode != 0:
        raise RuntimeError("本地分支与远程分支已经分叉，无法安全 fast-forward，请人工处理")


def pull_updates(remote: str, branch: str) -> None:
    run(["git", "pull", "--ff-only", remote, branch])


def build_project(skip_frontend: bool) -> None:
    build_command = [sys.executable, "build.py"]
    if skip_frontend:
        build_command.append("--skip-frontend")
    run(build_command)


def restart_service(service_name: str) -> None:
    if sys.platform != "win32":
        log("当前不是 Windows，跳过服务重启")
        return
    result = run(["powershell", "-NoProfile", "-Command", f"Restart-Service -Name '{service_name}'"], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"重启服务失败：{service_name}。请确认服务已通过 NSSM 注册")


def main() -> int:
    args = parse_args()
    try:
        ensure_git()
        ensure_remote(args.remote, args.repo_url)
        ensure_clean_worktree()
        run(["git", "fetch", args.remote, args.branch])

        if not has_updates(args.remote, args.branch):
            log("未发现远程更新")
            return 0

        log("发现远程更新")
        if args.check_only:
            log("check-only 模式，不执行更新")
            return 0

        ensure_fast_forward_possible(args.remote, args.branch)
        pull_updates(args.remote, args.branch)

        if not args.skip_build:
            build_project(skip_frontend=args.skip_frontend_build)

        if args.restart_service:
            restart_service(args.service_name)

        log("自动更新完成")
        return 0
    except Exception as exc:
        log(f"自动更新失败：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

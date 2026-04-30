# Windows Server 自动更新说明

本文档用于在服务器上定时检查 GitHub 仓库更新，并把 `https://github.com/fuzong01-cloud/sazj` 的新版本同步到本地部署目录。

当前自动更新脚本为根目录：

```text
C:\sazj\auto_update.py
```

## 设计原则

- 只从 `origin/main` 更新。
- 只允许 fast-forward 更新。
- 如果服务器本地代码有未提交改动，自动停止，不覆盖本地修改。
- 不删除 `.env`、SQLite 数据库、`uploads`、`logs`、`frontend/node_modules` 等运行数据。
- 更新后可自动执行 `python build.py` 安装依赖并构建前端。
- 更新成功后可重启 NSSM 注册的后端服务。

## 前置条件

服务器需要安装：

- Git for Windows
- Python
- Node.js
- 已经完成一次项目部署

确认当前目录是从 GitHub 克隆：

```powershell
cd C:\sazj
git remote -v
```

预期看到：

```text
origin  https://github.com/fuzong01-cloud/sazj.git (fetch)
origin  https://github.com/fuzong01-cloud/sazj.git (push)
```

如果服务器不是通过 Git 克隆得到的项目目录，建议先备份 `.env`、`backend\sazj.sqlite3`、`uploads` 和 `logs`，再重新 clone 仓库。

## 手动检查更新

只检查是否有更新，不拉取：

```powershell
cd C:\sazj
.\venv\Scripts\python.exe auto_update.py --check-only
```

发现更新后手动执行：

```powershell
.\venv\Scripts\python.exe auto_update.py --restart-service --service-name sazj-backend
```

如果只想更新后端依赖，不构建前端：

```powershell
.\venv\Scripts\python.exe auto_update.py --skip-frontend-build --restart-service --service-name sazj-backend
```

如果只拉代码，不安装依赖、不构建、不重启：

```powershell
.\venv\Scripts\python.exe auto_update.py --skip-build
```

## 使用 Windows 任务计划程序定时更新

推荐用任务计划程序每 5 到 10 分钟检查一次。

以管理员身份打开 PowerShell：

```powershell
$action = New-ScheduledTaskAction `
  -Execute "C:\sazj\venv\Scripts\python.exe" `
  -Argument "C:\sazj\auto_update.py --restart-service --service-name sazj-backend" `
  -WorkingDirectory "C:\sazj"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
  -TaskName "sazj-auto-update" `
  -Action $action `
  -Trigger $trigger `
  -Description "定时检查 GitHub 更新并自动更新薯安智检" `
  -RunLevel Highest
```

查看任务：

```powershell
Get-ScheduledTask -TaskName sazj-auto-update
```

手动触发一次：

```powershell
Start-ScheduledTask -TaskName sazj-auto-update
```

删除任务：

```powershell
Unregister-ScheduledTask -TaskName sazj-auto-update -Confirm:$false
```

## 日志位置

自动更新日志写入：

```text
C:\sazj\logs\auto_update.log
```

查看最近日志：

```powershell
Get-Content C:\sazj\logs\auto_update.log -Tail 80
```

## 常见问题

提示“本地工作区存在未提交改动”：

- 说明服务器代码被手动改过。
- 自动更新不会覆盖这些改动。
- 请先人工确认 `git status`，再决定提交、丢弃或重新部署。

提示“本地分支与远程分支已经分叉”：

- 说明服务器本地提交和 GitHub 最新提交不在同一条 fast-forward 链上。
- 自动更新会停止，避免误合并。
- 请人工处理 Git 分支。

提示找不到 Git：

- 安装 Git for Windows。
- 确认 `git.exe` 已加入系统 PATH。
- 重新打开 PowerShell 后再运行脚本。

更新后服务没有重启：

- 确认后端服务名是否为 `sazj-backend`。
- 如果服务名不同，运行脚本时指定：

```powershell
.\venv\Scripts\python.exe auto_update.py --restart-service --service-name 你的服务名
```

前端页面没有变化：

- 确认自动更新没有使用 `--skip-frontend-build`。
- 确认 `frontend\dist` 已重新生成。
- 如果使用 Caddy/Nginx/IIS，刷新浏览器缓存后再试。

## 注意事项

自动更新适合一个月演示部署和低频团队更新。进入正式生产后，建议改为手动发布流程或 CI/CD 流程，避免未验收代码直接进入服务器。

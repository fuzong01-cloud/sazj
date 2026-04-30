# Windows Server 轻量云服务器部署指南

本文档是当前项目的默认部署方案，目标环境为 Windows Server、2 核 CPU、2GB 内存、40GB 存储、一个月演示周期。

服务器只运行 Vue 静态页面、FastAPI 后端、SQLite 数据库文件、上传文件存储和日志记录。不要在服务器上训练 CNN，不要运行本地大模型，不要把 `final_model.h5` 接回新系统主线。

## 推荐目录

```text
C:\sazj\
  backend\
  frontend\
  deploy\
  logs\
  uploads\
  .env
```

## 安装 Python

1. 从 Python 官网安装 Python 3.11 或 3.12 Windows 版。
2. 安装时勾选 `Add python.exe to PATH`。
3. 验证：

```powershell
python --version
pip --version
```

## 安装 Node.js

1. 安装 Node.js LTS Windows 版。
2. 验证：

```powershell
node --version
npm --version
```

## 数据库选择

当前一个月轻量演示默认使用 SQLite，不需要额外安装 PostgreSQL。数据库文件建议放在：

```text
C:\sazj\backend\sazj.sqlite3
```

如果后续进入长期运行或多人并发阶段，再单独切换 PostgreSQL。

## 配置环境变量

在 `C:\sazj\.env` 中维护生产环境配置，可参考 [windows_env_example.md](./windows_env_example.md)。

后端当前会读取 `backend/.env`。短期演示部署可把 `C:\sazj\.env` 复制到 `C:\sazj\backend\.env`：

```powershell
Copy-Item C:\sazj\.env C:\sazj\backend\.env
```

最小配置：

```text
APP_ENV=production
API_PREFIX=/api
DATABASE_URL=sqlite:///C:/sazj/backend/sazj.sqlite3
AUTO_CREATE_TABLES=true
SQLITE_JOURNAL_MODE=OFF
FRONTEND_ORIGINS=http://服务器公网IP
UPLOAD_DIR=C:\sazj\uploads
LOG_DIR=C:\sazj\logs
PROVIDER_SECRET_KEY=请替换为32字符以上随机密钥
ADMIN_WEBUI_TOKEN=请替换为32字符以上随机管理员令牌
JWT_SECRET_KEY=请替换为32字符以上随机密钥
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAX_UPLOAD_BYTES=8388608
```

`PROVIDER_SECRET_KEY` 用于加密模型提供商 API Key。部署后不要随意修改，否则旧配置将无法解密。

`ADMIN_WEBUI_TOKEN` 用于保护 `/admin/providers` 模型配置后台，只给项目维护者使用。

`JWT_SECRET_KEY` 用于签发登录访问令牌。修改后旧 token 会失效，用户需要重新登录。

## 初始化后端

```powershell
cd C:\sazj
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python build.py --skip-frontend
```

当前阶段使用 `AUTO_CREATE_TABLES=true` 自动创建表。启动后端时会创建 `model_configs` 表。后续正式迁移阶段再接 Alembic。

首次启动前建议创建运行目录：

```powershell
New-Item -ItemType Directory -Force C:\sazj\logs
New-Item -ItemType Directory -Force C:\sazj\uploads
```

后端启动时也会自动创建 `UPLOAD_DIR` 和 `LOG_DIR`。

## 启动 FastAPI 后端

```powershell
cd C:\sazj
.\venv\Scripts\activate
python start.py --host 0.0.0.0 --port 8000 --no-reload
```

服务器本机验证：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

预期返回健康状态 JSON。

## 构建 Vue 前端

```powershell
cd C:\sazj\frontend
npm install
npm run build
```

构建产物在：

```text
C:\sazj\frontend\dist
```

## 静态文件和反向代理

短期演示优先推荐 Caddy for Windows，配置比 IIS 和 Nginx Windows 版更简单。

示例 `Caddyfile`：

```text
:80 {
    root * C:\sazj\frontend\dist
    encode gzip
    try_files {path} /index.html
    file_server

    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }

    handle /admin/* {
        reverse_proxy 127.0.0.1:8000
    }
}
```

验证：

```text
http://服务器公网IP/
http://服务器公网IP/api/health
http://服务器公网IP/admin/providers
```

如果暂时不配置反向代理，也可以直接开放 `8000` 端口访问后端接口，但正式演示建议统一走 `80` 端口。

## 注册为 Windows 服务

后端建议使用 NSSM 注册为 Windows 服务，详见 [windows_nssm_service.md](./windows_nssm_service.md)。

## 自动更新

服务器部署完成后，可以使用根目录 `auto_update.py` 定时检查 GitHub 更新。脚本会从 `https://github.com/fuzong01-cloud/sazj` 的 `origin/main` 拉取新版本，只允许 fast-forward 更新，并在检测到本地未提交改动时自动停止。

手动检查：

```powershell
cd C:\sazj
.\venv\Scripts\python.exe auto_update.py --check-only
```

执行更新并重启后端服务：

```powershell
.\venv\Scripts\python.exe auto_update.py --restart-service --service-name sazj-backend
```

定时任务配置详见 [windows_auto_update.md](./windows_auto_update.md)。

## 防火墙

至少开放：

- `80`：前端页面和反向代理后的 API。
- `8000`：仅在没有反向代理或需要临时调试时开放。
- 不需要开放数据库端口；SQLite 是本地文件。

详见 [windows_firewall_notes.md](./windows_firewall_notes.md)。

## 验收目标

当前阶段应验证：

- 服务器本机 `http://127.0.0.1:8000/api/health` 正常。
- 外部浏览器 `http://服务器公网IP/` 可以打开前端页面。
- 外部访问 `http://服务器公网IP/api/health` 返回后端健康状态。
- 维护者可以通过 `/admin/providers` 创建 VisionProvider 和 TextProvider 配置，并使用“测试连接”验证 Base URL、API Key 和模型名。
- 上传图片后可以调用外部 Vision LLM API。
- 可以调用 Text LLM API 生成防治建议和前端 AI 助手回答。
- 前端可获取定位和天气，`/api/predict` 能结合天气、湿度、降水和气候带生成建议。
- 重启服务器后，NSSM 管理的后端服务自动恢复。

后续功能完成后再补充验证：

- 用户注册登录。
- 识别历史保存到 SQLite。
- 日志写入 `C:\sazj\logs` 或 `system_logs` 表。
- 区域统计和风险预警页面可用。

## 常见问题

端口无法访问：

- 检查云服务器安全组是否开放 `80`。
- 检查 Windows 防火墙入站规则。
- 检查 Caddy/Nginx/IIS 是否已启动。

数据库连接失败：

- 检查 `DATABASE_URL` 用户名、密码、端口和数据库名。
- 确认 PostgreSQL 服务正在运行。
- 不要把 PostgreSQL `5432` 暴露到公网。

API Key 配置错误：

- `/admin/providers` 的“测试连接”只验证基础 `chat/completions` 连通性，不保证视觉图片识别一定可用。
- 调用 `/api/predict` 或 `/api/chat` 时如果返回 502，优先检查 `base_url`、`api_key`、`model_name`。

上传目录权限不足：

- 确认 `C:\sazj\uploads` 存在。
- 确认运行后端服务的 Windows 用户对该目录有写权限。
- 确认 `LOG_DIR` 对运行后端服务的 Windows 用户可写，否则日志文件无法创建。

日志文件未生成：

- 检查 `LOG_DIR` 是否存在。
- 检查 NSSM 服务使用的 Windows 用户是否有写权限。
- 应用会优先保证服务启动；如果文件日志无法打开，会在控制台或 NSSM stderr 日志中输出 `file logging disabled`。

内存不足：

- 不要在服务器上运行训练脚本、Notebook、本地大模型或 TensorFlow 推理。
- PostgreSQL、Caddy、Uvicorn 保持轻量配置。

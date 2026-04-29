# 后端服务

本目录是薯安智检的 FastAPI 后端。当前版本提供健康检查、模型配置、外部 Vision/Text Provider 调用入口，并已将模型配置接入 SQLAlchemy 数据库仓储。

## 启动方式

使用根目录已有 `.venv`：

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## 数据库配置

复制 `.env.example` 为 `.env` 后配置 PostgreSQL：

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sazj
AUTO_CREATE_TABLES=true
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
UPLOAD_DIR=../uploads
LOG_DIR=../logs
```

当前阶段开发环境使用 SQLAlchemy `create_all` 自动建表。后续正式迁移阶段应改为 Alembic。

`UPLOAD_DIR` 和 `LOG_DIR` 会在后端启动时自动创建。默认日志文件为 `LOG_DIR/backend.log`，使用轻量滚动日志，适合短期演示部署。

## Windows Server 启动

默认演示部署目标是 Windows Server 2 核 2GB 轻量云服务器。后端启动命令：

```powershell
cd C:\sazj\backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

进程守护优先使用 NSSM，完整部署步骤见 `deploy/windows_server_deploy.md` 和 `deploy/windows_nssm_service.md`。

## 当前接口

- `GET /api/health`
- `GET /api/model/status`
- `GET /api/model-configs`
- `POST /api/model-configs`
- `PUT /api/model-configs/{id}`
- `DELETE /api/model-configs/{id}`
- `POST /api/predict`
- `POST /api/advice/generate`
- `POST /api/chat`

## 注意

- 当前识别通过用户配置的 Vision LLM API 完成，不加载本地 TensorFlow 模型。
- 当前已持久化模型配置，但 API Key 仍为明文字段，下一阶段必须加密保存。

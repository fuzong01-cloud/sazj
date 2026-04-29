# 后端服务

本目录是薯安智检的 FastAPI 后端。当前后端提供健康检查、用户注册登录、用户级模型配置、外部 Vision/Text Provider 调用、识别记录持久化和历史记录查询。

## 本地启动

推荐从项目根目录启动：

```powershell
python start.py
```

`start.py` 会默认使用 SQLite，并自动设置：

```text
DATABASE_URL=sqlite:///backend/sazj.sqlite3
AUTO_CREATE_TABLES=true
SQLITE_JOURNAL_MODE=OFF
UPLOAD_DIR=uploads
LOG_DIR=logs
```

访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/health
```

## 构建依赖

推荐从项目根目录执行：

```powershell
python build.py --skip-frontend
```

如需同时安装前端依赖并构建前端：

```powershell
python build.py
```

前端开发服务从项目根目录启动：

```powershell
python start_frontend.py
```

## 数据库配置

本地开发默认使用 SQLite，数据库文件为：

```text
backend/sazj.sqlite3
```

如果需要切换 PostgreSQL，可在 `backend/.env` 或根目录 `.env` 中配置：

```text
DATABASE_URL=postgresql+psycopg://postgres:密码@127.0.0.1:5432/sazj
AUTO_CREATE_TABLES=true
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

当前阶段使用 SQLAlchemy `create_all` 自动建表。正式迁移阶段应改为 Alembic。

## 当前接口

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/model/status`
- `GET /api/model-configs`
- `POST /api/model-configs`
- `PUT /api/model-configs/{id}`
- `DELETE /api/model-configs/{id}`
- `POST /api/predict`
- `GET /api/history?limit=20&offset=0`
- `GET /api/history/{id}`
- `DELETE /api/history/{id}`
- `POST /api/advice/generate`
- `POST /api/chat`

## 注意事项

- 当前识别通过用户配置的 Vision LLM API 完成，不加载本地 TensorFlow 模型。
- 当前防治建议和聊天通过用户配置的 Text LLM API 完成。
- Provider API Key 会加密后入库。
- 登录后模型配置和历史记录优先按当前用户隔离。
- SQLite 适合本地开发和临时演示；正式 Windows Server 部署仍建议使用 PostgreSQL。

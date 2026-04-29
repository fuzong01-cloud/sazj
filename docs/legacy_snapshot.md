# 遗留项目快照

日期：2026-04-29

本文档记录新旧技术路线切换后的仓库状态。

## 新技术路线

新系统采用纯 API 驱动的大模型方案：

- 图像识别由用户配置的 Vision LLM API 完成。
- 文本建议、网页 AI 助手、病害问答由用户配置的 Text LLM API 完成。
- 平台本身不内置 API Key、Token，也不固定绑定 Kimi、豆包、通义、OpenAI 或其他厂商。
- 后端提供 `VisionProvider` 和 `TextProvider` 两套抽象层。
- 模型配置包括 `provider_name`、`provider_type`、`base_url`、`api_key`、`model_name`、`enabled`。
- `provider_type` 当前支持 `vision` 和 `text`。
- 默认部署目标改为 Windows Server 轻量云服务器，2 核 CPU、2GB 内存、40GB 存储。
- Ubuntu + systemd + Linux Nginx + Gunicorn 不再作为默认部署方案。
- 后端已读取 `UPLOAD_DIR`、`LOG_DIR` 和轻量数据库连接池配置。
- 启动时会自动创建上传目录、日志目录，并写入 `backend.log`。
- Provider API Key 新写入和更新时会加密保存，API 响应不返回明文。
- 当前已提供基础用户注册、登录、`/me` 接口，但业务数据尚未按用户隔离。
- 当前历史记录已优先使用当前用户上下文；未登录时保留全局历史视图。

## v0.4.0 数据库接入状态

当前已接入 SQLAlchemy：

- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/init_db.py`
- `backend/app/models/model_config.py`
- `backend/app/repositories/model_config_repository.py`

当前已持久化：

- 模型配置 `model_configs`
- 识别记录 `prediction_records`
- 用户 `users`

尚未持久化：

- 用户历史
- 区域统计
- 日志记录

## legacy 资料

以下内容只作为旧项目来源和历史问题说明，不进入新系统主线：

- `final_model.h5`
- `main/Potato Leaf Disease Prediction.py`
- `main/Potato Leaf Disease Classification.ipynb`
- `main/Potato Leaf Disease Classification (COLAB).ipynb`
- `main/sample/potato.png`
- Kaggle / PlantVillage 相关说明
- Colab `/content/...` 路径和训练脚本残留
- `webapp.py` Streamlit Demo
- `Procfile` 和 `setup.sh` 中的旧 Streamlit 部署路径

## 当前接口

- `GET /api/health`
- `GET /api/model/status`
- `GET /api/model-configs`
- `POST /api/model-configs`
- `GET /api/model-configs/{id}`
- `PUT /api/model-configs/{id}`
- `DELETE /api/model-configs/{id}`
- `POST /api/predict`
- `GET /api/history`
- `GET /api/history/{id}`
- `DELETE /api/history/{id}`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/advice/generate`
- `POST /api/chat`

## 当前限制

- 旧数据库中历史明文 API Key 需要重新保存一次配置，才能转换为加密字段。
- 尚未接入 Alembic，开发期暂用 `create_all`。
- 尚未实现用户系统、历史记录、区域统计和日志记录。
- 当前已提供历史记录查询、分页和删除 API，登录后按用户过滤，未登录时返回全局记录。
- 用户接口已建立，模型配置、区域统计还未接入用户归属。
- 前端主页面已展示最近识别历史，点击记录可查看摘要、建议、置信度和原始模型输出。
- Provider 当前按 OpenAI-compatible `chat/completions` 协议实现，后续可扩展不同厂商适配器。

## 验证命令

后端依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

PostgreSQL 环境变量示例：

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sazj"
$env:AUTO_CREATE_TABLES="true"
```

没有本地 PostgreSQL 时，可用内存 SQLite 临时验证 SQLAlchemy 仓储行为：

```powershell
$env:DATABASE_URL="sqlite:///:memory:"
$env:AUTO_CREATE_TABLES="true"
cd backend
..\.venv\Scripts\python.exe -c "from app.db.init_db import create_db_and_tables; create_db_and_tables(); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.post('/api/model-configs', json={'provider_name':'mock','provider_type':'vision','base_url':'https://example.com/v1','api_key':'secret','model_name':'vision-model','enabled':True}).json()); print(c.get('/api/model-configs').json())"
```

预期结果：

- 依赖安装成功。
- 数据库能创建 `model_configs` 表。
- `POST /api/model-configs` 能写入数据库。
- `GET /api/model-configs` 能读出刚写入的配置。

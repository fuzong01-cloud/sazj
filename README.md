# 薯安智检农业病害识别平台

薯安智检是一个面向马铃薯病虫害场景的 AI 识别、历史记录、区域统计、风险预警、知识库增强和防治建议管理平台。

当前技术路线已经调整：新系统不再使用本地 CNN，不设计离线识别，也不围绕 Kaggle/PlantVillage 数据集或训练脚本继续开发。`final_model.h5`、Notebook/Colab 训练代码和 Kaggle 相关内容只作为 legacy 资料保留，用于说明旧项目来源和历史问题，不进入新架构主线。

## 当前状态

- 版本基线：`v0.4.0 PostgreSQL model config baseline`。
- 当前后端入口：`backend/app/main.py`。
- 当前前端入口：`frontend/src/main.js`。
- 当前识别接口：`POST /api/predict`，通过用户配置的 Vision LLM API 完成。
- 当前建议接口：`POST /api/advice/generate`，通过用户配置的 Text LLM API 完成。
- 当前问答接口：`POST /api/chat`，通过用户配置的 Text LLM API 完成。
- 模型配置接口：`/api/model-configs`，已切换为 SQLAlchemy 数据库仓储。
- 模型配置归属：登录后创建和调用的是当前用户自己的 Vision/Text Provider；未登录时使用全局演示 provider。
- 识别记录：`POST /api/predict` 成功后会写入 `prediction_records` 表，并返回 `record_id`。
- 历史记录接口：`GET /api/history`、`GET /api/history/{id}`、`DELETE /api/history/{id}`，当前操作全局识别记录。
- 用户基础接口：`POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`。
- 用户上下文：前端支持登录/注册和本地 token 管理；登录后识别记录会绑定当前用户，历史记录优先返回当前用户数据。
- 前端历史记录：主页面已展示最近识别记录，点击记录可查看摘要、建议、置信度和原始模型输出。
- 旧本地模型：`final_model.h5` 仅作为 legacy 资料，不参与运行。
- 默认部署目标：Windows Server 轻量云服务器，2 核 CPU、2GB 内存、40GB 存储。

## 技术栈

- 后端：Python + FastAPI + Uvicorn
- 数据库：PostgreSQL + SQLAlchemy
- 外部模型调用：httpx + OpenAI-compatible chat/completions
- 前端：Vue + Vite + JavaScript
- 部署：Windows Server + Uvicorn + PostgreSQL for Windows + Caddy/NSSM

## 仓库结构

```text
.
|-- app.py                                  # 旧 Flask 页面下线提示
|-- final_model.h5                          # legacy 本地 CNN 模型资料，不参与新系统运行
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/                             # SQLAlchemy engine/session/init
|   |   |-- models/                         # SQLAlchemy models
|   |   |-- providers/                      # VisionProvider / TextProvider
|   |   |-- repositories/                   # 数据库仓储
|   |   |-- schemas/
|   |   `-- services/
|   |-- requirements.txt
|   `-- README.md
|-- frontend/
|-- deploy/                                 # Windows Server 部署文档
|-- main/                                   # legacy Colab/Kaggle 训练残留
|-- legacy/
|-- docs/
|-- README.md
`-- HISTORY.md
```

## PostgreSQL 配置

创建数据库后，在 `backend/.env` 中配置：

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sazj
AUTO_CREATE_TABLES=true
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
UPLOAD_DIR=../uploads
LOG_DIR=../logs
PROVIDER_SECRET_KEY=development-provider-secret-key-change-me
JWT_SECRET_KEY=development-jwt-secret-key-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

当前阶段使用 SQLAlchemy `create_all` 在开发环境自动建表。后续进入正式迁移阶段时，应改为 Alembic 管理迁移。

2 核 2GB Windows Server 默认采用轻量连接池：常驻连接 2 个，临时溢出连接 1 个。后端启动时会自动创建 `UPLOAD_DIR` 和 `LOG_DIR`，并在 `LOG_DIR/backend.log` 写入滚动日志。

`PROVIDER_SECRET_KEY` 用于加密模型提供商 API Key。生产环境必须替换为 32 字符以上随机密钥，并在部署后保持稳定。

## Windows Server 部署

当前项目默认面向一台 Windows Server 轻量云服务器部署：

```text
C:\sazj\
  backend\
  frontend\
  deploy\
  logs\
  uploads\
  .env
```

部署文档：

- [Windows Server 轻量云服务器部署指南](deploy/windows_server_deploy.md)
- [使用 NSSM 注册 FastAPI 后端服务](deploy/windows_nssm_service.md)
- [Windows Server .env 示例](deploy/windows_env_example.md)
- [Windows Server 防火墙与公网访问说明](deploy/windows_firewall_notes.md)

服务器只负责运行前端静态页面、FastAPI 后端、PostgreSQL、上传文件存储、日志记录和外部模型 API 转发。不要在服务器上训练 CNN、运行本地大模型或执行重型推理。

## 本地启动

后端：

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:5173
```

## 模型配置

创建视觉模型配置：

```http
POST /api/model-configs
Content-Type: application/json

{
  "provider_name": "my-vision-provider",
  "provider_type": "vision",
  "base_url": "https://example.com/v1",
  "api_key": "YOUR_API_KEY",
  "model_name": "vision-model-name",
  "enabled": true
}
```

创建文本模型配置：

```http
POST /api/model-configs
Content-Type: application/json

{
  "provider_name": "my-text-provider",
  "provider_type": "text",
  "base_url": "https://example.com/v1",
  "api_key": "YOUR_API_KEY",
  "model_name": "text-model-name",
  "enabled": true
}
```

注意：Provider API Key 会加密后存入数据库。API 响应只返回 `api_key_masked`，不会返回明文。

登录后调用 `/api/model-configs` 会自动绑定当前用户。不同用户不会共用同一组 provider；未登录请求仍使用 `user_id=null` 的全局演示配置。

## 识别记录

`POST /api/predict` 成功调用 VisionProvider 后，会写入 `prediction_records` 表。当前保存 provider 名称、模型名、疾病名称、风险等级、置信度、摘要、建议、原始模型文本、上传文件名、图片 Content-Type 和创建时间。

查询接口：

- `GET /api/history?limit=20&offset=0`
- `GET /api/history/{id}`
- `DELETE /api/history/{id}`

当前阶段还没有用户系统和图片文件持久化，因此识别记录暂未绑定用户，也不保存原图路径。用户系统完成后，历史记录接口会改为只返回当前用户的数据。

## 用户系统

当前已提供基础用户接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

密码使用 PBKDF2 哈希保存，登录后返回 Bearer Token。当前历史记录、模型配置尚未按用户隔离，后续阶段会逐步接入当前用户上下文。

前端已提供登录/注册面板。登录后：

- `/api/predict` 会把新识别记录绑定到当前用户。
- `/api/history`、`/api/history/{id}`、`DELETE /api/history/{id}` 会优先使用当前用户上下文。
- `/api/model-configs` 会优先使用当前用户上下文。
- 未登录时仍保留全局历史视图，便于演示和兼容旧数据。

## 开发计划

1. 完成模型配置 PostgreSQL 持久化。
2. 建立 Windows Server 2 核 2GB 演示部署方案。
3. 落地 Windows 部署运行参数、轻量日志和数据库连接池配置。
4. 补充图片文件保存。
5. 增加前端模型配置管理页面。
6. 补充图片文件保存。
7. 增加前端登录态路由保护和用户资料页。
7. 持久化区域统计和日志。
8. 增加知识库增强、防治建议管理、风险预警和统计看板。
9. 清理或迁移 legacy 模型、Notebook、Colab、Kaggle 残留资料。

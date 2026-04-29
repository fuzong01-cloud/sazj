# 薯安智检农业病害识别平台

薯安智检是一个面向马铃薯病虫害场景的 AI 识别、历史记录、区域统计、风险预警、知识库增强和防治建议管理平台。

当前技术路线已经调整：新系统不再使用本地 CNN，不设计离线识别，也不围绕 Kaggle/PlantVillage 数据集或训练脚本继续开发。`final_model.h5`、Notebook/Colab 训练代码和 Kaggle 相关内容只作为 legacy 资料保留，用于说明旧项目来源和历史问题，不进入新架构主线。

## 当前状态

- 版本基线：`v0.5.6 weather-aware prediction baseline`。
- 当前后端入口：`backend/app/main.py`。
- 当前前端入口：`frontend/src/main.js`。
- 当前识别接口：`POST /api/predict`，通过平台后端统一配置的 Vision LLM API 完成。
- 当前建议接口：`POST /api/advice/generate`，通过平台后端统一配置的 Text LLM API 完成。
- 当前问答接口：`POST /api/chat`，通过平台后端统一配置的 Text LLM API 完成。
- 模型配置后台：`/admin/providers`，由项目维护者配置全局 Vision/Text Provider，并支持测试连接。
- 模型配置 API：`/api/model-configs` 仅供管理员自动化使用，需要 `X-Admin-Token`。
- 识别记录：`POST /api/predict` 成功后会写入 `prediction_records` 表，并返回 `record_id`。
- 历史记录接口：`GET /api/history`、`GET /api/history/{id}`、`DELETE /api/history/{id}`，当前操作全局识别记录。
- 用户基础接口：`POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`。
- 用户上下文：前端支持登录/注册和本地 token 管理；登录后识别记录会绑定当前用户，历史记录优先返回当前用户数据。
- 前端历史记录：主页面已展示最近识别记录，点击记录可查看摘要、建议、置信度和原始模型输出。
- 前端 AI 助手：主页面已提供病害问答入口，调用后端 TextProvider。
- 定位天气：前端可获取浏览器定位，后端查询天气并判断气候带，识别时会把环境上下文传给 VisionProvider。
- 旧本地模型：`final_model.h5` 仅作为 legacy 资料，不参与运行。
- 默认部署目标：Windows Server 轻量云服务器，2 核 CPU、2GB 内存、40GB 存储。

## 技术栈

- 后端：Python + FastAPI + Uvicorn
- 数据库：本地默认 SQLite + SQLAlchemy，部署阶段可切换 PostgreSQL
- 外部模型调用：httpx + OpenAI-compatible chat/completions
- 前端：Vue + Vite + JavaScript
- 部署：Windows Server + Uvicorn + SQLite 默认演示库 + Caddy/NSSM

## 仓库结构

```text
.
|-- build.py                                # Python 构建入口：安装依赖并构建前端
|-- start.py                                # Python 启动入口：默认 SQLite 启动 FastAPI 后端
|-- start_frontend.py                       # Python 前端开发服务启动入口
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

旧的根目录 `app.py`、`webapp.py`、`Procfile`、`setup.sh` 和根目录 `requirements.txt` 已清理。当前后端依赖以 `backend/requirements.txt` 为准。

## 本地 SQLite 配置

本地开发默认使用 SQLite，不再要求先安装 PostgreSQL。默认数据库文件位于：

```text
backend/sazj.sqlite3
```

如需显式配置，可在 `backend/.env` 中写入：

```text
DATABASE_URL=sqlite:///./sazj.sqlite3
AUTO_CREATE_TABLES=true
SQLITE_JOURNAL_MODE=OFF
UPLOAD_DIR=../uploads
LOG_DIR=../logs
PROVIDER_SECRET_KEY=development-provider-secret-key-change-me
ADMIN_WEBUI_TOKEN=development-admin-token-change-me
JWT_SECRET_KEY=development-jwt-secret-key-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

当前阶段使用 SQLAlchemy `create_all` 在开发环境自动建表。后续进入正式迁移阶段时，应改为 Alembic 管理迁移。

`SQLITE_JOURNAL_MODE=OFF` 是当前 Windows 本地开发兼容设置，用于避开部分磁盘/同步目录环境下 SQLite journal 文件导致的 `disk I/O error`。长期部署或关键数据场景建议切换 PostgreSQL。

部署到 Windows Server 时仍可切换 PostgreSQL。2 核 2GB Windows Server 建议采用轻量连接池：常驻连接 2 个，临时溢出连接 1 个。后端启动时会自动创建 `UPLOAD_DIR` 和 `LOG_DIR`，并在 `LOG_DIR/backend.log` 写入滚动日志。

`PROVIDER_SECRET_KEY` 用于加密模型提供商 API Key。生产环境必须替换为 32 字符以上随机密钥，并在部署后保持稳定。

`ADMIN_WEBUI_TOKEN` 用于保护后端模型配置 WebUI。生产环境必须替换为随机令牌，不要发给普通用户。

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

服务器只负责运行前端静态页面、FastAPI 后端、SQLite 演示库、上传文件存储、日志记录和外部模型 API 转发。不要在服务器上训练 CNN、运行本地大模型或执行重型推理。

## 本地启动

首次构建：

```powershell
python build.py
```

启动后端：

```powershell
python start.py
```

启动前端开发服务：

```powershell
python start_frontend.py
```

访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:5173
```

## 后端模型配置 WebUI

平台维护者访问：

```text
http://127.0.0.1:8000/admin/providers
```

输入 `ADMIN_WEBUI_TOKEN` 后，可配置平台统一使用的 VisionProvider 和 TextProvider。

注意：Provider API Key 会加密后存入数据库，页面不会回显明文。普通用户前端不提供 API Key、Base URL 或模型名称配置入口。

VisionProvider 用于图片识别，TextProvider 用于 AI 助手和防治建议。二者可以配置为不同厂商、不同 Base URL、不同 API Key 和不同模型名。管理页中的“测试连接”按钮会验证当前 provider 的 Base URL、API Key 和模型名是否能完成基础 `chat/completions` 调用。

## 定位、天气和气候带

前端主页面提供“获取定位和天气”按钮。用户授权浏览器定位后，前端只把经纬度传给后端：

```text
GET /api/weather?latitude=31.2&longitude=121.5
```

后端使用 Open-Meteo Forecast API 查询当前天气，并按纬度粗分气候带：热带、亚热带、温带、高纬/寒温带。

上传图片识别时，前端会把经纬度一并提交给 `/api/predict`。后端重新获取天气上下文后再调用 VisionProvider，让大模型结合图片、天气、湿度、降水、气候带等信息输出更专业的防治建议。

## 识别记录

`POST /api/predict` 成功调用 VisionProvider 后，会写入 `prediction_records` 表。当前保存 provider 名称、模型名、疾病名称、风险等级、置信度、摘要、建议、原始模型文本、上传文件名、图片 Content-Type 和创建时间。

查询接口：

- `GET /api/history?limit=20&offset=0`
- `GET /api/history/{id}`
- `DELETE /api/history/{id}`
- `GET /api/weather?latitude=...&longitude=...`

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
- 未登录时仍保留全局历史视图，便于演示和兼容旧数据。

## 开发计划

1. 补充图片文件保存。
2. 将天气上下文保存到识别历史。
3. 增加前端登录态路由保护和用户资料页。
4. 持久化区域统计和日志。
5. 增加知识库增强、防治建议管理、风险预警和统计看板。
6. 按演示稳定性决定是否从 SQLite 切换 PostgreSQL。
7. 清理或迁移 legacy 模型、Notebook、Colab、Kaggle 残留资料。

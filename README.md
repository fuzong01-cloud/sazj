# 薯安智检农业病害识别平台

薯安智检是一个面向马铃薯病虫害场景的 AI 识别与防治建议平台。当前系统的核心价值不再是本地训练 CNN 模型，而是把外部大模型能力、安全的后台模型配置、用户会话历史、天气位置上下文和可部署的 WebUI 组合成一个轻量演示平台。

## 当前状态

当前基线：`v0.6.0 streaming WebUI baseline`。

已经确认的新方向：

- 不再使用本地 CNN 作为主线。
- 不在服务器上训练模型，也不运行本地大模型。
- `final_model.h5`、Notebook、Colab、Kaggle/PlantVillage 相关内容只作为 legacy 资料保留。
- 普通用户不在前端配置 API Key。
- 平台维护者在后端管理页统一配置外部大模型 Provider。
- 聊天、图片识别、防治建议默认走同一套通用 Provider 运行时。
- 本地开发和一个月演示部署默认使用 SQLite。
- 默认部署目标优先适配 Windows Server 2 核 2GB 轻量云服务器。

## 已完成能力

### 后端

- FastAPI 后端入口：`backend/app/main.py`。
- Python 启动入口：`start.py`。
- 默认 SQLite 数据库：`backend/sazj.sqlite3`。
- 自动初始化数据库表：开发阶段通过 SQLAlchemy `create_all` 完成。
- 用户注册、登录、当前用户信息、资料修改、头像上传、修改密码。
- 后端管理员 Provider WebUI：`/admin/providers`。
- Provider API Key 加密存储，不向前端普通用户暴露明文。
- 通用 OpenAI-compatible `chat/completions` 调用层。
- Kimi / Moonshot 兼容路径：`{base_url}/chat/completions` 或 `{base_url}/v1/chat/completions`，避免 `/v1/v1` 和 `/responses`。
- 文本聊天：`POST /api/chat`、`POST /api/chat/stream`。
- 图片识别：`POST /api/predict`、`POST /api/predict/stream`。
- 防治建议：`POST /api/advice/generate`。
- 天气位置：`GET /api/weather`。
- 网页搜索：`GET /api/search/web`，用于给模型回答补充搜索上下文。
- 会话历史：`GET /api/conversations`、`GET /api/conversations/{id}`、`PATCH /api/conversations/{id}`、`DELETE /api/conversations/{id}`。
- 旧识别记录接口仍保留：`GET /api/history`、`GET /api/history/{id}`、`DELETE /api/history/{id}`。
- 流式接口已增加 SSE 反缓冲响应头，便于前端实时显示回答和推理过程。

### 前端

- Vue + Vite 前端入口：`frontend/src/main.js`。
- Python 前端启动入口：`start_frontend.py`。
- ChatGPT 风格对话页面。
- 左侧侧边栏支持收起和展开。
- 侧边栏展示品牌、创建新聊天、搜索聊天、历史对话、用户信息。
- 历史对话按当前登录用户读取，支持删除和重命名。
- 未登录时要求先登录后使用主要功能。
- 顶部显示后端在线状态和当前可用模型。
- 模型选择下拉框只展示 Provider 名称，不把展示文本当作真实模型 ID。
- 输入框支持点击上传、页面拖拽上传、剪贴板粘贴图片。
- 加号扩展菜单支持上传图片/文件、获取天气和位置、网页搜索。
- 深度思考做成输入框内按钮，支持开启/关闭状态。
- AI 回复支持 Markdown 渲染。
- 推理过程支持展示、默认展开/收起策略、耗时提示和自动滚动到底部。
- 消息下方提供复制和重新生成按钮，按钮图标来自 `frontend/public/Resource/`。

### 数据与安全

- 用户密码使用 PBKDF2 哈希保存。
- 登录使用 Bearer Token。
- Provider API Key 使用 `PROVIDER_SECRET_KEY` 加密保存。
- 头像和上传目录保存在服务器文件系统中。
- 日志目录通过 `LOG_DIR` 配置并自动创建。
- 普通用户不能在前端查看或修改平台大模型 API Key。

## 技术栈

- 后端：Python、FastAPI、Uvicorn、SQLAlchemy
- 默认数据库：SQLite
- 可选数据库：PostgreSQL，当前不是默认演示路线
- 外部模型：OpenAI-compatible `chat/completions`
- 前端：Vue、Vite、JavaScript
- 部署目标：Windows Server 轻量云服务器
- 服务守护：NSSM 或 Windows 任务计划程序
- 静态服务和反向代理：Caddy、Nginx Windows 版或 IIS

## 目录结构

```text
.
|-- build.py                         # 安装依赖并构建前端
|-- start.py                         # 启动 FastAPI 后端，默认 SQLite
|-- start_frontend.py                # 启动 Vite 前端开发服务
|-- final_model.h5                   # legacy 本地 CNN 模型资料，不参与新系统运行
|-- backend/
|   |-- app/
|   |   |-- api/                     # FastAPI 路由
|   |   |-- core/                    # 配置、安全、加密
|   |   |-- db/                      # SQLAlchemy engine/session/init
|   |   |-- models/                  # 数据模型
|   |   |-- providers/               # 通用模型运行时、文本/视觉适配层
|   |   |-- repositories/            # 数据访问层
|   |   |-- schemas/                 # Pydantic schemas
|   |   `-- services/                # 业务服务
|   `-- requirements.txt
|-- frontend/
|   |-- public/Resource/             # 前端图标和 logo 资源
|   `-- src/
|-- deploy/                          # Windows Server 部署文档
|-- docs/                            # legacy 快照与阶段说明
|-- legacy/                          # 历史资料归档
|-- main/                            # legacy Colab/Kaggle 训练残留
|-- uploads/                         # 本地上传目录
|-- logs/                            # 本地日志目录
|-- README.md
`-- HISTORY.md
```

## 本地启动

首次准备依赖和前端构建：

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

访问地址：

```text
前端：http://127.0.0.1:5173
后端：http://127.0.0.1:8000
接口文档：http://127.0.0.1:8000/docs
Provider 管理页：http://127.0.0.1:8000/admin/providers
```

## 环境变量

可在 `backend/.env` 或根目录 `.env` 中配置。`backend/.env` 优先级更高。

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

生产或演示服务器必须替换：

- `PROVIDER_SECRET_KEY`
- `ADMIN_WEBUI_TOKEN`
- `JWT_SECRET_KEY`

这些值不要提交到 GitHub。

## Provider 管理

平台维护者访问：

```text
http://127.0.0.1:8000/admin/providers
```

输入 `ADMIN_WEBUI_TOKEN` 后，可以配置平台统一使用的通用模型 Provider，包括：

- Provider 名称
- Base URL
- API Key
- 模型名
- 是否启用
- 是否支持深度思考/推理
- 上下文长度
- 最大输出长度

普通用户只在前端选择可用 Provider，不接触 API Key、Base URL 或真实模型配置。

## 主要接口

```text
GET    /api/health
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
PATCH  /api/auth/me
PUT    /api/auth/me/password
POST   /api/auth/me/avatar

POST   /api/chat
POST   /api/chat/stream
POST   /api/predict
POST   /api/predict/stream
POST   /api/advice/generate

GET    /api/weather
GET    /api/search/web

GET    /api/conversations
GET    /api/conversations/{id}
PATCH  /api/conversations/{id}
DELETE /api/conversations/{id}

GET    /api/history
GET    /api/history/{id}
DELETE /api/history/{id}
```

当前前端主要使用 `conversations` 作为聊天历史；`history` 仍保留给旧识别记录和兼容场景。

## Windows Server 部署

当前默认演示目录建议：

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

2 核 2GB 服务器只负责运行 Web 服务、SQLite 演示库、上传文件、日志和外部 API 转发。不要在服务器上训练 CNN 或运行本地大模型。

## Legacy 资料说明

以下内容只作为历史资料，不参与新架构主线：

- `final_model.h5`
- `main/` 下 Notebook、Colab、Kaggle/PlantVillage 训练残留
- 旧 PPT、策划书、演示资料
- 旧 Flask / Streamlit 入口已清理

更换数据集、寻找训练脚本、彻底割裂 Kaggle 数据集粘连不属于当前代码主线。

## 当前限制

- SQLite 适合本地开发和短期演示，不适合长期高并发生产环境。
- 目前尚未接入 Alembic，数据库迁移仍以开发期自动建表为主。
- 网页搜索使用轻量 HTML 搜索方式，稳定性取决于外部搜索页面可访问性。
- 流式输出效果取决于上游模型、网络、浏览器和反向代理是否真正逐块返回数据。
- 天气和气候带判断是轻量实现，尚未结合长期气候统计、海拔、土壤和区域病害流行数据。
- 区域统计、风险预警、知识库增强、防治建议管理后台仍待继续建设。

## 下一阶段计划

1. 稳定 WebUI 流式输出和深度思考体验。
2. 完善会话重试、复制、错误回显和模型过载提示。
3. 增加区域统计和风险预警数据表。
4. 建立防治建议管理和知识库增强接口。
5. 补充系统日志入库和管理端查看页面。
6. 为 Windows Server 演示部署补充一键检查脚本。
7. 在需要更高并发或长期运行时，再设计 SQLite 到 PostgreSQL 的迁移方案。

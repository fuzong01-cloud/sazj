# 版本历史

## v0.5.6 weather-aware prediction baseline

日期：2026-04-29

该版本新增定位、天气和气候带上下文，并接入图片识别提示词。

本基线已完成：

- 新增 `backend/app/api/weather.py`。
- 新增 `backend/app/schemas/weather.py`。
- 新增 `backend/app/services/weather_service.py`。
- 新增 `GET /api/weather`，根据经纬度查询当前天气。
- 后端按纬度粗分气候带：热带、亚热带、温带、高纬/寒温带。
- `/api/predict` 新增 `latitude`、`longitude`、`location_label` 表单字段。
- VisionProvider 调用时会把位置、天气、湿度、降水、气候带传入提示词。
- 前端新增“定位与天气”面板，使用浏览器定位并显示天气信息。
- 前端上传图片时会把经纬度一并提交给后端。
- AI 助手上下文会附带最近一次识别结果和天气摘要。

已知限制：

- 天气上下文暂未保存到 `prediction_records` 表。
- 气候带判断是按纬度粗分，尚未结合海拔、季风区、地形和长期气候统计。
- VisionProvider 图片能力仍取决于后端配置的外部模型。

## v0.5.5 provider test and assistant baseline

日期：2026-04-29

该版本新增后端 Provider 测试连接按钮，并在普通前端增加 AI 助手。

本基线已完成：

- 新增 `backend/app/services/provider_test_service.py`。
- `/admin/providers` 中每个已保存 provider 增加“测试连接”按钮。
- 测试连接会验证 Base URL、API Key、模型名和 OpenAI-compatible `chat/completions` 响应格式。
- 新增 `frontend/src/api/chat.js`。
- 前端主页面新增 AI 助手面板，调用 `/api/chat`。
- AI 助手使用后端 TextProvider；图片识别继续使用 VisionProvider。
- VisionProvider 和 TextProvider 可在后端管理页面分别配置为不同 API。

已知限制：

- 测试连接只验证基础 `chat/completions` 连通性；视觉图片能力仍需通过图片识别接口验证。
- 前端 AI 助手仍是单页面板，没有独立会话历史持久化。

## v0.5.4 backend provider admin baseline

日期：2026-04-29

该版本撤回“普通用户在前端自配 API”的方案，改为由项目维护者在后端 WebUI 中配置平台统一承担的 Vision/Text LLM API。

本基线已完成：

- 移除前端模型配置管理面板。
- 删除前端 `frontend/src/api/modelConfigs.js`。
- 新增后端 `/admin/providers` WebUI。
- 新增 `ADMIN_WEBUI_TOKEN` 管理员令牌配置。
- `/api/model-configs` 改为管理员令牌保护，需要 `X-Admin-Token`。
- `/api/predict`、`/api/advice/generate`、`/api/chat` 改为使用全局启用 provider，不再读取用户级 provider。
- Provider API Key 仍由后端加密入库，不在前端用户界面暴露。

已知限制：

- 管理后台当前是轻量 HTML 表单，没有细粒度管理员账号体系。
- 尚未提供 provider 测试连接按钮。

## v0.5.3 frontend provider management baseline

日期：2026-04-29

该版本新增前端模型配置管理页面，让登录用户在界面中维护自己的 VisionProvider 和 TextProvider。

该方案已被 v0.5.4 撤回：普通用户不再维护 API，模型 API 改由后端管理员统一配置。

本基线已完成：

- 新增 `frontend/src/api/modelConfigs.js`，封装 `/api/model-configs` 增删改查。
- 主页面新增“模型配置”面板。
- 登录后可新增 VisionProvider / TextProvider。
- 支持编辑 provider 名称、类型、Base URL、模型名和启用状态。
- 编辑时 API Key 留空会保留原密钥。
- 支持启用/停用和删除当前用户自己的 provider。
- 未登录时只展示登录提示，不操作全局演示 provider。

已知限制：

- 当前仍是单页工作台，没有独立模型配置路由。
- 前端未直接测试外部模型连通性，后续可增加“测试连接”按钮。

## v0.5.2 legacy entry cleanup baseline

日期：2026-04-29

该版本清理旧运行入口和旧部署残留，避免新开发者误用 Flask/Streamlit 旧主线。

本基线已完成：

- 删除根目录 `app.py` 旧 Flask 下线提示入口。
- 删除根目录 `webapp.py` 旧 Streamlit Demo。
- 删除根目录 `Procfile` 和 `setup.sh` 旧 Streamlit/Heroku 部署残留。
- 删除根目录旧 `requirements.txt`，后端依赖统一使用 `backend/requirements.txt`。
- 清理本地临时 SQLite 探测文件、旧 `__pycache__` 和空 `templates/` 目录。
- 更新 README 和 legacy 快照，明确当前入口为 `start.py`、`start_frontend.py` 和 `backend/app/main.py`。

已知限制：

- `final_model.h5`、Notebook、PPT、策划书仍作为 legacy 资料保留。
- `main/` 下训练脚本和 Notebook 仍待后续归档或迁移，不参与新系统运行。

## v0.5.1 SQLite local start baseline

日期：2026-04-29

该版本将本地开发和短期演示默认数据库切回 SQLite，并新增 Python 构建/启动入口。

本基线已完成：

- 后端默认 `DATABASE_URL` 从 PostgreSQL 改为 `backend/sazj.sqlite3` 对应的 SQLite URL。
- SQLite 默认启用 `SQLITE_JOURNAL_MODE=OFF`，用于兼容当前 Windows 本地磁盘环境。
- 新增根目录 `start.py`，默认设置 SQLite、上传目录、日志目录并启动 FastAPI。
- 新增根目录 `build.py`，用于安装后端依赖，并可选安装/构建前端。
- 新增根目录 `start_frontend.py`，用于通过 Python 启动前端开发服务。
- `backend/.env.example` 改为 SQLite 默认配置。
- README 和 Windows 部署文档改为 SQLite 默认、PostgreSQL 可选。
- NSSM 文档改为通过 `python start.py` 启动后端服务。

已知限制：

- SQLite 适合本地开发和短期演示，不适合作为长期高并发数据库。
- 如果后续切换 PostgreSQL，需要重新配置 `DATABASE_URL` 并做迁移方案。

## v0.5.0 user-scoped provider config baseline

日期：2026-04-29

该版本将模型配置改为用户级配置。

本基线已完成：

- `model_configs` 新增可选 `user_id`。
- 登录用户创建 provider 时自动绑定当前用户。
- 登录用户列表、查看、更新、删除 provider 时只能操作自己的配置。
- 登录用户调用 `/api/predict` 时只使用自己的 VisionProvider。
- 登录用户调用 `/api/advice/generate` 和 `/api/chat` 时只使用自己的 TextProvider。
- 未登录请求仍使用 `user_id=null` 的全局演示 provider。
- 旧表缺少 `model_configs.user_id` 时，开发期启动会自动补列。

已知限制：

- 前端尚未提供模型配置管理页面。
- 全局演示 provider 仍保留，用于未登录演示流程。
- 正式迁移阶段仍需用 Alembic 替代自动补列。

## v0.4.9 frontend auth and user-scoped history baseline

日期：2026-04-29

该版本新增前端登录/注册界面和登录态管理，并让历史记录优先使用当前用户上下文。

本基线已完成：

- 新增 `frontend/src/api/auth.js`。
- 前端主页面新增登录/注册面板。
- 前端使用 `localStorage` 保存 access token。
- `/api/predict` 请求会在登录后携带 Bearer Token。
- `/api/history`、`GET /api/history/{id}`、`DELETE /api/history/{id}` 会在登录后携带 Bearer Token。
- 后端 `prediction_records` 新增可选 `user_id`。
- 登录用户新增识别记录时会绑定当前用户。
- 登录用户查询、查看、删除历史记录时，只操作自己的记录。
- 未登录时保留全局历史记录视图。

已知限制：

- 模型配置用户隔离已在 v0.5.0 完成。
- 上传原图尚未保存到文件系统。
- 前端仍是单页工作台，没有独立路由和用户资料页。

## v0.4.8 history paging delete and auth baseline

日期：2026-04-29

该版本新增历史记录分页、删除接口，并建立用户注册登录基础能力。

本基线已完成：

- `GET /api/history` 改为分页响应，包含 `items`、`total`、`limit`、`offset`。
- 新增 `DELETE /api/history/{id}`。
- 前端历史列表支持上一页、下一页和删除选中记录。
- 新增 `users` 表。
- 新增 `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`。
- 密码使用 PBKDF2 哈希保存。
- 登录返回 Bearer Token。

已知限制：

- 历史记录和模型配置尚未按用户隔离。
- 前端尚未提供登录注册页面。
- Token 使用当前项目内置的轻量 HS256 实现，后续可按需要替换为成熟认证库。

## v0.4.7 frontend history detail baseline

日期：2026-04-29

该版本新增前端历史记录详情面板。

本基线已完成：

- 点击历史记录列表中的一条记录后，调用 `GET /api/history/{id}`。
- 详情面板展示病害名称、风险等级、识别时间、置信度、provider、模型名。
- 详情面板展示摘要、防治建议和原始模型输出。

已知限制：

- 当前详情面板仍使用全局历史记录。
- 尚未提供历史删除、分页控件和独立详情路由。
- 尚未绑定用户系统。

## v0.4.6 frontend history list baseline

日期：2026-04-29

该版本新增前端历史记录列表。

本基线已完成：

- 新增 `frontend/src/api/history.js`。
- 主页面加载时调用 `GET /api/history`。
- 识别成功后自动刷新历史记录。
- 前端展示识别时间、病害名称、风险等级、provider 和模型名。

已知限制：

- 当前仍是全局历史记录。
- 已在 v0.4.7 提供历史详情面板，删除按钮和分页控件尚未实现。
- 尚未绑定用户系统。

## v0.4.5 history query API baseline

日期：2026-04-29

该版本新增历史记录查询 API。

本基线已完成：

- 新增 `backend/app/api/history.py`。
- 新增 `GET /api/history`，按创建时间倒序返回识别记录列表。
- 新增 `GET /api/history/{id}`，返回单条识别记录详情。
- `GET /api/history` 支持 `limit` 查询参数，范围为 1 到 100，默认 20。

已知限制：

- 当前历史记录是全局列表，尚未按用户隔离。
- 尚未提供删除历史记录接口。
- 尚未提供前端历史记录页面。

## v0.4.4 prediction records baseline

日期：2026-04-29

该版本实现识别记录持久化的第一版。

本基线已完成：

- 新增 `backend/app/models/prediction_record.py`，定义 `prediction_records` 表。
- 新增 `backend/app/schemas/prediction_record.py`。
- 新增 `backend/app/repositories/prediction_record_repository.py`。
- `/api/predict` 成功识别后会写入识别记录。
- `PredictResponse` 新增 `record_id`，便于后续历史记录和排查。

当前保存字段：

- provider 名称、模型名。
- 疾病名称、风险等级、置信度。
- 摘要、建议、原始模型文本。
- 上传文件名、图片 Content-Type、创建时间。

已知限制：

- 尚未实现用户系统，识别记录暂未绑定用户。
- 尚未保存上传原图文件路径。
- 已在 v0.4.5 提供全局历史记录查询 API，前端页面尚未实现。

## v0.4.3 encrypted provider credentials baseline

日期：2026-04-29

该版本实现 Provider API Key 加密存储。

本基线已完成：

- 新增 `backend/app/core/crypto.py`。
- 新增 `PROVIDER_SECRET_KEY` 配置，要求至少 32 个字符。
- 创建或更新 `/api/model-configs` 时，`api_key` 会加密后写入数据库。
- 读取 provider 配置给 VisionProvider / TextProvider 使用时，会在后端内存中解密。
- API 响应继续只返回 `api_key_masked`，不返回明文。

已知限制：

- 历史数据库中已经存在的明文 API Key 不会自动批量迁移，需要重新保存对应模型配置。
- `PROVIDER_SECRET_KEY` 变更后，旧的加密 API Key 无法解密，需要重新配置 provider。
- 用户系统尚未实现，模型配置仍是全局配置。

## v0.4.2 Windows runtime settings baseline

日期：2026-04-29

该版本将 Windows Server 部署运行参数落到后端代码中。

本基线已完成：

- 后端读取 `UPLOAD_DIR` 和 `LOG_DIR`。
- 后端启动时自动创建上传目录和日志目录。
- 新增轻量滚动日志，默认写入 `LOG_DIR/backend.log`。
- 后端读取 `DB_POOL_SIZE`、`DB_MAX_OVERFLOW`、`DB_POOL_TIMEOUT`、`DB_POOL_RECYCLE`。
- PostgreSQL 连接池默认调整为适合 2 核 2GB 服务器的保守配置：常驻连接 2 个，临时溢出连接 1 个。
- 根目录 `.env` 和 `backend/.env` 均可读取，`backend/.env` 优先覆盖。

已知限制：

- 上传文件保存功能尚未正式接入，当前只是目录和配置基线。
- 日志已写入文件，但尚未接入 `system_logs` 表或管理端查看页面。
- Provider API Key 加密已在 v0.4.3 完成。

## v0.4.1 Windows Server deployment plan

日期：2026-04-29

该版本将默认部署目标从 Ubuntu 入门级服务器调整为 Windows Server 轻量云服务器。

本基线已完成：

- 新增 `deploy/windows_server_deploy.md`，说明 Windows Server 上 Python、Node.js、PostgreSQL、前端构建、后端启动、反向代理和验收流程。
- 新增 `deploy/windows_nssm_service.md`，说明如何用 NSSM 把 FastAPI/Uvicorn 注册为 Windows 服务。
- 新增 `deploy/windows_env_example.md`，提供 Windows Server `.env` 配置示例。
- 新增 `deploy/windows_firewall_notes.md`，说明 Windows 防火墙、云服务器安全组和公网访问排查。
- README 的默认部署目标改为 Windows Server 2 核 2GB。

已知限制：

- 该版本只调整部署文档和后续计划，不新增用户系统、历史记录或日志入库能力。
- 当前后端服务仍未实现 provider API Key 加密，下一阶段继续处理。
- PostgreSQL 迁移仍暂用 `AUTO_CREATE_TABLES=true`，尚未接入 Alembic。

## v0.4.0 PostgreSQL model config baseline

日期：2026-04-29

该版本接入 PostgreSQL/SQLAlchemy 的第一步：将模型配置从内存仓储切换为数据库仓储。

本基线已完成：

- 新增 `backend/app/db/`，包含 SQLAlchemy `Base`、engine、session 和建表入口。
- 新增 `backend/app/models/model_config.py`，定义 `model_configs` 表。
- 重写 `backend/app/repositories/model_config_repository.py`，模型配置增删改查改为数据库操作。
- 后端启动时可按 `AUTO_CREATE_TABLES=true` 自动创建表。
- `/api/model-configs` 已通过数据库持久化配置。
- VisionProvider / TextProvider 读取启用 provider 时改为读取数据库配置。

已知限制：

- 当前仅持久化模型配置。
- API Key 当前仍是明文字段，下一阶段必须加密保存。
- 尚未接入 Alembic，开发期暂用 `create_all`。
- 识别结果、用户历史、区域统计和日志尚未入库。

## v0.3.0 api-provider baseline

日期：2026-04-29

该版本根据新技术路线切换为纯 API 驱动的大模型方案。本地 CNN、TensorFlow、Kaggle/PlantVillage 和训练脚本不再作为新系统主线。

本基线已完成：

- 移除后端主线对 TensorFlow、NumPy、Pillow 的依赖。
- 新增 `backend/app/providers/vision_provider.py`，用于调用用户配置的 Vision LLM API。
- 新增 `backend/app/providers/text_provider.py`，用于调用用户配置的 Text LLM API。
- 新增模型配置结构和 API：`/api/model-configs`。
- `POST /api/predict` 改为通过 VisionProvider 调用外部视觉模型。
- 新增 `POST /api/advice/generate`，通过 TextProvider 生成防治建议。
- 新增 `POST /api/chat`，通过 TextProvider 提供网页 AI 助手能力。
- `final_model.h5` 和 `main/` 下训练残留只作为 legacy 资料记录，不参与运行。

## v0.2.0 prediction API baseline

日期：2026-04-29

该版本曾将旧 Flask 中的图片预测逻辑迁入 FastAPI 后端服务层，并新增 `POST /api/predict`。该路线已被 v0.3.0 替换：本地 CNN 不再作为新系统主线。

## v0.1.0 structure baseline

日期：2026-04-29

该版本建立前后端分离的目录骨架。

## v0.0.0 legacy baseline

日期：2026-04-28

该版本用于记录结构化重构前的项目接手状态。

## 计划 v0.5.0 encrypted provider credentials

- 对 API Key / Token 做加密保存。
- 增加 `.env` 中的加密密钥配置。
- 避免数据库中出现明文 provider 凭据。

## 计划 v0.6.0 prediction records baseline

- 持久化识别记录。
- 记录 provider、模型名、识别摘要、风险等级、用户和区域信息。
- 为用户历史和区域统计做数据基础。

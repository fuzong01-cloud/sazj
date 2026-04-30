# 版本历史

## v0.6.0 streaming WebUI baseline

日期：2026-04-30

该版本把前端体验推进到 ChatGPT 风格的对话式 WebUI，并补齐流式输出、深度思考、网页搜索和用户会话历史的主路径。

本基线已完成：

- 前端改为左侧历史侧边栏 + 中央对话框 + 底部输入框结构。
- 侧边栏支持收起和展开，收起后只保留展开按钮，主聊天区位置保持稳定。
- 侧边栏展示品牌、创建新聊天、搜索聊天、历史对话和底部用户信息。
- 历史对话支持悬停菜单、删除和重命名，重命名改为弹窗输入，不再使用浏览器 `prompt`。
- 移除历史列表分页控件，避免在短列表中占用空间。
- 主聊天区不再显示头像，用户消息右对齐并使用淡灰色圆角气泡，AI 消息左对齐。
- 消息操作按钮改为图标按钮，复制和重试图标来自 `frontend/public/Resource/`。
- 模型选择下拉框只展示 Provider 名称，不再展示真实模型 ID。
- 输入框支持点击上传、页面任意区域拖拽上传、剪贴板粘贴图片。
- 加号扩展菜单支持上传图片/文件、获取天气和位置、网页搜索。
- 天气位置和网页搜索启用后以绿色圆角标签显示，可单独取消。
- 深度思考改为输入框内圆角按钮，开启时使用绿色重点色。
- 前端支持 Markdown 渲染 AI 回复。
- 推理过程支持展示、默认展开/收起策略、思考中状态、耗时显示和自动滚动到底部。
- 后端 `/api/chat/stream` 和 `/api/predict/stream` 返回 SSE，并增加反缓冲响应头。
- Provider 运行时支持流式 `chat/completions`，能解析普通内容和推理内容。
- 新增网页搜索服务，回答前可把搜索结果作为上下文传给模型。

已知限制：

- 实际流式体验取决于上游模型是否流式返回、网络代理是否缓冲，以及浏览器是否及时刷新。
- 网页搜索当前是轻量实现，结果质量和可用性依赖外部搜索页面。
- 深度思考内容的字段名兼容不同模型仍需继续扩展。

## v0.5.9 provider runtime and Kimi compatibility baseline

日期：2026-04-30

该版本重点修复后台 Provider 测试成功但前台真实调用失败的问题，统一测试连接、文本聊天和视觉识别的运行时链路。

本基线已完成：

- 抽出通用 OpenAI-compatible `chat/completions` 运行时。
- 修复 Kimi / Moonshot URL 拼接，避免 `/v1/v1/chat/completions` 和 `/responses`。
- 文本聊天使用最小兼容 payload，不默认附加不确定参数。
- 图片识别使用多模态 `messages`，把上传图片转为 `data:image/...;base64,...`。
- 修复前端把展示字符串当成真实模型名的问题。
- 后端错误回显中保留上游 `error.message`，不再只显示 HTTP 400。
- 后台 Provider 测试增加实际请求 URL、payload、上游状态码和响应摘要日志，且不打印 API Key。
- 修复 `provider_test_service.py` 缺少 `import httpx` 导致 `/admin/providers/test` 500 的问题。

已知限制：

- 视觉识别能力取决于所选模型是否支持图片输入。
- 不同供应商的多模态字段兼容性仍需按实际模型继续适配。

## v0.5.8 conversation and profile baseline

日期：2026-04-30

该版本把前端历史从“识别记录列表”推进为“用户会话历史”，并补充个人资料能力。

本基线已完成：

- 新增会话历史接口：`/api/conversations`。
- 纯文本聊天、图片识别和带附件消息统一创建 conversation。
- 用户发送第一条消息时，如无 `conversation_id`，后端会创建新会话并返回 ID。
- 前端收到 `conversation_id` 后自动更新当前会话并刷新侧边栏历史。
- 模型调用失败时仍保存用户消息和错误状态，避免用户输入丢失。
- 会话标题默认使用第一条用户消息生成。
- 用户资料支持用户名、邮箱、头像和密码修改。
- 头像上传保存到服务器上传目录。
- 前端登录状态与用户信息面板打通。

已知限制：

- 当前会话消息结构已经满足演示，但还没有做复杂搜索、归档和多端同步策略。
- 用户权限仍是轻量实现，尚未引入管理员账号体系。

## v0.5.7 unified provider admin baseline

日期：2026-04-30

该版本撤回“普通用户自行配置 API”的产品路线，改为平台维护者在后端 WebUI 统一配置大模型 API。

本基线已完成：

- 普通前端移除用户级模型配置管理入口。
- 后端 `/admin/providers` 作为模型配置 WebUI。
- `ADMIN_WEBUI_TOKEN` 用于保护管理页。
- Provider API Key 继续加密入库。
- Provider 类型从强 Vision/Text 认知逐步弱化为通用模型配置。
- 文本聊天和图片识别默认使用同一个当前选择的 Provider。
- 管理端增加快速模型、深度思考模型、上下文长度、最大输出长度等配置项。
- 前端模型选择只展示 Provider 名称，真实模型名只由后端运行时使用。

已知限制：

- 管理端仍是轻量 HTML 表单，尚未做完整后台系统。
- 供应商能力差异仍依赖管理员正确配置和测试。

## v0.5.6 weather-aware prediction baseline

日期：2026-04-29

该版本新增定位、天气和气候带上下文，并接入图片识别提示词。

本基线已完成：

- 新增 `GET /api/weather`。
- 后端按纬度粗分气候带：热带、亚热带、温带、高纬/寒温带。
- `/api/predict` 支持 `latitude`、`longitude`、`location_label`。
- 图片识别提示词会包含位置、天气、湿度、降水和气候带。
- 前端可通过浏览器定位获取天气信息。

已知限制：

- 气候带判断是粗粒度实现，尚未结合海拔、地形、长期气候统计和区域病害流行数据。

## v0.5.5 provider test and assistant baseline

日期：2026-04-29

该版本新增后端 Provider 测试连接按钮，并在普通前端增加 AI 助手。

本基线已完成：

- 新增 `backend/app/services/provider_test_service.py`。
- `/admin/providers` 中每个已保存 Provider 增加“测试连接”按钮。
- 测试连接验证 Base URL、API Key、模型名和 `chat/completions` 响应格式。
- 前端主页面新增 AI 助手入口。
- AI 助手调用后端模型 Provider。

已知限制：

- 测试连接只验证基础文本调用，视觉能力需要通过图片识别接口验证。

## v0.5.4 backend provider admin baseline

日期：2026-04-29

该版本撤回“普通用户在前端自配 API”的方案，改为由项目维护者在后端 WebUI 中配置平台统一承担的大模型 API。

本基线已完成：

- 移除前端用户级模型配置管理面板。
- 新增后端 `/admin/providers` WebUI。
- 新增 `ADMIN_WEBUI_TOKEN`。
- `/api/model-configs` 改为管理员令牌保护。
- Provider API Key 加密入库，不在普通用户界面暴露。

已知限制：

- 管理后台是轻量 HTML 表单，没有细粒度管理员账号体系。

## v0.5.3 frontend provider management baseline

日期：2026-04-29

该版本曾新增前端模型配置管理页面，让登录用户维护自己的 VisionProvider 和 TextProvider。

该方案已被 v0.5.4 之后的路线撤回：普通用户不再维护 API，模型 API 改由后端管理员统一配置。

## v0.5.2 legacy entry cleanup baseline

日期：2026-04-29

该版本清理旧运行入口和旧部署残留，避免新开发者误用 Flask/Streamlit 旧主线。

本基线已完成：

- 删除根目录 `app.py` 旧 Flask 下线提示入口。
- 删除根目录 `webapp.py` 旧 Streamlit Demo。
- 删除根目录 `Procfile` 和 `setup.sh`。
- 删除根目录旧 `requirements.txt`，后端依赖统一使用 `backend/requirements.txt`。
- 更新 README 和 legacy 快照，明确当前入口为 `start.py`、`start_frontend.py` 和 `backend/app/main.py`。

## v0.5.1 SQLite local start baseline

日期：2026-04-29

该版本将本地开发和短期演示默认数据库切回 SQLite，并新增 Python 构建/启动入口。

本基线已完成：

- 后端默认 `DATABASE_URL` 改为 SQLite。
- 新增根目录 `start.py`。
- 新增根目录 `build.py`。
- 新增根目录 `start_frontend.py`。
- `backend/.env.example` 改为 SQLite 默认配置。
- README 和 Windows 部署文档改为 SQLite 默认、PostgreSQL 可选。
- NSSM 文档改为通过 `python start.py` 启动后端服务。

已知限制：

- SQLite 适合本地开发和短期演示，不适合作为长期高并发数据库。

## v0.5.0 user-scoped provider config baseline

日期：2026-04-29

该版本曾将模型配置改为用户级配置。

该路线后来被后端统一 Provider 管理替代。历史意义是验证了用户上下文、Provider 隔离和数据库字段扩展能力。

## v0.4.9 frontend auth and user-scoped history baseline

日期：2026-04-29

该版本新增前端登录/注册界面和登录态管理，并让历史记录优先使用当前用户上下文。

本基线已完成：

- 前端支持登录/注册。
- 前端使用 `localStorage` 保存 access token。
- 登录后请求携带 Bearer Token。
- 登录用户新增识别记录时会绑定当前用户。
- 登录用户查询、查看、删除历史记录时优先操作自己的记录。

## v0.4.8 history paging delete and auth baseline

日期：2026-04-29

该版本新增历史记录分页、删除接口，并建立用户注册登录基础能力。

本基线已完成：

- `GET /api/history` 支持分页。
- 新增 `DELETE /api/history/{id}`。
- 新增 `users` 表。
- 新增 `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`。
- 密码使用 PBKDF2 哈希保存。

## v0.4.7 frontend history detail baseline

日期：2026-04-29

该版本新增前端历史记录详情面板，展示摘要、建议、置信度和原始模型输出。

## v0.4.6 frontend history list baseline

日期：2026-04-29

该版本新增前端历史记录列表，识别成功后自动刷新历史记录。

## v0.4.5 history query API baseline

日期：2026-04-29

该版本新增 `GET /api/history` 和 `GET /api/history/{id}`。

## v0.4.4 prediction records baseline

日期：2026-04-29

该版本实现识别记录持久化第一版。

本基线已完成：

- 新增 `prediction_records` 表。
- `/api/predict` 成功识别后写入识别记录。
- 保存 Provider、模型名、疾病名称、风险等级、置信度、摘要、建议、原始模型文本、上传文件名和创建时间。

## v0.4.3 encrypted provider credentials baseline

日期：2026-04-29

该版本实现 Provider API Key 加密存储。

本基线已完成：

- 新增 `PROVIDER_SECRET_KEY`。
- 创建或更新 Provider 时加密 API Key。
- API 响应只返回脱敏字段，不返回明文。

## v0.4.2 Windows runtime settings baseline

日期：2026-04-29

该版本将 Windows Server 部署运行参数落到后端代码中。

本基线已完成：

- 后端读取 `UPLOAD_DIR` 和 `LOG_DIR`。
- 后端启动时自动创建上传目录和日志目录。
- 新增轻量滚动日志。
- PostgreSQL 连接池配置曾按 2 核 2GB 服务器做过保守设置。

当前说明：

- 项目后来把默认演示数据库切回 SQLite，PostgreSQL 仅作为后续可选方案。

## v0.4.1 Windows Server deployment plan

日期：2026-04-29

该版本将默认部署目标从 Ubuntu 入门级服务器调整为 Windows Server 轻量云服务器。

本基线已完成：

- 新增 `deploy/windows_server_deploy.md`。
- 新增 `deploy/windows_nssm_service.md`。
- 新增 `deploy/windows_env_example.md`。
- 新增 `deploy/windows_firewall_notes.md`。

## v0.4.0 PostgreSQL model config baseline

日期：2026-04-29

该版本曾接入 PostgreSQL/SQLAlchemy 的第一步，将模型配置从内存仓储切换为数据库仓储。

当前说明：

- SQLAlchemy 数据层继续保留。
- 默认数据库已经切回 SQLite。
- PostgreSQL 暂时不是短期演示默认路径。

## v0.3.0 api-provider baseline

日期：2026-04-29

该版本根据新技术路线切换为纯 API 驱动的大模型方案。本地 CNN、TensorFlow、Kaggle/PlantVillage 和训练脚本不再作为新系统主线。

本基线已完成：

- 移除后端主线对 TensorFlow、NumPy、Pillow 的依赖。
- 新增模型 Provider 抽象。
- `POST /api/predict` 改为通过外部视觉模型识别。
- 新增 `POST /api/advice/generate`。
- 新增 `POST /api/chat`。
- `final_model.h5` 和 `main/` 下训练残留只作为 legacy 资料记录。

## v0.2.0 prediction API baseline

日期：2026-04-29

该版本曾将旧 Flask 中的图片预测逻辑迁入 FastAPI 后端服务层，并新增 `POST /api/predict`。该路线已被 v0.3.0 替换：本地 CNN 不再作为新系统主线。

## v0.1.0 structure baseline

日期：2026-04-29

该版本建立前后端分离目录骨架。

## v0.0.0 legacy baseline

日期：2026-04-28

该版本记录结构化重构前的项目接手状态。原项目包含演示型 Flask/Streamlit/Notebook/Colab/Kaggle 残留、旧模型文件、PPT 和策划书。当前新系统已把这些内容作为 legacy 资料保留，不再进入主线运行。

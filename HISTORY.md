# 版本历史

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
- Provider API Key 仍未加密，下一阶段继续处理。

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

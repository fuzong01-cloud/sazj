# 版本历史

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

已知限制：

- 模型配置当前暂存在内存中，尚未写入 PostgreSQL。
- API Key 当前仅在内存中保存，尚未实现加密持久化。
- 识别历史、区域统计、日志记录尚未持久化。
- Vision/Text Provider 当前按 OpenAI-compatible `chat/completions` 格式实现，后续可扩展厂商适配器。

## v0.2.0 prediction API baseline

日期：2026-04-29

该版本曾将旧 Flask 中的图片预测逻辑迁入 FastAPI 后端服务层，并新增 `POST /api/predict`。该路线已被 v0.3.0 替换：本地 CNN 不再作为新系统主线。

## v0.1.0 structure baseline

日期：2026-04-29

该版本建立前后端分离的目录骨架。

## v0.0.0 legacy baseline

日期：2026-04-28

该版本用于记录结构化重构前的项目接手状态。

## 计划 v0.4.0 PostgreSQL persistence baseline

- 接入 PostgreSQL。
- 增加数据库迁移。
- 持久化模型配置。
- 持久化识别记录、用户历史、区域统计和系统日志。
- 对 API Key / Token 做加密保存。

## 计划 v0.5.0 user and history baseline

- 实现用户注册和登录。
- 实现用户级模型配置管理。
- 实现识别历史查询。
- 实现区域统计基础接口。

## 计划 v0.6.0 knowledge and operations baseline

- 增加知识库增强。
- 增加防治建议管理。
- 增加风险预警。
- 增加结构化日志、指标和部署文档。

# 版本历史

## v0.1.0 structure baseline

日期：2026-04-29

该版本建立前后端分离的目录骨架，同时保留旧 Flask 应用可运行。

本基线已完成：

- 新增 `backend/`，作为后续 FastAPI 后端目录。
- 新增 `GET /api/health` 健康检查接口。
- 新增 `GET /api/model/status` 模型文件状态接口。
- 新增 `frontend/`，作为后续 Vue + Vite 前端目录。
- 新增前端健康检查调用，用于验证前端能连接后端。
- 保留根目录 `app.py`、`templates/index.html` 和 `final_model.h5` 不变，旧 Flask 版本仍可启动。

已知限制：

- 新 FastAPI 后端目前不加载模型，不执行图片识别。
- 新 Vue 前端目前只是结构基线，不承接旧 Flask 页面的完整业务。
- 数据库、用户系统、历史记录、区域统计、日志监控和部署脚本仍待后续阶段实现。

## v0.0.0 legacy baseline

日期：2026-04-28

该版本用于记录结构化重构前的项目接手状态。

本基线已完成：

- 确认 `app.py` 是当前 Flask 运行基线。
- 确认 `templates/index.html` 和 `final_model.h5` 是当前 Flask 应用运行所需文件。
- 确认 `webapp.py`、`Procfile` 和 `setup.sh` 是遗留 Streamlit 部署或 Demo 残留。
- 确认 `main/Potato Leaf Disease Prediction.py` 和 Notebook 文件是 Colab/Kaggle 训练残留。
- 新增面向 GitHub 首页展示的项目文档。
- 新增遗留快照文档，用于后续清理规划。
- 围绕当前 Flask 基线整理 `requirements.txt`。

已知限制：

- 项目尚未前后端分离。
- FastAPI、Vue、PostgreSQL、认证、历史记录、统计、加密、高并发控制、日志和监控均尚未实现。
- 当前模型文件和训练残留仍来自接手时的演示项目脉络。
- 当前页面和 Python 文件仍存在命名混乱、职责混杂和文本编码风险。

## 计划 v0.2.0 识别 API 基线

- 将预测逻辑移动到后端服务层接口后面。
- 增加稳定的 `POST /api/predict` 合同。
- 增加模型适配器边界，避免后续模型替换继续绑定旧 Kaggle/Colab 代码。

## 计划 v0.3.0 持久化基线

- 增加 PostgreSQL 连接配置。
- 增加数据库迁移。
- 增加用户、识别记录、模型提供商配置、区域和系统日志等表。

## 计划 v0.4.0 产品功能

- 实现用户注册和登录。
- 持久化识别历史。
- 增加区域统计。
- 增加用户自行配置 OpenAI-compatible 模型提供商的能力。
- 对敏感的模型提供商凭据进行加密保存。

## 计划 v0.5.0 运维基线

- 增加结构化请求日志和错误日志。
- 增加轻量指标和健康检查。
- 增加 Ubuntu 入门级服务器部署文档。
- 增加基础并发保护，例如上传大小限制、超时控制和请求限流。

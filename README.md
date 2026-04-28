# 薯安智检农业病害识别平台

薯安智检是一个农业病害识别项目，当前正从演示型马铃薯叶片病害识别 Demo，逐步改造成可维护、可部署、可扩展的 Web 平台。

本仓库目前处于遗留基线整理阶段。当前可运行版本仍是 Flask 单体应用：加载 `final_model.h5`，渲染 `templates/index.html`，接收图片上传并返回识别结果；在配置了 OpenAI-compatible 接口环境变量时，可以生成辅助分析建议。目标架构是 Vue + JavaScript 前端、Python FastAPI 后端和 PostgreSQL 数据库。

## 当前状态

- 版本基线：`v0.0.0 legacy baseline`。
- 当前可运行入口：`app.py`。
- 当前页面：Flask 模板 `templates/index.html`。
- 当前模型文件：`final_model.h5`。
- 当前可选外部服务：Open-Meteo 天气接口，以及通过环境变量配置的 Moonshot/OpenAI-compatible 聊天接口。
- 尚未实现：Vue 前端、FastAPI 后端、PostgreSQL、用户系统、历史记录、区域统计、数据加密、高并发控制、日志、监控、用户自定义大模型提供商配置。

## 技术栈

当前遗留运行栈：

- Python
- Flask
- TensorFlow / Keras
- NumPy
- Pillow
- Requests
- OpenAI Python SDK，仅在配置兼容接口的 API Key 和 Base URL 时使用

目标技术路线：

- 前端：Vue + JavaScript，按 MVVM 思路组织代码
- 后端：Python + FastAPI
- 数据库：PostgreSQL
- 部署：面向 Ubuntu 入门级服务器的轻量、清晰、可复现方案

## 仓库结构

当前结构：

```text
.
|-- app.py                                  # 当前 Flask 运行基线
|-- templates/index.html                    # 当前 Flask 页面
|-- final_model.h5                          # 遗留模型文件
|-- requirements.txt                        # Flask 基线最小依赖
|-- webapp.py                               # 遗留 Streamlit Demo，不作为当前运行基线
|-- Procfile                                # 遗留 Streamlit 部署配置
|-- setup.sh                                # 遗留 Streamlit 配置脚本
|-- main/
|   |-- Potato Leaf Disease Prediction.py   # Colab/Kaggle 风格训练残留
|   |-- Potato Leaf Disease Classification.ipynb
|   |-- Potato Leaf Disease Classification (COLAB).ipynb
|   `-- sample/potato.png
|-- docs/
|   `-- legacy_snapshot.md
|-- README.md
`-- HISTORY.md
```

后续建议结构，本阶段暂不创建或迁移：

```text
.
|-- backend/
|   `-- app/
|       |-- api/
|       |-- core/
|       |-- models/
|       |-- schemas/
|       |-- services/
|       `-- main.py
|-- frontend/
|   `-- src/
|       |-- api/
|       |-- assets/
|       |-- components/
|       |-- router/
|       |-- store/
|       `-- views/
|-- docs/
|-- deploy/
|-- models/
`-- legacy/
```

## 本地启动

PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Linux 或 macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

启动后访问：

```text
http://127.0.0.1:5000
```

可选环境变量：

```text
MODEL_PATH=final_model.h5
MOONSHOT_API_KEY=
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2.5
```

当 `MOONSHOT_API_KEY` 为空时，应用仍应可以启动，并使用本地兜底建议逻辑。

## 开发计划

1. 保留并记录当前可运行基线。
2. 隔离 Notebook、Colab、Kaggle 和原 Demo 残留，不直接删除重要文件。
3. 新增 FastAPI 后端骨架，提供健康检查和模型服务接口。
4. 新增 Vue 前端骨架，通过 API 调用后端。
5. 接入 PostgreSQL，保存用户、识别记录、模型提供商配置、区域和日志。
6. 分阶段实现用户系统、历史记录、区域统计、模型配置、数据加密、日志监控和轻量部署。

修改遗留代码前，请先阅读 `HISTORY.md` 和 `docs/legacy_snapshot.md`。


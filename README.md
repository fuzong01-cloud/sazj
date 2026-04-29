# 薯安智检农业病害识别平台

薯安智检是一个面向马铃薯病虫害场景的 AI 识别、历史记录、区域统计、风险预警、知识库增强和防治建议管理平台。

当前技术路线已经调整：新系统不再使用本地 CNN，不设计离线识别，也不围绕 Kaggle/PlantVillage 数据集或训练脚本继续开发。`final_model.h5`、Notebook/Colab 训练代码和 Kaggle 相关内容只作为 legacy 资料保留，用于说明旧项目来源和历史问题，不进入新架构主线。

## 当前状态

- 版本基线：`v0.3.0 api-provider baseline`。
- 当前后端入口：`backend/app/main.py`。
- 当前前端入口：`frontend/src/main.js`。
- 当前识别接口：`POST /api/predict`，通过用户配置的 Vision LLM API 完成。
- 当前建议接口：`POST /api/advice/generate`，通过用户配置的 Text LLM API 完成。
- 当前问答接口：`POST /api/chat`，通过用户配置的 Text LLM API 完成。
- 模型配置接口：`/api/model-configs`，当前为内存版结构基线，后续迁入 PostgreSQL。
- 旧本地模型：`final_model.h5` 仅作为 legacy 资料，不参与运行。

## 技术栈

当前运行栈：

- 后端：Python + FastAPI + Uvicorn
- 外部模型调用：httpx + OpenAI-compatible chat/completions
- 前端：Vue + Vite + JavaScript

目标技术路线：

- Vision LLM API：负责图像识别。
- Text LLM API：负责文本建议、网页 AI 助手和病害问答。
- PostgreSQL：保存模型配置、识别结果、用户历史、区域统计和日志。
- 平台不内置 API Key、Token，也不固定绑定任何厂商。

## 仓库结构

```text
.
|-- app.py                                  # 旧 Flask 页面下线提示
|-- final_model.h5                          # legacy 本地 CNN 模型资料，不参与新系统运行
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- providers/                      # VisionProvider / TextProvider
|   |   |-- repositories/                   # 临时内存仓储，后续替换为 PostgreSQL
|   |   |-- schemas/
|   |   `-- services/
|   |-- requirements.txt
|   `-- README.md
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- styles/
|   |   `-- App.vue
|   |-- package.json
|   `-- README.md
|-- main/                                   # legacy Colab/Kaggle 训练残留
|-- docs/
|   `-- legacy_snapshot.md
|-- README.md
`-- HISTORY.md
```

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

当前模型配置暂存在内存中，服务重启后会丢失。后续阶段将迁移到 PostgreSQL，并对 API Key 加密保存。

## 开发计划

1. 完成 VisionProvider / TextProvider 抽象层。
2. 完成模型配置 API，并迁移到 PostgreSQL。
3. 让识别结果、用户历史、区域统计和日志持久化。
4. 建立用户系统和权限控制。
5. 增加知识库增强、防治建议管理、风险预警和统计看板。
6. 清理或迁移 legacy 模型、Notebook、Colab、Kaggle 残留资料。

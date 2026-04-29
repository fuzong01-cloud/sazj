# 前端服务

本目录是薯安智检的 Vue + Vite 前端。当前版本提供后端健康检查、登录注册、图片上传、识别结果展示、AI 助手和历史记录详情。

## 启动方式

```powershell
python start_frontend.py
```

启动后访问：

```text
http://127.0.0.1:5173
```

## 构建

```powershell
cd frontend
npm run build
```

## 环境变量

复制 `.env.example` 为 `.env` 后可调整后端地址：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 当前能力

- 展示 FastAPI 后端连接状态。
- 支持用户登录、注册和本地 token 管理。
- 上传图片并调用 `POST /api/predict`。
- 提供 AI 助手面板并调用 `POST /api/chat`。
- 展示识别结果、置信度、provider、模型名和历史记录详情。

模型 API 由后端管理员统一配置，普通用户前端不暴露 API Key、Base URL 或模型名称配置入口。

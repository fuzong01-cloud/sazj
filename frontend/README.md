# 前端服务

本目录是薯安智检的 Vue + Vite 前端。当前版本提供后端健康检查、图片上传和识别结果展示。

## 启动方式

```powershell
cd frontend
npm install
npm run dev
```

启动后访问：

```text
http://127.0.0.1:5173
```

## 构建

```powershell
npm run build
```

## 环境变量

复制 `.env.example` 为 `.env` 后可调整后端地址：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 当前能力

- 展示 FastAPI 后端连接状态。
- 上传图片并调用 `POST /api/predict`。
- 展示识别类别、置信度和各类别概率。

# 前端结构基线

本目录是后续 Vue 前端的结构基线，目前只提供一个可运行的 Vite + Vue 页面，用于验证前后端分离后的开发入口。

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

## 当前能力

- 展示平台结构基线。
- 调用 `GET /api/health` 检查 FastAPI 后端是否可访问。
- 暂不承接旧 Flask 页面的识别业务。

## 环境变量

复制 `.env.example` 为 `.env` 后可调整后端地址：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

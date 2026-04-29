# 后端服务

本目录是薯安智检的 FastAPI 后端。当前版本已经提供健康检查、模型状态和图片识别接口。

## 启动方式

使用根目录已有 `.venv`：

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

也可以在 `backend/` 内单独创建虚拟环境：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/model/status
http://127.0.0.1:8000/docs
```

## 当前接口

- `GET /api/health`：检查后端服务是否可用。
- `GET /api/model/status`：检查当前配置的模型文件是否存在。
- `POST /api/predict`：上传图片并返回识别结果。

## 环境变量

复制 `.env.example` 为 `.env` 后可调整配置：

```text
APP_NAME=薯安智检 API
APP_ENV=development
API_PREFIX=/api
MAX_UPLOAD_BYTES=8388608
FRONTEND_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## 注意

- 当前识别通过用户配置的 Vision LLM API 完成，不加载本地 TensorFlow 模型。
- 当前模型配置暂存在内存中，尚未写入 PostgreSQL。

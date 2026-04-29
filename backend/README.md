# 后端结构基线

本目录是后续 FastAPI 后端的结构基线，目前只提供健康检查和模型状态接口，不承接旧 Flask 应用的完整业务逻辑。

## 启动方式

PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Linux：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
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

## 注意

- 当前后端不会加载模型，也不会执行识别。
- 当前后端不会替代根目录的旧 Flask 应用。
- 后续预测、用户、历史、统计、模型配置等功能应逐步放入 `app/services/`、`app/api/`、`app/schemas/` 等目录。

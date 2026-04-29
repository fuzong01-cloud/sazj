# 遗留项目快照

日期：2026-04-29

本文档记录新旧技术路线切换后的仓库状态。

## 新技术路线

新系统采用纯 API 驱动的大模型方案：

- 图像识别由用户配置的 Vision LLM API 完成。
- 文本建议、网页 AI 助手、病害问答由用户配置的 Text LLM API 完成。
- 平台本身不内置 API Key、Token，也不固定绑定 Kimi、豆包、通义、OpenAI 或其他厂商。
- 后端提供 `VisionProvider` 和 `TextProvider` 两套抽象层。
- 模型配置包括 `provider_name`、`provider_type`、`base_url`、`api_key`、`model_name`、`enabled`。
- `provider_type` 当前支持 `vision` 和 `text`。

## legacy 资料

以下内容只作为旧项目来源和历史问题说明，不进入新系统主线：

- `final_model.h5`
- `main/Potato Leaf Disease Prediction.py`
- `main/Potato Leaf Disease Classification.ipynb`
- `main/Potato Leaf Disease Classification (COLAB).ipynb`
- `main/sample/potato.png`
- Kaggle / PlantVillage 相关说明
- Colab `/content/...` 路径和训练脚本残留
- `webapp.py` Streamlit Demo
- `Procfile` 和 `setup.sh` 中的旧 Streamlit 部署路径

## 当前可运行基线

当前后端：

- `backend/app/main.py`
- `backend/app/providers/vision_provider.py`
- `backend/app/providers/text_provider.py`
- `backend/app/api/model_configs.py`
- `backend/app/api/predict.py`
- `backend/app/api/advice.py`
- `backend/app/api/chat.py`

当前前端：

- `frontend/src/App.vue`
- `frontend/src/api/health.js`
- `frontend/src/api/predict.js`

当前接口：

- `GET /api/health`
- `GET /api/model/status`
- `GET /api/model-configs`
- `POST /api/model-configs`
- `GET /api/model-configs/{id}`
- `PUT /api/model-configs/{id}`
- `DELETE /api/model-configs/{id}`
- `POST /api/predict`
- `POST /api/advice/generate`
- `POST /api/chat`

## 当前限制

- 模型配置当前暂存在内存中，服务重启会丢失。
- API Key 当前只在内存中保存，尚未加密持久化。
- 尚未接入 PostgreSQL。
- 尚未实现用户系统、历史记录、区域统计和日志记录。
- Provider 当前按 OpenAI-compatible `chat/completions` 协议实现，后续可扩展不同厂商适配器。

## 验证命令

后端依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

后端接口验证：

```powershell
cd backend
..\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.get('/api/health').status_code); print(c.get('/api/model-configs').json())"
```

前端构建：

```powershell
cd frontend
npm run build
```

预期结果：

- 后端可以导入并返回健康检查。
- 未配置 provider 时，`POST /api/predict` 返回明确的未配置提示。
- 创建 `provider_type=vision` 后，`POST /api/predict` 会调用该 Vision LLM API。
- 创建 `provider_type=text` 后，`POST /api/advice/generate` 和 `POST /api/chat` 会调用该 Text LLM API。

# 遗留项目快照

日期：2026-04-29

本文档记录结构化重构前后的仓库接手状态。本阶段目标是理解并保留当前基线，不删除重要文件，也不进行大范围重写。

## v0.1.0 结构基线补充

当前仓库已新增前后端分离骨架：

- `backend/`：FastAPI 后端结构基线。
- `frontend/`：Vue + Vite 前端结构基线。

该骨架只用于后续迁移，不替代旧 Flask 应用：

- 旧版 Flask 仍通过根目录 `app.py` 启动。
- 新 FastAPI 后端只提供健康检查和模型文件状态检查。
- 新 Vue 前端只验证前端开发入口和后端连接状态。
- 识别、天气、AI 建议、聊天等旧功能仍在 `app.py` 和 `templates/index.html` 中。

## 当前可运行基线

当前旧版可运行基线是 Flask 应用：

- `app.py`
- `templates/index.html`
- `final_model.h5`
- `requirements.txt`

已在现有本地 `.venv` 中验证：

- `app.py` 可以通过 Python 语法编译。
- `webapp.py` 可以通过 Python 语法编译。
- 导入 Flask 应用时会加载并预热 `final_model.h5`。
- Flask 测试客户端访问 `/` 返回 HTTP `200`，内容类型为 `text/html`。
- 未配置 `MOONSHOT_API_KEY` 时，应用仍可启动，并使用本地兜底 AI 建议逻辑。

`app.py` 中当前发现的 Flask 路由：

- `GET /`
- `POST /predict`
- `POST /analyze`
- `POST /chat`
- `POST /weather/by-coords`
- `POST /weather/by-city`

## 文件分类

有效运行文件：

- `app.py`：当前 Flask 应用和路由定义。
- `templates/index.html`：当前渲染页面，包含内联 CSS 和 JavaScript。
- `final_model.h5`：当前 TensorFlow/Keras 模型文件。
- `requirements.txt`：本阶段整理后的 Flask 基线最小依赖。

新增结构基线文件：

- `backend/app/main.py`：FastAPI 应用入口。
- `backend/app/api/health.py`：健康检查接口。
- `backend/app/api/model.py`：模型状态接口。
- `backend/app/services/model_registry.py`：模型文件状态检查服务。
- `backend/requirements.txt`：FastAPI 后端依赖。
- `frontend/package.json`：Vue + Vite 前端依赖和脚本。
- `frontend/src/App.vue`：前端结构基线页面。
- `frontend/src/api/health.js`：后端健康检查调用。

遗留 Demo 文件：

- `webapp.py`：Streamlit 版本 Demo，包含原作者链接页脚，后续不应保留在正式产品路径中。
- `Procfile`：指向 `streamlit run webapp.py`，与当前 Flask 基线不一致。
- `setup.sh`：写入 Streamlit 配置和 credentials，是旧 Streamlit 部署残留。

Notebook、Colab 和 Kaggle 残留：

- `main/Potato Leaf Disease Prediction.py`：包含 `!unzip` 等 Colab shell 语法、硬编码 `/content/...` 路径、Kaggle 数据集说明和原作者元信息，不是可直接运行的普通 Python 文件。
- `main/Potato Leaf Disease Classification.ipynb`：接手仓库中的空 Notebook 占位文件。
- `main/Potato Leaf Disease Classification (COLAB).ipynb`：接手仓库中的空 Notebook 占位文件。
- `main/sample/potato.png`：接手仓库中的空样例图片占位文件。

项目文档和演示材料：

- `薯安智检项目策划书.docx`
- `薯安智检项目策划书.pdf`
- `薯安智检项目策划书PPT.pptx`
- `薯安智检项目策划书PPT.pdf`
- `薯安智检项目概要介绍.docx`
- `薯安智检项目概要介绍.pdf`
- `薯安智检——马铃薯病害智能识别系统.pptx`
- `薯安智检——马铃薯病害智能识别系统 (1).pptx`
- 图片素材 `微信图片_*.png`

本地或临时文件：

- `.venv/`：本地虚拟环境，已被 Git 忽略。
- `.idea/`：IDE 元数据，已被 Git 忽略。
- `__pycache__/`：Python 字节码缓存，已被 Git 忽略。
- `~$智检项目概要介绍.docx`：Office 临时锁文件，不应提交。
- `改造计划.md`：已有规划文档，内容有参考价值，但当前终端输出可见编码显示风险。

## 主要遗留问题

- 项目仍保留单体 Flask 页面应用，前后端分离迁移刚刚开始。
- `app.py` 同时承担路由、模型加载、图片预处理、天气访问、大模型访问、兜底建议和聊天逻辑，职责过重。
- `templates/index.html` 包含大量内联样式和脚本，旧页面尚未按 Vue 或 MVVM 边界组织。
- `webapp.py` 保留原 Demo 作者标识和 Streamlit UI/部署假设。
- `main/Potato Leaf Disease Prediction.py` 包含 Colab shell 语法和 Kaggle/Google Drive 硬编码路径。
- Notebook 文件和样例图片占位文件为空。
- `Procfile` 和 `setup.sh` 指向旧 Streamlit 路径，而当前实际可运行基线是 Flask。
- 应用尚无 PostgreSQL 连接、迁移、用户系统、识别历史、区域统计、数据加密、请求限流、结构化日志和监控。
- 模型文件和演示材料集中放在仓库根目录，影响仓库浏览和维护。
- 部分源码或文档在终端输出中存在乱码风险，后续编辑前需要谨慎确认编码。

## 当前功能真实情况

旧 Flask 源码中当前可用：

- 通过 `POST /predict` 上传图片并调用模型识别。
- 通过 Open-Meteo 按浏览器定位或城市名称查询天气。
- 在配置 OpenAI-compatible 客户端后生成 AI 风格解释；未配置时使用本地兜底逻辑。
- 提供基础聊天接口，可在有识别上下文和 API Key 时回答问题。

新 FastAPI 后端当前可用：

- 通过 `GET /api/health` 返回服务健康状态。
- 通过 `GET /api/model/status` 返回模型文件存在状态。

新 Vue 前端当前可用：

- 展示结构基线页面。
- 调用后端健康检查接口并显示连接状态。

文档或 PPT 中提到但源码尚未完整实现：

- 用户注册和登录。
- 识别历史记录。
- 区域病害统计。
- PostgreSQL 持久化。
- 数据加密。
- 高并发处理。
- 日志和监控。
- 用户自行配置模型提供商。
- 生产级部署脚本。

## 建议的后续结构

不要一次性创建或迁移所有目录。下面是遗留基线稳定后的目标方向：

```text
backend/
  app/
    main.py
    api/
    core/
    models/
    schemas/
    services/
    repositories/
    utils/
frontend/
  src/
    api/
    assets/
    components/
    views/
    router/
    store/
docs/
deploy/
models/
legacy/
```

计划迁移意图：

- 在 FastAPI 后端具备等价的预测接口前，保持 `app.py` 可运行。
- 将模型加载和预测逻辑移动到后端服务层。
- 在 API 边界稳定后，再把当前 HTML 页面迁移到 Vue 前端。
- 旧 Streamlit 和 Colab 文件只在单独清理评审后迁入 `legacy/` 或删除。
- 模型文件只在启动路径和部署说明同步更新后再迁入 `models/`。

## 本阶段不要删除的文件

- `app.py`
- `templates/index.html`
- `final_model.h5`
- 项目 PPT、PDF 和 Word 文档
- 现有图片素材
- `改造计划.md`

## 后续需要评审清理的文件

- `webapp.py`
- `Procfile`
- `setup.sh`
- `main/Potato Leaf Disease Prediction.py`
- `main/Potato Leaf Disease Classification.ipynb`
- `main/Potato Leaf Disease Classification (COLAB).ipynb`
- `main/sample/potato.png`
- Office 临时文件 `~$智检项目概要介绍.docx`
- `__pycache__/`

## 第一阶段验证命令

旧 Flask：

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -c "import flask, PIL, numpy, tensorflow, openai, dotenv, requests; print('runtime imports ok')"
python app.py
```

预期结果：

- 控制台打印模型预热完成；如果 `final_model.h5` 缺失，应打印明确的模型加载错误。
- 未配置 API Key 时，控制台提示 AI 分析会使用兜底逻辑。
- Flask 服务监听 `http://127.0.0.1:5000`。
- 访问 `/` 能返回当前页面。

## 第二阶段结构基线验证命令

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/model/status
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

预期结果：

- 后端健康检查返回 `ok: true`。
- 模型状态接口能返回 `final_model.h5` 是否存在。
- 前端页面能显示结构基线信息，并显示后端连接状态。
- 根目录旧 Flask 应用仍能通过 `python app.py` 启动。

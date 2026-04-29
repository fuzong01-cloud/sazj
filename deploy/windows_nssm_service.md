# 使用 NSSM 注册 FastAPI 后端服务

NSSM 用于把 Uvicorn 后端注册为 Windows 服务，保证服务器重启后自动恢复运行。

## 安装 NSSM

1. 下载 NSSM Windows 版本。
2. 解压到例如：

```text
C:\tools\nssm\nssm.exe
```

3. 验证：

```powershell
C:\tools\nssm\nssm.exe version
```

## 服务参数

推荐服务名：

```text
sazj-backend
```

程序路径：

```text
C:\sazj\venv\Scripts\python.exe
```

启动参数：

```text
C:\sazj\start.py --host 0.0.0.0 --port 8000 --no-reload
```

工作目录：

```text
C:\sazj
```

## 图形界面注册

```powershell
C:\tools\nssm\nssm.exe install sazj-backend
```

在弹窗中填写：

- `Path`：`C:\sazj\venv\Scripts\python.exe`
- `Startup directory`：`C:\sazj`
- `Arguments`：`C:\sazj\start.py --host 0.0.0.0 --port 8000 --no-reload`

在 `I/O` 页配置日志：

- `Output`：`C:\sazj\logs\backend.out.log`
- `Error`：`C:\sazj\logs\backend.err.log`

应用自身还会在 `LOG_DIR` 中写入滚动日志，默认文件为：

```text
C:\sazj\logs\backend.log
```

在 `Exit actions` 页保持默认自动重启策略即可。

## 命令行注册

```powershell
C:\tools\nssm\nssm.exe install sazj-backend C:\sazj\venv\Scripts\python.exe "C:\sazj\start.py --host 0.0.0.0 --port 8000 --no-reload"
C:\tools\nssm\nssm.exe set sazj-backend AppDirectory C:\sazj
C:\tools\nssm\nssm.exe set sazj-backend AppStdout C:\sazj\logs\backend.out.log
C:\tools\nssm\nssm.exe set sazj-backend AppStderr C:\sazj\logs\backend.err.log
C:\tools\nssm\nssm.exe set sazj-backend Start SERVICE_AUTO_START
```

启动服务：

```powershell
Start-Service sazj-backend
```

查看状态：

```powershell
Get-Service sazj-backend
```

停止服务：

```powershell
Stop-Service sazj-backend
```

删除服务：

```powershell
C:\tools\nssm\nssm.exe remove sazj-backend confirm
```

## 验证

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

预期返回后端健康状态。

## 常见问题

服务启动后立刻停止：

- 检查 `C:\sazj\logs\backend.err.log`。
- 确认虚拟环境依赖已安装。
- 确认 `.env` 或 `backend\.env` 中 `DATABASE_URL` 正确。

服务能启动但外部不能访问：

- 检查 Uvicorn 是否使用 `--host 0.0.0.0`。
- 检查 Windows 防火墙和云服务器安全组。
- 如果使用 Caddy 反向代理，优先让公网访问 `80` 端口。

修改代码或环境变量后不生效：

```powershell
Restart-Service sazj-backend
```

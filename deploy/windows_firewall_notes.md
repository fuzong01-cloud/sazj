# Windows Server 防火墙与公网访问说明

Windows Server 部署需要同时检查云服务器安全组和系统防火墙。两边都放行后，公网才能访问。

## 推荐端口

```text
80    前端页面和反向代理后的 API
8000  FastAPI 后端，建议只在临时调试时开放
```

短期演示推荐公网只开放 `80`，由 Caddy/Nginx/IIS 反向代理到 `127.0.0.1:8000`。

## PowerShell 开放 80 端口

以管理员身份运行 PowerShell：

```powershell
New-NetFirewallRule -DisplayName "SAZJ HTTP 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

## 临时开放 8000 端口

仅用于调试：

```powershell
New-NetFirewallRule -DisplayName "SAZJ FastAPI 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

调试完成后建议删除：

```powershell
Remove-NetFirewallRule -DisplayName "SAZJ FastAPI 8000"
```

## 不开放数据库端口

当前默认使用 SQLite，数据库是本地文件，不需要开放数据库端口。后续如果切换 PostgreSQL，也不要创建公网 `5432` 入站规则；确需远程维护时，优先使用云厂商控制台、远程桌面或临时安全组白名单。

## 云服务器安全组

在云厂商控制台检查：

- 入站 TCP `80` 是否开放。
- 如果临时调试后端，入站 TCP `8000` 是否开放。
- 是否没有额外开放数据库端口。

## 验证命令

服务器本机：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

外部浏览器：

```text
http://服务器公网IP/
http://服务器公网IP/api/health
```

## 常见问题

本机能访问，公网不能访问：

- 云服务器安全组没有开放端口。
- Windows 防火墙没有入站规则。
- Caddy/Nginx/IIS 没有监听 `0.0.0.0:80`。

前端能打开，`/api/health` 失败：

- 反向代理规则没有正确转发 `/api/*`。
- 后端服务没有启动。
- 后端只监听了 `127.0.0.1` 但代理配置不匹配。

公网直接访问 `:8000` 失败：

- 这是可接受状态。推荐让公网访问 `80`，由反向代理转发到后端。

数据库连接失败：

- SQLite 默认不依赖网络端口，优先检查 `DATABASE_URL` 文件路径和目录权限。
- 如果已切换 PostgreSQL，再检查 PostgreSQL 服务状态、账号密码、数据库名和 `DATABASE_URL`。

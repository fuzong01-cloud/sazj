# Windows Server .env 示例

建议生产或演示环境主配置放在：

```text
C:\sazj\.env
```

短期演示部署也可以复制一份到：

```text
C:\sazj\backend\.env
```

## SQLite 默认配置

当前项目已切回 SQLite 作为本地和短期演示默认数据库，避免 Windows Server 上额外安装 PostgreSQL。

```text
APP_NAME=薯安智检 API
APP_ENV=production
API_PREFIX=/api

DATABASE_URL=sqlite:///C:/sazj/backend/sazj.sqlite3
AUTO_CREATE_TABLES=true
SQLITE_JOURNAL_MODE=OFF

MAX_UPLOAD_BYTES=8388608
UPLOAD_DIR=C:\sazj\uploads
LOG_DIR=C:\sazj\logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=5242880
LOG_BACKUP_COUNT=3

PROVIDER_SECRET_KEY=请替换为32字符以上随机密钥
ADMIN_WEBUI_TOKEN=请替换为32字符以上随机管理员令牌
JWT_SECRET_KEY=请替换为32字符以上随机密钥
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_ORIGINS=http://服务器公网IP
```

## Provider API Key 加密

`PROVIDER_SECRET_KEY` 用于加密模型提供商的 API Key / Token。要求：

- 至少 32 个字符。
- 生产或演示环境必须替换默认值。
- 部署后不要随意修改；修改后，数据库中已有 provider API Key 将无法解密，需要重新配置。

## Provider 管理后台令牌

`ADMIN_WEBUI_TOKEN` 用于访问后端模型配置 WebUI：

```text
http://服务器公网IP/admin/providers
```

该令牌只给项目维护者使用，不要发给普通用户。

VisionProvider 和 TextProvider 可以分别配置不同 API。图片识别使用 VisionProvider；防治建议和前端 AI 助手使用 TextProvider。

天气能力由后端调用 Open-Meteo Forecast API，不需要额外 API Key，但服务器需要允许访问外网 HTTPS。

## 登录令牌密钥

`JWT_SECRET_KEY` 用于签发登录访问令牌。要求：

- 生产或演示环境必须替换默认值。
- 建议使用 32 字符以上随机字符串。
- 修改后旧登录 token 会失效，用户需要重新登录。

## PostgreSQL 可选配置

如果后续需要多人长期使用或更强并发，再切换 PostgreSQL：

```text
DATABASE_URL=postgresql+psycopg://postgres:密码@127.0.0.1:5432/sazj
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

2 核 2GB Windows Server 上应保持较小连接池。不要把 PostgreSQL 暴露到公网。

## 敏感信息注意事项

- `.env` 不要提交到 Git。
- API Key 不要写进 README、前端代码或截图。
- Provider API Key 会加密后再存入数据库。

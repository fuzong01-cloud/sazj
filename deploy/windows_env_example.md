# Windows Server .env 示例

建议生产环境主配置放在：

```text
C:\sazj\.env
```

当前后端默认读取：

```text
C:\sazj\backend\.env
```

短期演示部署可以把根目录 `.env` 复制一份到 `backend\.env`。

建议 Windows Server 中的目录配置使用绝对路径。相对路径会按 `backend\` 目录解析。

## 当前可用配置

```text
APP_NAME=薯安智检 API
APP_ENV=production
API_PREFIX=/api

DATABASE_URL=postgresql+psycopg://postgres:请替换为真实密码@127.0.0.1:5432/sazj
AUTO_CREATE_TABLES=true
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

MAX_UPLOAD_BYTES=8388608
UPLOAD_DIR=C:\sazj\uploads
LOG_DIR=C:\sazj\logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=5242880
LOG_BACKUP_COUNT=3
PROVIDER_SECRET_KEY=请替换为32字符以上随机密钥
FRONTEND_ORIGINS=http://服务器公网IP
```

## 后续阶段预留配置

以下配置是后续用户认证阶段预留项。当前代码不一定全部读取，新增功能时应优先沿用这些名称。

```text
JWT_SECRET_KEY=请替换为32字节以上随机密钥
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Provider API Key 加密

`PROVIDER_SECRET_KEY` 用于加密模型提供商的 API Key / Token。要求：

- 至少 32 个字符。
- 生产环境必须替换默认值。
- 部署后不要随意修改；修改后，数据库中已有的 provider API Key 将无法解密，需要重新配置。

## PostgreSQL 连接说明

本机 PostgreSQL：

```text
DATABASE_URL=postgresql+psycopg://postgres:密码@127.0.0.1:5432/sazj
```

不要把 PostgreSQL 暴露到公网。2GB 内存服务器上，数据库只服务本机后端即可。

## 低内存连接池建议

2核2G Windows Server 建议保持较小连接池：

```text
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=1
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

这表示常驻连接最多 2 个，临时溢出连接最多 1 个，避免演示服务器内存被数据库连接耗尽。

## CORS 配置

如果前端通过公网 IP 访问：

```text
FRONTEND_ORIGINS=http://服务器公网IP
```

如果临时使用前端开发服务器：

```text
FRONTEND_ORIGINS=http://服务器公网IP,http://127.0.0.1:5173,http://localhost:5173
```

## 敏感信息注意事项

- `.env` 不要提交到 Git。
- API Key 不要写进 README、前端代码或截图。
- Provider API Key 会加密后再存入 PostgreSQL。
- 如果发现旧数据库中存在明文 provider API Key，请在当前版本启动后重新保存一次该模型配置。

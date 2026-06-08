# 部署文档

本文档介绍云计算服务安全评估智能预审Agent在不同环境下的部署方式。

## 目录

- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)
- [基础设施依赖](#基础设施依赖)
- [常见问题](#常见问题)

## 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Python | 3.10 | 3.11+ |
| Node.js | 18 | 20+ |
| PostgreSQL | 14 | 16+ |
| Redis | 6 | 7+ |
| MinIO | RELEASE.2023-10 | 最新稳定版 |
| Milvus | 2.3 | 2.4+ |

## 开发环境部署

### 1. 后端

```bash
# 克隆项目
git clone <repository-url>
cd yunpinggu

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 AI_MODEL_API_KEY

# 启动后端服务
python main.py
```

后端服务运行在 `http://localhost:8000`。

### 2. 前端

```bash
cd yunping/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，自动代理 `/api` 请求到后端。

### 3. 验证

- 前端页面：`http://localhost:5173`
- 后端 API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

## Docker 部署

### 后端 Dockerfile

在项目根目录创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（OpenCV 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端 Dockerfile

在 `yunping/frontend/` 目录创建 `Dockerfile`：

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx 配置

在 `yunping/frontend/` 目录创建 `nginx.conf`：

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # 前端路由 - SPA 回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 大模型推理耗时较长，设置较长超时
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
    }

    # 上传文件大小限制
    client_max_body_size 10m;
}
```

### docker-compose.yml

在项目根目录创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/audit_db
      - MINIO_ENDPOINT=minio:9000
      - MILVUS_HOST=milvus
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - uploads:/app/uploads
      - configs:/app/configs
      - logs:/app/logs
    depends_on:
      - db
      - redis
      - minio
    restart: unless-stopped

  frontend:
    build: ./yunping/frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: audit_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data
    restart: unless-stopped

  milvus:
    image: milvusdb/milvus:v2.4-latest
    command: milvus run standalone
    environment:
      ETCD_USE_EMBED: "true"
      ETCD_DATA_DIR: /var/lib/milvus/etcd
      COMMON_STORAGETYPE: local
    ports:
      - "19530:19530"
      - "9091:9091"
    volumes:
      - milvusdata:/var/lib/milvus
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
  miniodata:
  milvusdata:
  uploads:
  configs:
  logs:
```

### 启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看后端日志
docker-compose logs -f backend

# 停止所有服务
docker-compose down

# 停止并清除数据卷
docker-compose down -v
```

## 生产环境部署

### 1. 服务器配置建议

| 规模 | CPU | 内存 | 磁盘 | 说明 |
|------|-----|------|------|------|
| 小型 | 4 核 | 16 GB | 100 GB SSD | 单机部署，含所有组件 |
| 中型 | 8 核 | 32 GB | 500 GB SSD | 应用与数据库分离部署 |
| 大型 | 16 核+ | 64 GB+ | 1 TB+ SSD | 微服务化，各组件独立扩容 |

> PaddleOCR 和 Embedding 模型对内存需求较高，建议至少 16 GB。

### 2. 安全配置

**必须修改的配置项**：

```bash
# JWT 密钥 - 使用强随机字符串
JWT_SECRET_KEY=<生成一个64位随机字符串>

# 数据库密码
DATABASE_URL=postgresql+psycopg2://<user>:<strong_password>@<host>:5432/audit_db

# MinIO 密码
MINIO_ACCESS_KEY=<custom_access_key>
MINIO_SECRET_KEY=<custom_secret_key>

# 大模型 API Key
AI_MODEL_API_KEY=<your_api_key>
```

生成随机密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**HTTPS 配置**：

生产环境必须启用 HTTPS，推荐使用 Nginx 反向代理 + Let's Encrypt 证书：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其余配置同上方 nginx.conf
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

### 3. 数据库初始化

```bash
# 首次启动时，后端会自动创建所有表
# 如需手动初始化：
python -c "from app.database import init_db; init_db()"
```

### 4. MinIO 存储桶初始化

```bash
# 使用 mc 客户端
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/audit-materials
```

### 5. Systemd 服务配置（Linux）

创建 `/etc/systemd/system/audit-agent.service`：

```ini
[Unit]
Description=Cloud Security Audit Agent
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=app
WorkingDirectory=/opt/yunpinggu
Environment=PATH=/opt/yunpinggu/venv/bin
ExecStart=/opt/yunpinggu/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable audit-agent
sudo systemctl start audit-agent
```

### 6. 日志管理

日志默认输出到 `logs/app.log`，建议配置日志轮转：

```bash
# /etc/logrotate.d/audit-agent
/opt/yunpinggu/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
}
```

## 环境变量配置

### 后端环境变量

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `DATABASE_URL` | `sqlite:///./document_db.sqlite` | 否 | 数据库连接串，生产环境使用 PostgreSQL |
| `JWT_SECRET_KEY` | `change-this-secret-in-production` | **是** | JWT 签名密钥，生产环境必须修改 |
| `JWT_EXPIRATION_HOURS` | `24` | 否 | Token 过期时间（小时） |
| `AI_MODEL_API_KEY` | - | **是** | 大模型 API Key |
| `AI_MODEL_BASE_URL` | `https://api.openai.com/v1` | 否 | 大模型 API 地址 |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | 否 | Embedding 模型名称 |
| `VECTOR_DIMENSION` | `1024` | 否 | 向量维度 |
| `SIMILARITY_THRESHOLD` | `0.8` | 否 | 相似度检索阈值 |
| `RERANK_MODEL` | `BAAI/bge-reranker-base` | 否 | Rerank 模型名称 |
| `RERANK_ENABLED` | `True` | 否 | 是否启用 Rerank |
| `MINIO_ENDPOINT` | `localhost:9000` | 否 | MinIO 对象存储地址 |
| `MINIO_ACCESS_KEY` | `minioadmin` | 否 | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | `minioadmin` | 否 | MinIO 密钥 |
| `MILVUS_HOST` | `localhost` | 否 | Milvus 向量库地址 |
| `MILVUS_PORT` | `19530` | 否 | Milvus 端口 |
| `REDIS_URL` | `redis://localhost:6379/0` | 否 | Redis 缓存地址 |
| `UPLOAD_DIR` | `uploads` | 否 | 文件上传目录 |
| `LOG_DIR` | `logs` | 否 | 日志目录 |

### 前端环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VITE_API_BASE_URL` | `/api` | API 基础路径 |
| `VITE_UPLOAD_MAX_SIZE` | `10485760` | 上传文件大小限制（字节） |
| `VITE_ENABLE_DEBUG` | `true` | 调试模式（生产环境设为 `false`） |

## 基础设施依赖

### 组件矩阵

| 组件 | 开发环境 | 生产环境 | 用途 |
|------|---------|---------|------|
| 数据库 | SQLite（内置） | PostgreSQL | 业务数据存储 |
| 对象存储 | 本地文件系统 | MinIO | 文件上传存储 |
| 向量库 | NumPy（内存） | Milvus | 向量相似度检索 |
| 缓存 | 内存 | Redis | 数据缓存 + OCR 结果缓存 |
| OCR | PaddleOCR（本地） | PaddleOCR（本地） | 图像文字识别 |

### PostgreSQL 配置建议

```sql
-- 创建数据库和用户
CREATE DATABASE audit_db;
CREATE USER audit_user WITH ENCRYPTED PASSWORD '<strong_password>';
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_user;
```

连接串格式：

```
postgresql+psycopg2://audit_user:<password>@<host>:5432/audit_db
```

### Milvus 配置建议

生产环境推荐使用 Milvus 集群模式（依赖 etcd + MinIO + Pulsar），开发环境可使用 Standalone 模式。

向量集合配置：

- 集合名：`benchmark_embeddings`
- 向量维度：1024 或 1536（与 Embedding 模型匹配）
- 索引类型：IVF_FLAT 或 HNSW
- 度量类型：COSINE

## 常见问题

### Q: PaddleOCR 启动慢

PaddleOCR 首次加载模型需要下载权重文件，后续会缓存到本地。如需加速，可提前下载模型文件到 `~/.paddleocr/` 目录。

### Q: 大模型 API 超时

后端默认请求超时为 60 秒，大模型推理可能耗时较长。可在 Nginx 层增加 `proxy_read_timeout`，或在 `app/services/llm_service.py` 中调整 `timeout` 参数。

### Q: 向量检索无结果

检查 Milvus 服务是否正常运行，向量维度是否与 Embedding 模型输出维度一致。开发环境使用 NumPy 内存存储，服务重启后数据会丢失。

### Q: 文件上传失败

- 检查 `uploads/` 目录是否有写入权限
- 检查文件大小是否超过 10MB 限制
- 检查文件扩展名是否在允许列表中（.docx/.xlsx/.xls/.png/.jpg/.jpeg/.pdf）

### Q: 数据库迁移

项目使用 SQLAlchemy `create_all()` 自动建表，不支持自动迁移。如需修改表结构：

1. 开发环境：删除 SQLite 文件，重启服务自动重建
2. 生产环境：使用 Alembic 管理数据库迁移，或手动执行 DDL

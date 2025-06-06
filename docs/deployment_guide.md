# 部署指南

## 环境要求

### 基础环境
- Python 3.13+
- Redis 6.0+
- PostgreSQL 13+ (可选，默认使用PostgreSQL，测试使用Sqlite)
- Linux/macOS/Windows

### 系统资源建议
- **开发环境**：2GB RAM, 1 CPU核心
- **测试环境**：4GB RAM, 2 CPU核心  
- **生产环境**：8GB+ RAM, 4+ CPU核心

## 快速部署

### 1. 克隆项目

```bash
git clone https://gitee.com/lijianqiao/fastapibase.git
cd fastapi-base
```

### 2. 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements/prod.txt
```

### 3. 环境变量配置

```bash
# 创建 .env 文件
cp .env.example .env
```

```bash
# .env 配置示例
# 应用配置
APP_NAME=FastAPI Base
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/fastapi_base
# 或使用 SQLite
# DATABASE_URL=sqlite:///./fastapi_base.db

# Redis缓存配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# 安全配置
SECRET_KEY=your-application-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60
```

### 4. 数据库初始化

```bash
# 运行数据库迁移
alembic upgrade head

# 创建初始数据（可选）
python scripts/init_data.py
```

### 5. 启动应用

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Redis 配置

### 安装 Redis

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### CentOS/RHEL
```bash
sudo yum install epel-release
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### Docker
```bash
docker run --name redis -p 6379:6379 -d redis:7-alpine
```

### Redis 配置优化

#### 生产环境配置 (`/etc/redis/redis.conf`)

```bash
# 网络配置
bind 127.0.0.1 ::1
port 6379
timeout 300
tcp-keepalive 300

# 内存配置
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# 持久化配置
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# AOF配置
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 安全配置
requirepass your-redis-password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""

# 日志配置
loglevel notice
logfile /var/log/redis/redis-server.log

# 客户端配置
maxclients 10000
```

#### Redis 监控

```bash
# 检查 Redis 状态
redis-cli ping

# 查看 Redis 信息
redis-cli info

# 监控 Redis 命令
redis-cli monitor

# 查看内存使用
redis-cli info memory
```

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements/prod.txt requirements.txt

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非特权用户
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_base
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fastapi_base
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass redis-password
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 部署命令

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

## Nginx 配置

### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # 缓存配置
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m 
                     max_size=100m inactive=60m use_temp_path=off;

    server {
        listen 80;
        server_name yourdomain.com;
        
        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 安全头
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000";

        # API 代理
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 缓存静态响应
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        }

        # 健康检查
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 生产环境优化

### 性能调优

#### 应用配置

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4  # CPU核心数 * 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
preload_app = True
```

#### 数据库连接池

```python
# app/config.py
class Settings(BaseSettings):
    # 数据库连接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
```

#### Redis 连接池

```python
# app/config.py
class Settings(BaseSettings):
    # Redis连接池配置
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS: dict = {
        "TCP_KEEPINTVL": 1,
        "TCP_KEEPCNT": 3,
        "TCP_KEEPIDLE": 1,
    }
```

### 监控配置

#### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### Grafana 仪表板

主要监控指标：
- HTTP请求数量和响应时间
- 数据库连接池使用率
- Redis缓存命中率
- 系统资源使用情况

### 日志管理

#### 日志配置

```python
# app/core/logging.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/app.log",
            "maxBytes": 100 * 1024 * 1024,  # 100MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
```

#### ELK Stack 集成

```yaml
# docker-compose.yml 添加
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

## 备份策略

### 数据库备份

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fastapi_base_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump postgresql://user:password@localhost:5432/fastapi_base > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

### Redis 备份

```bash
#!/bin/bash
# backup_redis.sh

BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 复制 RDB 文件
cp /var/lib/redis/dump.rdb $BACKUP_DIR/dump_$DATE.rdb

# 复制 AOF 文件
cp /var/lib/redis/appendonly.aof $BACKUP_DIR/appendonly_$DATE.aof

# 压缩备份文件
tar -czf $BACKUP_DIR/redis_backup_$DATE.tar.gz -C $BACKUP_DIR dump_$DATE.rdb appendonly_$DATE.aof

# 清理临时文件
rm $BACKUP_DIR/dump_$DATE.rdb $BACKUP_DIR/appendonly_$DATE.aof

# 删除7天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Redis backup completed: $BACKUP_DIR/redis_backup_$DATE.tar.gz"
```

## 安全加固

### 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置防火墙
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 应用安全

```python
# app/config.py
class Settings(BaseSettings):
    # 安全配置
    ALLOWED_HOSTS: List[str] = ["yourdomain.com", "api.yourdomain.com"]
    CORS_ORIGINS: List[str] = ["https://yourdomain.com"]
    SECURE_COOKIES: bool = True
    HTTPS_ONLY: bool = True
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60
```

## 故障排查

### 常见问题

#### 1. Redis 连接失败
```bash
# 检查 Redis 状态
systemctl status redis
redis-cli ping

# 检查网络连接
telnet localhost 6379

# 查看错误日志
tail -f /var/log/redis/redis-server.log
```

#### 2. 数据库连接池耗尽
```python
# 监控连接池状态
async def check_db_pool():
    pool = get_db_engine().pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "invalid": pool.invalid(),
    }
```

#### 3. 缓存命中率低
```bash
# 检查 Redis 命中率
redis-cli info stats | grep hit

# 监控缓存键
redis-cli --scan --pattern "fastapi_base:*" | head -20
```

### 性能监控脚本

```bash
#!/bin/bash
# monitor.sh

echo "=== 系统资源 ==="
free -h
df -h
top -bn1 | head -20

echo "=== Redis 状态 ==="
redis-cli info memory | grep used_memory_human
redis-cli info stats | grep keyspace

echo "=== 数据库连接 ==="
sudo netstat -an | grep :5432 | wc -l

echo "=== 应用日志 ==="
tail -n 10 /app/logs/app.log
```

## 自动化部署

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /app/fastapi-base
          git pull origin main
          docker-compose down
          docker-compose up -d --build
          docker-compose logs -f app
```

这样就完成了完整的部署指南，包含了Redis配置、Docker部署、性能优化、监控和安全等各个方面的说明。

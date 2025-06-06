# FastAPI Base 快速入门教程

本教程将引导您快速搭建和使用 FastAPI Base 系统。

## 🎯 教程目标

完成本教程后，您将能够：
- 搭建完整的 FastAPI Base 开发环境
- 理解系统的核心概念和架构
- 使用 API 进行用户管理和权限控制
- 掌握缓存和性能优化功能

## 📋 准备工作

### 系统要求
- Windows 10/11 或 Linux/macOS
- Python 3.13 或更高版本
- Redis 服务（用于缓存）
- Git（用于克隆代码）

### 检查环境

```cmd
# 检查Python版本
python --version

# 检查pip版本
pip --version

# 检查Git版本
git --version
```

## 🚀 第一步：环境搭建

### 1. 克隆项目

```cmd
# 克隆项目到本地
git clone https://gitee.com/lijianqiao/fastapibase.git
cd fastapi-base
```

### 2. 创建虚拟环境

```cmd
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate
```

### 3. 安装依赖

```cmd
# 安装项目依赖
pip install -r requirements/dev.txt
```

### 4. 启动Redis服务

**选项A: 使用Docker（推荐）**
```cmd
# 拉取并运行Redis容器
docker run --name fastapi-redis -p 6379:6379 -d redis:7-alpine

# 验证Redis运行状态
docker ps
```

**选项B: 本地安装Redis**
- Windows: 下载 Redis for Windows
- Linux: `sudo apt install redis-server`
- macOS: `brew install redis`

### 5. 配置环境变量

```cmd
# 复制环境配置模板
copy .env.example .env
```

编辑 `.env` 文件：
```bash
# 基本配置
APP_NAME=FastAPI Base
DEBUG=true
ENVIRONMENT=development

# 数据库配置（使用SQLite）
DATABASE_URL=sqlite:///./fastapi_base.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-secret-key-for-development-only
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# 应用密钥
SECRET_KEY=your-app-secret-key-here
```

## 🗄️ 第二步：数据库初始化

### 1. 执行数据库迁移

```cmd
# 执行迁移创建表结构
alembic upgrade head
```

### 2. 初始化基础数据

```cmd
# 运行初始化脚本
python init_data.py
```

初始化完成后，系统会创建：
- 默认权限（用户管理、角色管理等）
- 默认角色（超级管理员、管理员、普通用户）
- 默认管理员账户（admin/admin@123）

## 🎬 第三步：启动应用

### 1. 启动开发服务器

```cmd
# 方式1: 使用项目主文件
python main.py

# 方式2: 使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 验证服务启动

打开浏览器访问：
- **应用主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

看到以下响应说明服务启动成功：
```json
{
  "status": "healthy",
  "timestamp": "2025-06-06T10:30:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

## 🔑 第四步：API使用体验

### 1. 用户登录

使用Swagger UI（http://localhost:8000/docs）或命令行测试：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin",
    "password": "admin@123"
  }'
```

成功响应：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 2. 获取当前用户信息

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 创建新用户

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "Test@123",
    "full_name": "测试用户"
  }'
```

### 4. 查询用户列表

```bash
curl -X GET "http://localhost:8000/api/v1/users?page=1&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛡️ 第五步：权限管理体验

### 1. 查看当前用户权限

```bash
curl -X GET "http://localhost:8000/api/v1/permissions/user-permissions/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. 创建新角色

```bash
curl -X POST "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试角色",
    "code": "test_role",
    "description": "用于测试的角色"
  }'
```

### 3. 给角色分配权限

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/batch-assign-permissions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": 4,
    "permission_ids": [1, 2, 3]
  }'
```

## 🚄 第六步：缓存功能体验

### 1. 查看缓存效果

第一次API调用（缓存未命中）：
```bash
time curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

第二次API调用（缓存命中，响应更快）：
```bash
time curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. 检查Redis缓存

如果您安装了redis-cli：
```bash
# 连接Redis
redis-cli

# 查看缓存键
KEYS fastapi_base:*

# 查看用户权限缓存
GET fastapi_base:user_permissions:1

# 查看Token黑名单
KEYS fastapi_base:token_blacklist:*
```

## 🔐 第七步：安全功能体验

### 1. 测试Token黑名单

```bash
# 登出用户（将Token加入黑名单）
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 尝试使用已登出的Token访问API（应该失败）
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

预期响应：
```json
{
  "code": 401,
  "message": "令牌已失效"
}
```

### 2. 测试权限控制

尝试用普通用户访问管理员接口：
```bash
# 以普通用户身份登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "testuser",
    "password": "Test@123"
  }'

# 尝试创建用户（需要管理员权限）
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer NORMAL_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

预期响应：
```json
{
  "code": 403,
  "message": "权限不足"
}
```

## 📊 第八步：监控和日志

### 1. 查看健康状态

```bash
curl -X GET "http://localhost:8000/health"
```

### 2. 查看监控指标

```bash
curl -X GET "http://localhost:8000/metrics"
```

### 3. 查看审计日志

```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs?page=1&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛠️ 开发技巧

### 1. 使用开发工具

```cmd
# 代码格式化
ruff format app/

# 代码检查
ruff check app/

# 运行测试
pytest

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

### 2. 数据库管理

```cmd
# 创建新的迁移文件
alembic revision --autogenerate -m "Add new feature"

# 查看迁移历史
alembic history

# 回滚迁移
alembic downgrade -1
```

### 3. 重置开发环境

```cmd
# 删除数据库文件
del fastapi_base.db

# 重新执行迁移
alembic upgrade head

# 重新初始化数据
python init_data.py
```

## 🎯 进阶学习

### 1. 阅读文档
- [项目文档](docs/项目文档.md) - 了解系统架构
- [API文档](docs/api.md) - 详细的API说明
- [缓存指南](docs/cache_guide.md) - 缓存使用最佳实践
- [部署指南](docs/deployment_guide.md) - 生产环境部署

### 2. 研究代码结构
```
app/
├── models/          # 数据模型定义
├── repositories/    # 数据访问层
├── services/        # 业务逻辑层
├── api/            # API路由层
└── core/           # 核心功能（安全、配置等）
```

### 3. 自定义开发

#### 添加新的API端点
```python
# app/api/v1/endpoints/custom.py
from fastapi import APIRouter, Depends
from app.services.custom_service import CustomService

router = APIRouter()

@router.get("/custom-data")
async def get_custom_data(
    service: CustomService = Depends()
):
    return await service.get_data()
```

#### 添加新的权限
```python
# 在init_data.py中添加
custom_permissions = [
    ("custom", "read", "查看自定义数据"),
    ("custom", "write", "修改自定义数据"),
]
```

## ❓ 常见问题

### Q: 无法连接Redis怎么办？
1. 检查Redis服务是否启动：`docker ps` 或服务管理器
2. 检查端口是否被占用：`netstat -an | findstr 6379`
3. 验证Redis配置：确认REDIS_URL在.env中正确设置

### Q: 数据库迁移失败？
1. 检查数据库文件权限
2. 确认SQLAlchemy版本兼容性
3. 删除数据库文件重新迁移

### Q: API返回401错误？
1. 检查Token是否过期
2. 确认Authorization头格式：`Bearer YOUR_TOKEN`
3. 验证JWT_SECRET_KEY配置

### Q: 权限验证不工作？
1. 确认用户拥有正确的角色
2. 检查角色是否分配了相应权限
3. 验证权限装饰器使用是否正确

## 🎉 恭喜！

您已经完成了 FastAPI Base 的快速入门教程！现在您可以：

✅ 搭建完整的开发环境  
✅ 使用API进行用户和权限管理  
✅ 理解缓存和性能优化  
✅ 掌握安全认证机制  
✅ 进行基本的开发和调试  

## 📝 下一步

1. **深入学习**: 阅读详细文档，了解系统架构
2. **实践开发**: 基于模板开发自己的业务功能
3. **部署上线**: 学习生产环境部署和运维
4. **贡献代码**: 参与开源项目，提交PR

祝您使用愉快！🚀

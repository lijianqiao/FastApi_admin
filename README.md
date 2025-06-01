# Litestar Admin System

基于 Litestar 框架构建的后台管理系统模板，提供用户管理、权限管理、角色管理、审计日志等功能。

## 技术栈

- Python 3.13+
- Fastapi 0.115.12
- SQLAlchemy 2.0+ (异步 ORM)
- SQLite (数据库)
- Alembic (数据库迁移)
- pydantic v2 (校验数据)
- JWT (身份认证)

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
uv venv .venv --python 3.13

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv sync
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，修改相关配置
```

### 3. 数据库初始化

```bash
# 初始化 Alembic
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 运行应用

```bash
# 开发模式运行
python -m app.main

# 或使用 uvicorn 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问应用

- 应用地址: http://localhost:8000
- 健康检查: http://localhost:8000/health
- API 文档: http://localhost:8000/schema (Swagger UI)
- OpenAPI 规范: http://localhost:8000/schema/openapi.json

## 开发规范

请参考项目根目录下的 `litestar开发规则.md` 文件，其中详细说明了：

- 代码规范和类型注解要求
- DTO 设计和使用原则
- 数据库和 ORM 最佳实践
- 认证授权实现方式
- 错误处理和日志记录
- 性能优化建议

## 主要特性

- ✅ 项目骨架和配置管理
- 🔄 用户管理 (开发中)
- 🔄 角色权限管理 (开发中)
- 🔄 审计日志 (开发中)
- 🔄 JWT 认证授权 (开发中)
- 🔄 OpenAPI 文档生成 (开发中)

## 许可证

MIT License
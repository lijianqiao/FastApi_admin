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

# 初始化基础数据（权限、角色、管理员）
python init_data.py --help # 查看使用方法

# ============================================================
# 📚 数据库初始化工具
# ============================================================
# 用法:
#   python init_data.py              # 初始化数据库（保留现有数据）
#   python init_data.py --reset      # 重置数据库（清空并重新初始化）
#   python init_data.py --help       # 显示帮助信息

# 说明:
#   • 初始化模式：只创建不存在的数据，保留现有数据
#   • 重置模式：清空所有数据后重新初始化
# ============================================================
```

### 4. 运行应用

```bash
# 开发模式运行
python main.py

# 或使用 uvicorn 直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问应用

- 应用地址: http://localhost:8000
- 健康检查: http://localhost:8000/health
- API 文档: http://localhost:8000/docs (Swagger UI)
- OpenAPI 规范: http://localhost:8000/openapi.json

### 6. 默认账户

初始化完成后，系统会创建默认超级管理员账户：

- **用户名**: admin
- **密码**: admin@123
- **角色**: 超级管理员（拥有所有权限）

⚠️ **安全提醒**: 请登录后立即修改默认密码！

## 数据库初始化说明

系统提供了完整的数据库初始化功能，包括：

### 默认权限

- **用户管理**: create, read, update, delete, list
- **角色管理**: create, read, update, delete, list, assign
- **权限管理**: create, read, update, delete, list, assign
- **系统管理**: config, monitor, audit

### 默认角色

- **超级管理员** (super_admin): 拥有所有权限
- **管理员** (admin): 拥有大部分管理权限
- **普通用户** (user): 只有基本查看权限

### 初始化方式

```bash
# 方式1: 通过主程序参数
python main.py init-db

# 方式2: 直接运行初始化脚本
python init_data.py

# 方式3: 在代码中调用
from app.db.init_db import init_database
await init_database()
```

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
- 🔄 用户管理
- 🔄 角色权限管理
- 🔄 审计日志
- 🔄 JWT 认证授权
- 🔄 OpenAPI 文档生成

## 许可证

MIT License
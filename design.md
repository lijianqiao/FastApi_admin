# 现代后台管理系统架构设计

## 技术栈选择

### 核心框架
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy 2.0** - ORM（异步支持）
- **PostgreSQL** - 生产级数据库
- **Redis** - 缓存和会话存储

### 认证授权
- **JWT + Refresh Token** - 无状态认证
- **RBAC** - 基于角色的访问控制

### 现代化特性
- **异步编程** - 全栈async/await
- **API文档** - Swagger/OpenAPI自动生成
- **数据验证** - Pydantic V2
- **日志系统** - 结构化日志（JSON格式）
- **监控告警** - Prometheus + Grafana

## 项目结构

```text
admin_system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── dependencies.py        # 依赖注入
│   │
│   ├── core/                  # 核心功能
│   │   ├── __init__.py
│   │   ├── security.py        # JWT、密码加密
│   │   ├── permissions.py     # 权限验证
│   │   ├── database.py        # 数据库连接
│   │   ├── redis.py          # Redis连接
│   │   └── exceptions.py      # 自定义异常
│   │
│   ├── models/                # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── base.py           # 基础模型
│   │   └── ...
│   │
│   ├── schemas/               # Pydantic模型
│   │   ├── __init__.py
│   │   ├── base.py           # 基础schema
│   │   ├── ...
│   │   └── common.py           # 公共校验模型
│   │
│   ├── api/                   # API路由
│   │   ├── __init__.py
│   │   ├── v1/               # API版本1
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   └── dependencies.py   # API依赖
│   │
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── base.py           # 基础服务
│   │   └── ...
│   │
│   ├── crud/                  # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py           # 基础CRUD
│   │   └── ...
│   │
│   ├── middleware/            # 中间件
│   │   ├── __init__.py
│   │   ├── cors.py             # cors 设置
│   │   ├── rate_limit.py       # 限流
│   │   ├── audit_middleware.py # 审计日志中间件
│   │   └── error_handler.py    # 异常处理器
│   │
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       ├── logger.py           # 日志
│       ├── validators.py       # 校验
│       ├── helpers.py
│       └── constants.py
│
├── tests/                     # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_roles.py
│   └── test_permissions.py
│
├── migrations/                # 数据库迁移
│   └── alembic/
│
├── scripts/                   # 脚本文件
│   ├── init_db.py            # 初始化数据库
│   ├── create_superuser.py   # 创建超级用户
│   └── backup_db.py          # 数据库备份
│
├── requirements/              # 依赖文件
│   ├── base.txt              # 基础依赖
│   ├── dev.txt               # 开发依赖
│   └── prod.txt              # 生产依赖
│
├── .env.example              # 环境变量示例
├── pyproject.toml            # 项目配置
├── README.md
├── uv.lock
├── .gitignore
└── Makefile                  # 常用命令
```

## 数据库模型设计

### 1. 用户模型 (User)
```python
字段列表：
- id: 主键
- username: 用户名（唯一）
- email: 邮箱（唯一）
- password_hash: 密码哈希
- full_name: 全名
- avatar_url: 头像URL
- phone: 手机号
- department: 部门
- position: 职位
- is_active: 是否激活
- is_superuser: 是否超级用户
- email_verified: 邮箱是否验证
- phone_verified: 手机是否验证
- last_login_at: 最后登录时间
- last_login_ip: 最后登录IP
- login_count: 登录次数
- password_changed_at: 密码修改时间
- created_at: 创建时间
- updated_at: 更新时间
- created_by: 创建者
- updated_by: 更新者

关联关系：
- user_roles: 多对多关系（用户-角色）
- audit_logs: 一对多关系（用户-审计日志）
```

### 2. 角色模型 (Role)
```python
字段列表：
- id: 主键
- name: 角色名称（唯一）
- code: 角色代码（唯一）
- description: 描述
- level: 角色等级
- is_active: 是否激活
- is_system: 是否系统角色
- sort_order: 排序
- created_at: 创建时间
- updated_at: 更新时间
- created_by: 创建者
- updated_by: 更新者

关联关系：
- role_permissions: 多对多关系（角色-权限）
- user_roles: 多对多关系（用户-角色）
```

### 3. 权限模型 (Permission)
```python
字段列表：
- id: 主键
- name: 权限名称
- code: 权限代码（唯一）
- description: 描述
- resource: 资源
- action: 操作
- method: HTTP方法
- path: API路径
- category: 权限分类
- is_system: 是否系统权限
- sort_order: 排序
- created_at: 创建时间
- updated_at: 更新时间

关联关系：
- role_permissions: 多对多关系（角色-权限）
```

### 4. 用户角色关联模型 (UserRole)
```python
字段列表：
- user_id: 用户ID（外键）
- role_id: 角色ID（外键）
- assigned_at: 分配时间
- assigned_by: 分配者
- expires_at: 过期时间（可选）
- is_active: 是否激活
```

### 5. 角色权限关联模型 (RolePermission)
```python
字段列表：
- role_id: 角色ID（外键）
- permission_id: 权限ID（外键）
- granted_at: 授权时间
- granted_by: 授权者
```

### 6. 审计日志模型 (AuditLog)
```python
字段列表：
- id: 主键
- user_id: 用户ID（外键）
- username: 用户名（冗余存储）
- action: 操作类型
- resource: 资源类型
- resource_id: 资源ID
- resource_name: 资源名称
- method: HTTP方法
- path: 请求路径
- old_values: 旧值（JSON）
- new_values: 新值（JSON）
- ip_address: IP地址
- user_agent: 用户代理
- request_id: 请求ID
- session_id: 会话ID
- status: 操作状态
- error_message: 错误信息
- duration: 操作耗时
- created_at: 创建时间
```

### 7. 系统配置模型 (SystemConfig)
```python
字段列表：
- id: 主键
- key: 配置键（唯一）
- value: 配置值（JSON）
- description: 描述
- category: 配置分类
- data_type: 数据类型
- is_public: 是否公开
- is_encrypted: 是否加密
- validation_rule: 验证规则
- default_value: 默认值
- version: 版本号
- created_at: 创建时间
- updated_at: 更新时间
- created_by: 创建者
- updated_by: 更新者
```

## API设计规范

### 认证相关 API
```
POST   /api/v1/auth/login              # 用户登录
POST   /api/v1/auth/logout             # 用户登出
POST   /api/v1/auth/refresh            # 刷新Token
GET    /api/v1/auth/me                 # 获取当前用户信息
PUT    /api/v1/auth/me                 # 更新当前用户信息
POST   /api/v1/auth/change-password    # 修改密码
POST   /api/v1/auth/forgot-password    # 忘记密码
POST   /api/v1/auth/reset-password     # 重置密码
POST   /api/v1/auth/verify-email       # 验证邮箱
POST   /api/v1/auth/verify-phone       # 验证手机
```

### 用户管理 API
```
GET    /api/v1/users                   # 获取用户列表（支持分页、筛选、排序）
POST   /api/v1/users                   # 创建用户
GET    /api/v1/users/{id}              # 获取用户详情
PUT    /api/v1/users/{id}              # 更新用户
DELETE /api/v1/users/{id}              # 删除用户
PATCH  /api/v1/users/{id}/status       # 更新用户状态
PATCH  /api/v1/users/{id}/password     # 重置用户密码
GET    /api/v1/users/{id}/roles        # 获取用户角色
PUT    /api/v1/users/{id}/roles        # 设置用户角色
GET    /api/v1/users/{id}/permissions  # 获取用户权限
GET    /api/v1/users/{id}/audit-logs   # 获取用户操作日志
POST   /api/v1/users/batch-create      # 批量创建用户
PUT    /api/v1/users/batch-update      # 批量更新用户
DELETE /api/v1/users/batch-delete      # 批量删除用户
GET    /api/v1/users/export            # 导出用户数据
POST   /api/v1/users/import            # 导入用户数据
```

### 角色管理 API
```
GET    /api/v1/roles                   # 获取角色列表
POST   /api/v1/roles                   # 创建角色
GET    /api/v1/roles/{id}              # 获取角色详情
PUT    /api/v1/roles/{id}              # 更新角色
DELETE /api/v1/roles/{id}              # 删除角色
PATCH  /api/v1/roles/{id}/status       # 更新角色状态
GET    /api/v1/roles/{id}/permissions  # 获取角色权限
PUT    /api/v1/roles/{id}/permissions  # 设置角色权限
GET    /api/v1/roles/{id}/users        # 获取角色用户
POST   /api/v1/roles/{id}/users        # 添加角色用户
DELETE /api/v1/roles/{id}/users/{user_id} # 移除角色用户
GET    /api/v1/roles/tree              # 获取角色树结构
```

### 权限管理 API
```
GET    /api/v1/permissions             # 获取权限列表
POST   /api/v1/permissions             # 创建权限
GET    /api/v1/permissions/{id}        # 获取权限详情
PUT    /api/v1/permissions/{id}        # 更新权限
DELETE /api/v1/permissions/{id}        # 删除权限
GET    /api/v1/permissions/tree        # 获取权限树结构
GET    /api/v1/permissions/categories  # 获取权限分类
POST   /api/v1/permissions/sync        # 同步系统权限
```

### 审计日志 API
```
GET    /api/v1/audit-logs              # 获取审计日志列表
GET    /api/v1/audit-logs/{id}         # 获取审计日志详情
GET    /api/v1/audit-logs/stats        # 获取审计统计
GET    /api/v1/audit-logs/export       # 导出审计日志
DELETE /api/v1/audit-logs/cleanup      # 清理过期日志
```

### 系统配置 API
```
GET    /api/v1/system/configs          # 获取配置列表
POST   /api/v1/system/configs          # 创建配置
GET    /api/v1/system/configs/{key}    # 获取配置详情
PUT    /api/v1/system/configs/{key}    # 更新配置
DELETE /api/v1/system/configs/{key}    # 删除配置
GET    /api/v1/system/configs/public   # 获取公开配置
POST   /api/v1/system/configs/batch    # 批量设置配置
GET    /api/v1/system/info             # 获取系统信息
GET    /api/v1/system/health           # 健康检查
GET    /api/v1/system/metrics          # 系统指标
```

### 统一响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid-string"
}
```

### 错误响应格式
```json
{
  "code": 400,
  "message": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "Email format is invalid"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid-string"
}
```

## 安全特性

### 认证机制
- JWT访问令牌（15分钟过期）
- Refresh Token（7天过期）
- 密码加密（bcrypt + salt）
- 登录失败锁定机制
- 多设备登录管理

### 权限控制
- 基于角色的访问控制（RBAC）
- 资源级权限控制
- API接口权限验证
- 数据级权限控制
- 动态权限验证

### 安全防护
- CORS跨域配置
- API限流（Redis实现）
- SQL注入防护
- XSS防护
- CSRF防护
- 请求签名验证
- IP白名单/黑名单

## 性能优化

### 数据库优化
- 连接池配置
- 查询优化（索引设计）
- 分页查询优化
- 批量操作优化
- 数据库监控

### 缓存策略
- Redis缓存热点数据
- 用户会话缓存
- 权限信息缓存
- API响应缓存
- 查询结果缓存

### 异步处理
- 全异步数据库操作
- 异步日志记录
- 后台任务队列

## 监控和日志

### 日志系统
- 结构化日志（JSON格式）
- 分级日志记录（DEBUG/INFO/WARNING/ERROR）
- 日志轮转和归档
- 敏感信息脱敏

### 监控指标
- API响应时间和成功率
- 数据库连接数和查询性能
- Redis连接和命中率
- 内存和CPU使用情况
- 用户活跃度统计

### 健康检查
- 数据库连接检查
- Redis连接检查
- 依赖服务状态检查
- 系统资源监控

## 开发规范

### 代码规范

#### 格式化工具
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [".git", "__pycache__", ".venv", "alembic/versions"]

[tool.ruff.lint]
select = [
    "E",  # pycodestyle 错误
    "W",  # PycodeStyle 警告
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8 推导式
    "UP", # pyupgrade
]
ignore = [
    "E501", # 行太长，由 black 处理
    "B008", # 不在参数默认值中执行函数调用
    "W191", # 缩进包含制表符
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.ruff.lint.isort]
known-first-party = ["app"]
```

#### 类型注解
```python
# 强制使用类型注解
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

async def get_user(user_id: int) -> Optional[User]:
    """获取用户信息"""
    pass

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
```

#### 命名规范
```python
# 变量和函数：snake_case
user_name = "john"
def get_user_by_id(): pass

# 类：PascalCase
class UserService: pass

# 常量：UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5

# 私有属性/方法：前缀下划线
def _internal_method(): pass
```

#### 注释和文档
```python
class UserService:
    """用户服务类
    
    提供用户相关的业务逻辑处理
    """
    
    async def create_user(self, user_data: UserCreate) -> User:
        """创建新用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            创建的用户对象
            
        Raises:
            ValueError: 当用户数据无效时
            DuplicateError: 当用户已存在时
        """
        pass
```

### 测试策略

#### 测试结构
```python
# tests/test_users.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user():
    """测试创建用户"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/users", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
    assert response.status_code == 201
    assert response.json()["data"]["username"] == "testuser"
```

#### 测试覆盖率
```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term-missing

# 要求最低覆盖率80%
pytest --cov=app --cov-fail-under=80
```

### Git工作流

#### 分支策略
```
main        # 主分支，生产环境
develop     # 开发分支
feature/*   # 功能分支
hotfix/*    # 热修复分支
release/*   # 发布分支
```

#### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动

# 示例
feat(user): add user registration functionality
fix(auth): resolve JWT token expiration issue
docs(api): update API documentation
```

### 项目管理

#### 开发环境设置
```bash
# Makefile
.PHONY: install dev test lint format clean

install:
	pip install -r requirements/dev.txt
	pre-commit install

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app

lint:
	ruff check app
	mypy app

format:
	ruff format app

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
```

#### 代码审查清单
- [ ] 代码符合项目规范
- [ ] 已添加必要的测试
- [ ] 测试覆盖率达标
- [ ] API文档已更新
- [ ] 错误处理完善
- [ ] 日志记录合理
- [ ] 性能考虑（查询优化、缓存等）
- [ ] 安全检查（权限验证、输入验证）

### 发布流程

#### 版本管理
```python
# app/__init__.py
__version__ = "1.0.0"

# 版本号规则：MAJOR.MINOR.PATCH
# MAJOR: 不兼容的API修改
# MINOR: 向下兼容的功能新增
# PATCH: 向下兼容的问题修正
```

#### 发布检查清单
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 文档更新完成
- [ ] 变更日志更新
- [ ] 数据库迁移脚本准备
- [ ] 回滚方案准备


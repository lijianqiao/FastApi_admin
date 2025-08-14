# FastAPI RBAC 后台管理系统

基于 FastAPI 的现代化 RBAC 权限管理系统，提供完整的用户、角色、权限管理和操作日志功能。

## 🚀 核心特性

- **RBAC 权限模型** - 用户-角色-权限三层权限控制
- **操作日志系统** - 自动记录用户操作行为
- **JWT 认证** - 安全的身份验证和授权
- **依赖注入权限控制** - 基于装饰器的细粒度权限检查
- **软删除支持** - 数据安全保护，支持恢复
- **高性能 DAO 层** - 支持批量操作、缓存优化
- **统一异常处理** - 标准化错误响应

## 📁 项目结构

```
app/
├── main.py                 # 应用入口
├── core/                   # 核心组件
│   ├── config.py           # 配置管理
│   ├── security.py         # JWT 安全管理
│   ├── permissions/        # 权限系统
│   │   └── simple_decorators.py  # 权限装饰器
│   ├── exceptions.py       # 异常处理
│   └── middleware.py       # 中间件
├── models/                 # 数据模型
│   ├── user.py             # 用户模型
│   ├── role.py             # 角色模型
│   ├── permission.py       # 权限模型
│   └── operation_log.py    # 操作日志模型
├── dao/                    # 数据访问层
├── services/               # 业务逻辑层
├── schemas/                # 数据校验层
├── api/v1/                 # API 接口层
│   ├── auth.py             # 认证接口
│   ├── users.py            # 用户管理
│   ├── roles.py            # 角色管理
│   ├── permissions.py      # 权限管理
│   └── operation_logs.py   # 操作日志
└── utils/                  # 工具函数
    ├── deps.py             # 依赖注入
    └── operation_logger.py # 操作日志装饰器
```

## ⚡ 快速开始

```bash
# 创建环境
uv venv --python 3.13

# 安装依赖
uv sync

# 配置环境变量 (记得创建数据库，修改对应配置)
cp .env.example .env

# 初始化数据库
aerich init-db

# 初始化管理员用户、角色、权限 (环境变量文件可以修改初始化管理员账户的相关信息)
uv run python manage_db.py init

# 运行应用
uv run python start.py
```

访问: http://127.0.0.1:8000/api/docs

## 🧪 测试

项目包含一套完整的测试用例，覆盖了核心的 API 端点和业务逻辑。

```bash
# 运行所有测试
pytest
```

## 🌟 权限系统

### RBAC 模型
- **用户 (User)**: 系统使用者
- **角色 (Role)**: 权限的集合
- **权限 (Permission)**: 具体的操作权限

### 权限控制
```python
# API 端点权限控制
@router.get("/users")
async def list_users(
    context: OperationContext = Depends(require_permission("user:read"))
):
    """获取用户列表"""
    pass

# 多权限检查
@router.put("/users/{user_id}")
async def update_user(
    context: OperationContext = Depends(require_any_permission("user:update", "admin:write"))
):
    """更新用户"""
    pass
```

### 操作日志
```python
# 自动记录操作日志
@log_create_with_context("user")
async def create_user(self, request: UserCreateRequest, operation_context: OperationContext):
    """创建用户时自动记录日志"""
    pass
```

## 🔧 核心组件

### 权限常量
```python
class Permissions:
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 角色管理
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    # ...
```

### 基础模型
```python
class BaseModel(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)  # 软删除
    version = fields.IntField(default=1)  # 乐观锁
```

## 🔒 安全特性

- JWT Token 认证
- 权限缓存机制
- 软删除数据保护
- 操作日志审计
- 乐观锁防并发冲突
- CORS 跨域支持

## 📄 许可证

MIT License

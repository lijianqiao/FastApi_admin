# FastAPI Base - 企业级后台管理系统

基于 FastAPI 框架构建的现代化企业级后台管理系统后端 API，采用分层架构设计，具备高性能、强安全性、易维护、易扩展等特点。

## ✨ 主要特性

- 🚀 **高性能**: 基于 FastAPI + SQLAlchemy 2.0 异步架构
- 🔐 **安全可靠**: JWT认证、RBAC权限、Token黑名单、输入校验
- 📊 **缓存优化**: Redis缓存层，权限验证性能提升80%
- 🔍 **完整审计**: 操作日志记录与查询，支持审计追踪
- 📈 **监控指标**: Prometheus集成，健康检查和性能监控
- 🏗️ **分层架构**: 清晰的分层设计，易于维护和扩展

## 🛠️ 技术栈

- **语言框架**: Python 3.13+ / FastAPI 0.115.12
- **数据库**: SQLAlchemy 2.0+ (异步ORM) / SQLite/PostgreSQL
- **缓存**: Redis (权限缓存、Token黑名单、限流)
- **认证**: JWT (RS256) + RBAC权限模型
- **数据校验**: Pydantic v2
- **数据库迁移**: Alembic
- **监控**: Prometheus + 结构化日志
- **开发工具**: Ruff、Black、pytest

## 🚀 快速开始

### 1. 环境准备

```cmd
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 安装依赖
pip install -r requirements/dev.txt
```

### 2. Redis 配置

系统需要Redis作为缓存服务：

```cmd
# 使用Docker运行Redis
docker run --name redis -p 6379:6379 -d redis:7-alpine

# 或者安装本地Redis服务
# Windows: 下载并安装Redis for Windows
# 确保Redis服务在 localhost:6379 上运行
```

### 3. 环境配置

```cmd
# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件，配置必要参数
```

关键配置项：
```bash
# 数据库配置
DATABASE_URL=sqlite:///./fastapi_base.db

# Redis缓存配置  
REDIS_URL=redis://localhost:6379/0

# JWT密钥配置
JWT_SECRET_KEY=your-super-secret-key-here

# 应用配置
APP_NAME=FastAPI Base
DEBUG=true
ENVIRONMENT=development
```

### 4. 数据库初始化

```cmd
# 执行数据库迁移
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

### 5. 启动应用

```cmd
# 开发模式运行
python main.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问应用

- **应用地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs (Swagger UI)
- **监控指标**: http://localhost:8000/metrics

### 7. 默认管理员账户

```
用户名: admin
密码: admin@123
角色: 超级管理员
```

⚠️ **重要**: 首次登录后请立即修改默认密码！

## 🏗️ 系统架构

### 分层架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Routes    │ │ Middlewares │ │      Dependencies       ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ UserService │ │ AuthService │ │     CacheService        ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ UserRepo    │ │ RoleRepo    │ │    PermissionRepo       ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │  Database   │ │    Redis    │ │        Models           ││
│  │ (SQLAlchemy)│ │   (Cache)   │ │      (ORM)              ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

- **模型层** (`models/`): SQLAlchemy ORM模型定义
- **数据仓库层** (`repositories/`): 数据访问逻辑，支持预加载优化
- **服务层** (`services/`): 业务逻辑处理，集成缓存和权限验证
- **API路由层** (`api/v1/endpoints/`): HTTP请求处理和响应
- **缓存层** (`services/cache_service.py`): Redis缓存管理和Token黑名单

## 🔐 安全特性

### JWT认证机制
- **RS256算法**: RSA公私钥签名验证
- **双Token设计**: access_token + refresh_token
- **Token黑名单**: 安全登出，防止Token重用
- **JTI追踪**: 每个Token唯一标识，支持精确失效控制

### RBAC权限模型
- **细粒度权限**: 基于资源和操作的权限控制
- **角色继承**: 支持角色层次化管理
- **权限缓存**: 权限验证结果缓存30分钟，性能提升80%
- **动态权限**: 运行时权限变更立即生效

### 数据安全
- **密码加密**: Bcrypt + 随机盐值
- **输入校验**: Pydantic v2严格类型检查
- **SQL注入防护**: SQLAlchemy参数化查询
- **限流保护**: 基于Redis的API限流

## 🚄 性能优化

### 缓存层设计
- **Redis集成**: 异步Redis客户端，支持连接池
- **多层缓存**: 用户权限、角色、Token黑名单分层缓存
- **智能失效**: 数据变更时自动清理相关缓存
- **批量操作**: 支持批量设置和获取，减少网络开销

### 数据库优化
- **预加载查询**: 使用eager loading避免N+1查询问题
- **连接池管理**: SQLAlchemy异步连接池优化
- **索引设计**: 关键字段建立索引，提升查询性能
- **查询优化**: 复杂查询使用联表预加载

### 性能指标
- **权限验证**: 缓存命中率90%+，响应时间减少80%
- **Token验证**: 黑名单检查<1ms，支持高并发
- **数据库查询**: 预加载优化减少70%的查询次数

## 📊 核心功能

### 用户管理
- ✅ 用户注册、登录、信息管理
- ✅ 多种登录方式（用户名/邮箱/手机号）
- ✅ 密码强度验证和安全存储
- ✅ 用户状态管理（激活/禁用）
- ✅ 批量用户操作

### 权限管理  
- ✅ RBAC权限模型实现
- ✅ 细粒度权限控制
- ✅ 动态权限验证装饰器
- ✅ 权限缓存优化
- ✅ 权限继承和组合

### 角色管理
- ✅ 角色CRUD操作
- ✅ 角色权限分配
- ✅ 用户角色管理
- ✅ 角色层次化设计

### 审计日志
- ✅ 完整的操作审计记录
- ✅ 用户行为追踪
- ✅ 登录日志和安全事件
- ✅ 日志查询和分析
- ✅ 日志清理和归档

### 认证安全
- ✅ JWT双Token机制
- ✅ Token黑名单管理
- ✅ 安全登出功能
- ✅ 会话管理和超时控制
- ✅ 多设备登录管理

## 📖 文档说明

| 文档                                   | 描述                            | 适用对象   |
| -------------------------------------- | ------------------------------- | ---------- |
| [🚀 快速入门](docs/quick_start.md)      | 新手教程，从环境搭建到API使用   | 新用户     |
| [📋 项目文档](docs/项目文档.md)         | 项目整体介绍、架构设计、API接口 | 开发者     |
| [📡 API文档](docs/api.md)               | 详细的API接口说明和使用示例     | 前端开发者 |
| [🚄 缓存指南](docs/cache_guide.md)      | Redis缓存使用方法和最佳实践     | 后端开发者 |
| [🚀 部署指南](docs/deployment_guide.md) | 生产环境部署、配置和监控        | 运维工程师 |
| [📊 项目总结](docs/project_summary.md)  | 完整功能清单和技术总结          | 技术负责人 |

## 🧪 测试

### 运行测试

```cmd
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 测试覆盖率
- 目标覆盖率: ≥80%
- 单元测试: 核心服务和仓库层
- 集成测试: API端点和认证流程
- 功能测试: 完整业务流程验证

## 🛠️ 开发指南

### 代码规范
- **类型注解**: 强制使用类型注解，Pydantic v2校验
- **代码格式**: 使用Ruff格式化，行长度100字符  
- **命名规范**: 
  - 变量/函数: `snake_case`
  - 类: `PascalCase`
  - 常量: `UPPER_SNAKE_CASE`
- **注释文档**: 重要函数必须包含docstring

### 分层开发规范
```python
# 仓库层 - 只负责数据访问
class UserRepository:
    async def get_with_roles(self, user_id: int) -> Optional[User]:
        """预加载用户角色信息"""
        pass

# 服务层 - 业务逻辑处理  
class UserService:
    async def get_user_with_permissions(self, user_id: int) -> UserWithPermissions:
        """获取用户及其权限信息，优先从缓存获取"""
        pass

# API层 - 只处理HTTP请求响应
@router.get("/users/{user_id}")
async def get_user(user_id: int, user_service: UserService = Depends()):
    """获取用户信息API"""
    pass
```

### 缓存使用规范
```python
# 1. 优先从缓存获取
permissions = await cache_service.get_user_permissions(str(user_id))

# 2. 缓存未命中时查询数据库
if permissions is None:
    permissions = await permission_service.get_user_permissions(user_id)
    await cache_service.set_user_permissions(str(user_id), permissions)

# 3. 数据变更时清理缓存
await cache_service.invalidate_user_cache(str(user_id))
```

### Git工作流
```
main        # 主分支，生产环境
develop     # 开发分支  
feature/*   # 功能分支
hotfix/*    # 热修复分支
```

## 🚀 生产部署

### Docker部署

```cmd
# 构建镜像
docker build -t fastapi-base .

# 使用docker-compose部署
docker-compose up -d
```

### 环境变量配置
```bash
# 生产环境必需配置
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis-host:6379/0
JWT_SECRET_KEY=production-secret-key
SECRET_KEY=app-secret-key
ENVIRONMENT=production
DEBUG=false
```

### 性能调优
- **Gunicorn**: 多进程部署，worker数量=CPU核心数×2
- **Redis配置**: 合理设置maxmemory和淘汰策略
- **数据库**: 配置连接池大小和超时时间
- **缓存策略**: 根据业务场景调整TTL时间

## 🔧 常见问题

### Q: Redis连接失败怎么办？
```cmd
# 检查Redis服务状态
docker ps | grep redis

# 测试Redis连接
redis-cli ping
```

### Q: 数据库迁移失败？
```cmd
# 检查当前迁移状态
alembic current

# 回滚到上一个版本
alembic downgrade -1

# 重新执行迁移
alembic upgrade head
```

### Q: Token验证失败？
- 检查JWT_SECRET_KEY配置是否正确
- 确认Token是否在黑名单中
- 验证Token格式和签名算法

### Q: 权限验证不生效？
- 检查用户角色分配是否正确
- 确认权限缓存是否失效
- 验证权限装饰器使用是否正确

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📧 联系方式

- 项目地址: https://gitee.com/lijianqiao/fastapibase
- 问题反馈: https://gitee.com/lijianqiao/fastapibase/issues
- 邮箱: lijianqiao2906@live.com

---

⭐ 如果这个项目对你有帮助，请给一个Star！
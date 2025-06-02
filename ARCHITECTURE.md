# 架构重构建议

## 当前问题
当前的 `app/models/models.py` 实际上是数据库模型，不是领域模型。

## 建议的分层架构

```
app/
├── models/
│   ├── domain/          # 领域模型 - 纯业务逻辑
│   │   ├── __init__.py
│   │   ├── user.py      # User 领域模型
│   │   ├── role.py      # Role 领域模型
│   │   └── permission.py # Permission 领域模型
│   │
│   ├── database/        # 数据库模型 - ORM 映射
│   │   ├── __init__.py
│   │   └── models.py    # 当前的 SQLAlchemy 模型
│   │
│   └── schemas/         # Pydantic 模型 - API 验证
│       ├── __init__.py
│       ├── user.py      # UserCreate, UserResponse 等
│       └── role.py
│
├── repositories/        # 数据访问层
│   ├── __init__.py
│   ├── user_repository.py
│   └── role_repository.py
│
└── services/           # 业务服务层
    ├── __init__.py
    ├── user_service.py
    └── auth_service.py
```

## 实现示例

### 1. 领域模型 (Domain Model)
```python
# app/models/domain/user.py
from dataclasses import dataclass
from typing import List
from .role import Role

@dataclass
class User:
    id: UUID
    username: str
    email: str
    _password_hash: str
    is_active: bool = True
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return verify_password(password, self._password_hash)
    
    def assign_role(self, role: Role) -> None:
        """分配角色 - 包含业务规则"""
        if not self.is_active:
            raise UserInactiveError("无法为非活跃用户分配角色")
        
    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        # 复杂的权限计算逻辑
        pass
```

### 2. 数据库模型 (Database Model)
```python
# app/models/database/models.py
# 当前的 SQLAlchemy 模型保持不变
class User(UUIDAuditModel):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(...)
    # 数据库相关配置
```

### 3. Repository 模式
```python
# app/repositories/user_repository.py
from app.models.domain.user import User as DomainUser
from app.models.database.models import User as DBUser

class UserRepository:
    async def find_by_id(self, user_id: UUID) -> DomainUser:
        """将数据库模型转换为领域模型"""
        db_user = await self.session.get(DBUser, user_id)
        return self._to_domain(db_user)
    
    def _to_domain(self, db_user: DBUser) -> DomainUser:
        """数据库模型 -> 领域模型"""
        return DomainUser(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            _password_hash=db_user.password,
            is_active=db_user.is_active
        )
    
    def _to_database(self, domain_user: DomainUser) -> DBUser:
        """领域模型 -> 数据库模型"""
        # 转换逻辑
        pass
```

### 4. 业务服务
```python
# app/services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def authenticate_user(self, username: str, password: str) -> DomainUser:
        """用户认证 - 业务逻辑"""
        user = await self.user_repo.find_by_username(username)
        if not user.verify_password(password):
            raise AuthenticationError("密码错误")
        return user
```

## 迁移步骤

1. **保持当前代码**：不破坏现有功能
2. **创建领域模型**：在 `models/domain/` 中创建纯业务模型
3. **重构仓储层**：实现领域模型和数据库模型的转换
4. **迁移业务逻辑**：将业务规则从服务层移到领域模型
5. **逐步替换**：在新功能中使用新架构

## 优势

- **关注点分离**：业务逻辑与持久化分离
- **可测试性**：领域模型易于单元测试
- **可维护性**：业务规则集中在领域模型中
- **扩展性**：符合 DDD 和企业级架构原则
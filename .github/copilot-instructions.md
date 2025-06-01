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


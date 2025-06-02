"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:32:03
@Docs: Pydantic 模式模块

定义 API 请求和响应的数据模型
"""

from .permission import (
    PermissionBase,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
)
from .role import (
    RoleBase,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from .user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "UserPasswordChange",
    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleResponse",
    "RoleUpdate",
    # Permission schemas
    "PermissionBase",
    "PermissionCreate",
    "PermissionResponse",
    "PermissionUpdate",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:32:03
@Docs: 领域模型模块

领域模型包含纯业务逻辑，不依赖于特定的持久化技术或框架。
"""

from .exceptions import (
    DomainException,
    InvalidCredentialsError,
    PermissionDeniedError,
    RoleAssignmentError,
    UserInactiveError,
)
from .permission import Permission
from .role import Role
from .user import User

__all__ = [
    "User",
    "Role",
    "Permission",
    "DomainException",
    "UserInactiveError",
    "PermissionDeniedError",
    "InvalidCredentialsError",
    "RoleAssignmentError",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/03 02:32:03
@Docs: 仓库层模块导出
"""

from .base import (
    AbstractBaseRepository,
    AutoIdBaseRepository,
    AutoIdModel,
    AutoIdModelT,
    BaseModel,
    BaseRepository,
    IdType,
    ModelT,
    UUIDModelT,
)
from .repositories import AuditLogRepository, PermissionRepository, RoleRepository, UserRepository

__all__ = [
    "BaseModel",
    "AutoIdModel",
    "AbstractBaseRepository",
    "BaseRepository",
    "AutoIdBaseRepository",
    "UUIDModelT",
    "ModelT",
    "IdType",
    "AutoIdModelT",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "AuditLogRepository",
]

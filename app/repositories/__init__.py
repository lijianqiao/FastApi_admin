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
    BaseRepository,
    BigIntAuditBase,
    BigIntAuditBaseT,
    IdType,
    ModelT,
    UUIDAuditBase,
    UUIDModelT,
)
from .repositories import AuditLogRepository, PermissionRepository, RoleRepository, UserRepository

__all__ = [
    "UUIDAuditBase",
    "BigIntAuditBase",
    "AbstractBaseRepository",
    "BaseRepository",
    "AutoIdBaseRepository",
    "UUIDModelT",
    "ModelT",
    "IdType",
    "BigIntAuditBaseT",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "AuditLogRepository",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/05/29 19:39:42
@Docs: 数据库模块初始化
"""

from app.db.base import (
    AuditMixin,
    Base,
    BigIntAuditModel,
    BigIntModel,
    SlugMixin,
    UniqueMixin,
    UUIDAuditModel,
    UUIDModel,
)
from app.db.session import (
    DatabaseManager,
    database_manager,
    get_async_session,
    get_repository_session,
    get_sqlalchemy_config,
    sqlalchemy_config,
)

__all__ = [
    "Base",
    # UUID 基类
    "UUIDModel",
    "UUIDAuditModel",
    # BigInt 基类
    "BigIntModel",
    "BigIntAuditModel",
    # Mixins
    "AuditMixin",
    "SlugMixin",
    "UniqueMixin",
    # 会话管理
    "get_async_session",
    "get_repository_session",
    "get_sqlalchemy_config",
    "sqlalchemy_config",
    # 数据库管理
    "DatabaseManager",
    "database_manager",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/05/29 19:39:42
@Docs: 数据库模块初始化 - 简化设计
"""

from advanced_alchemy.base import BigIntAuditBase, UUIDAuditBase

from app.db.session import (
    DatabaseManager,
    database_manager,
    get_async_session,
    get_sqlalchemy_config,
    sqlalchemy_config,
)

__all__ = [
    # 基础模型
    "UUIDAuditBase",
    "BigIntAuditBase",
    # 会话管理
    "get_async_session",
    "get_sqlalchemy_config",
    "sqlalchemy_config",
    # 数据库管理
    "DatabaseManager",
    "database_manager",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/05/29 19:39:42
@Docs: 模型初始化模块 - 简化设计
"""

from .models import AuditLog, Permission, Role, User

__all__ = [
    "User",
    "Role",
    "Permission",
    "AuditLog",
]

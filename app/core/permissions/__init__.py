"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/01/01
@Docs: 权限系统模块（简化版）
"""

from app.core.permissions.simple_decorators import (
    Permissions,
    has_permission,
    permission_manager,
    require_all_permissions,
    require_any_permission,
    require_permission,
)

__all__ = [
    "Permissions",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "has_permission",
    "permission_manager",
]

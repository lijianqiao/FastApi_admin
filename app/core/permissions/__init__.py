"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/01/01
@Docs: 权限系统模块（简化版）
"""

from app.core.permissions.simple_decorators import require_permission

__all__ = ["require_permission"]

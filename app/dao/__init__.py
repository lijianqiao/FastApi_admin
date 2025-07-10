"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/01/01
@Docs: DAO层统一导出
"""

from app.dao.base import BaseDAO
from app.dao.operation_log import OperationLogDAO
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO

__all__ = [
    "BaseDAO",
    "UserDAO",
    "RoleDAO",
    "PermissionDAO",
    "OperationLogDAO",
]

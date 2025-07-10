"""
-*- coding: utf-8 -*-
 @Author: li
 @Email: lijianqiao2906@live.com
 @FileName: __init__.py
 @DateTime: 2025/3/11 上午9:53
 @Docs: 服务层模块导出
"""

from app.services.auth import AuthService
from app.services.base import BaseService
from app.services.operation_log import OperationLogService
from app.services.permission import PermissionService
from app.services.role import RoleService
from app.services.user import UserService

__all__ = [
    "BaseService",
    "UserService",
    "AuthService",
    "RoleService",
    "PermissionService",
    "OperationLogService",
]

"""
通用服务注册与聚合层

用于统一注册和聚合所有具体服务，便于依赖注入和管理。
"""

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: services.py
@DateTime: 2025/06/03
@Docs: 应用核心服务层实现 - 服务工厂和依赖管理
"""

from typing import TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.audit_service import AuditLogService
from app.services.auth_service import AuthService
from app.services.base import AppBaseService
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.services.user_service import UserService

T = TypeVar("T", bound=AppBaseService)


class ServiceFactory:
    """
    服务工厂类

    提供统一的服务实例创建和管理功能
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._instances = {}

    def get_auth_service(self) -> AuthService:
        """获取认证服务实例"""
        if "auth" not in self._instances:
            self._instances["auth"] = AuthService(self.session)
        return self._instances["auth"]

    def get_user_service(self) -> UserService:
        """获取用户服务实例"""
        if "user" not in self._instances:
            self._instances["user"] = UserService(self.session)
        return self._instances["user"]

    def get_permission_service(self) -> PermissionService:
        """获取权限服务实例"""
        if "permission" not in self._instances:
            self._instances["permission"] = PermissionService(self.session)
        return self._instances["permission"]

    def get_role_service(self) -> RoleService:
        """获取角色服务实例"""
        if "role" not in self._instances:
            self._instances["role"] = RoleService(self.session)
        return self._instances["role"]

    def get_audit_log_service(self) -> AuditLogService:
        """获取审计日志服务实例"""
        if "audit_log" not in self._instances:
            self._instances["audit_log"] = AuditLogService(self.session)
        return self._instances["audit_log"]

    def get_service(self, service_class: type[T]) -> T:
        """
        通用服务获取方法

        Args:
            service_class: 服务类型

        Returns:
            服务实例
        """
        service_name = service_class.__name__.lower()
        if service_name not in self._instances:
            self._instances[service_name] = service_class(self.session)
        return self._instances[service_name]

    def clear_cache(self):
        """清理服务实例缓存"""
        self._instances.clear()


async def get_service_factory(session: AsyncSession = Depends(get_async_session)) -> ServiceFactory:
    """
    获取服务工厂实例

    Args:
        session: 数据库会话

    Returns:
        服务工厂实例
    """
    return ServiceFactory(session)

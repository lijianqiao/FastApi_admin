"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dependencies.py
@DateTime: 2025/06/05
@Docs: API依赖注入系统 - 认证、权限检查、用户获取
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.models import User
from app.services.services import ServiceFactory, get_service_factory

# OAuth2 Bearer Token 获取
security = HTTPBearer()


async def get_current_user_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    """
    获取当前用户的访问令牌

    Args:
        credentials: HTTP Bearer 认证凭据

    Returns:
        访问令牌字符串

    Raises:
        HTTPException: 当认证失败时
    """
    return credentials.credentials


async def get_current_user(
    token: Annotated[str, Depends(get_current_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> User:
    """
    获取当前认证用户

    Args:
        token: 访问令牌
        session: 数据库会话
        service_factory: 服务工厂

    Returns:
        当前用户对象

    Raises:
        HTTPException: 当用户不存在或令牌无效时
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码访问令牌
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception from None

    # 获取用户服务并查询用户
    user_service = service_factory.get_user_service()
    user = await user_service.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    获取活跃用户（已激活且未禁用）

    Args:
        current_user: 当前用户

    Returns:
        活跃用户对象

    Raises:
        HTTPException: 当用户未激活时
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_superuser(current_user: Annotated[User, Depends(get_active_user)]) -> User:
    """
    获取超级管理员用户

    Args:
        current_user: 当前活跃用户

    Returns:
        超级管理员用户对象

    Raises:
        HTTPException: 当用户不是超级管理员时
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


def require_permissions(*required_permissions: str) -> Callable:
    """
    权限检查装饰器工厂

    Args:
        *required_permissions: 需要的权限列表

    Returns:
        权限检查依赖函数
    """

    async def check_permissions(
        current_user: Annotated[User, Depends(get_active_user)],
        service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    ) -> User:
        """
        检查用户权限

        Args:
            current_user: 当前活跃用户
            service_factory: 服务工厂

        Returns:
            通过权限检查的用户

        Raises:
            HTTPException: 当权限不足时
        """
        # 超级管理员拥有所有权限
        if current_user.is_superuser:
            return current_user

        # 检查用户权限
        permission_service = service_factory.get_permission_service()
        user_permissions = await permission_service.get_user_permissions(current_user.id)
        user_permission_names = {perm.name for perm in user_permissions}

        # 检查是否拥有所需的所有权限
        missing_permissions = set(required_permissions) - user_permission_names
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}",
            )

        return current_user

    return check_permissions


def require_roles(*required_roles: str) -> Callable:
    """
    角色检查装饰器工厂

    Args:
        *required_roles: 需要的角色列表

    Returns:
        角色检查依赖函数
    """

    async def check_roles(
        current_user: Annotated[User, Depends(get_active_user)],
        service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    ) -> User:
        """
        检查用户角色

        Args:
            current_user: 当前活跃用户
            service_factory: 服务工厂

        Returns:
            通过角色检查的用户

        Raises:
            HTTPException: 当角色不符时
        """  # 超级管理员拥有所有角色
        if current_user.is_superuser:
            return current_user

        # 检查用户角色
        user_service = service_factory.get_user_service()
        user_with_roles = await user_service.get_user_roles(current_user.id)
        user_role_names = {role.name for role in user_with_roles.roles}

        # 检查是否拥有所需的任一角色
        if not any(role in user_role_names for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}",
            )

        return current_user

    return check_roles


def require_any_permission(*required_permissions: str) -> Callable:
    """
    任一权限检查装饰器工厂（拥有其中任一权限即可）

    Args:
        *required_permissions: 需要的权限列表

    Returns:
        权限检查依赖函数
    """

    async def check_any_permission(
        current_user: Annotated[User, Depends(get_active_user)],
        service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    ) -> User:
        """
        检查用户是否拥有任一所需权限

        Args:
            current_user: 当前活跃用户
            service_factory: 服务工厂

        Returns:
            通过权限检查的用户

        Raises:
            HTTPException: 当权限不足时
        """
        # 超级管理员拥有所有权限
        if current_user.is_superuser:
            return current_user

        # 检查用户权限
        permission_service = service_factory.get_permission_service()
        user_permissions = await permission_service.get_user_permissions(current_user.id)
        user_permission_names = {perm.name for perm in user_permissions}

        # 检查是否拥有任一所需权限
        if not any(perm in user_permission_names for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required any of permissions: {', '.join(required_permissions)}",
            )

        return current_user

    return check_any_permission


def require_all_roles(*required_roles: str) -> Callable:
    """
    全部角色检查装饰器工厂（需要拥有所有指定角色）

    Args:
        *required_roles: 需要的角色列表

    Returns:
        角色检查依赖函数
    """

    async def check_all_roles(
        current_user: Annotated[User, Depends(get_active_user)],
        service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    ) -> User:
        """
        检查用户是否拥有所有指定角色

        Args:
            current_user: 当前活跃用户
            service_factory: 服务工厂

        Returns:
            通过角色检查的用户

        Raises:
            HTTPException: 当角色不符时
        """
        # 超级管理员拥有所有角色
        if current_user.is_superuser:
            return current_user  # 检查用户角色
        user_service = service_factory.get_user_service()
        user_with_roles = await user_service.get_user_roles(current_user.id)
        user_role_names = {role.name for role in user_with_roles.roles}

        # 检查是否拥有所有指定角色
        missing_roles = set(required_roles) - user_role_names
        if missing_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing roles: {', '.join(missing_roles)}",
            )

        return current_user

    return check_all_roles


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    service_factory: ServiceFactory = Depends(get_service_factory),
) -> User | None:
    """
    获取可选用户（可以为空，用于公共接口）

    Args:
        credentials: HTTP Bearer 认证凭据（可选）
        service_factory: 服务工厂

    Returns:
        用户对象或None
    """
    if not credentials:
        return None
    try:
        # 解码访问令牌
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            return None

        # 获取用户服务并查询用户
        user_service = service_factory.get_user_service()
        user = await user_service.get_user_by_id(user_id)

        return user if user and user.is_active else None
    except Exception:
        return None


class PermissionChecker:
    """权限检查器类，用于复杂权限逻辑"""

    def __init__(self, service_factory: ServiceFactory):
        self.service_factory = service_factory

    async def has_permission(self, user: User, permission: str) -> bool:
        """检查用户是否拥有指定权限"""
        if user.is_superuser:
            return True
        permission_service = self.service_factory.get_permission_service()
        user_permissions = await permission_service.get_user_permissions(user.id)
        return any(perm.name == permission for perm in user_permissions)

    async def has_role(self, user: User, role: str) -> bool:
        """检查用户是否拥有指定角色"""
        if user.is_superuser:
            return True

        user_service = self.service_factory.get_user_service()
        user_with_roles = await user_service.get_user_roles(user.id)
        return any(r.name == role for r in user_with_roles.roles)

    async def can_access_resource(self, user: User, resource_id: int, action: str) -> bool:
        """检查用户是否可以访问特定资源"""
        # 这里可以实现更复杂的资源访问控制逻辑
        # 例如：检查资源所有者、部门权限等
        return await self.has_permission(user, f"{action}_{resource_id}")


async def get_permission_checker(
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> PermissionChecker:
    """获取权限检查器实例"""
    return PermissionChecker(service_factory)


# 常用依赖注入类型别名
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_active_user)]
SuperUser = Annotated[User, Depends(get_superuser)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
PermissionCheckerDep = Annotated[PermissionChecker, Depends(get_permission_checker)]
ServiceFactoryDep = Annotated[ServiceFactory, Depends(get_service_factory)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# 常用权限检查依赖
RequireUserRead = Depends(require_permissions("user:read"))
RequireUserWrite = Depends(require_permissions("user:write"))
RequireUserDelete = Depends(require_permissions("user:delete"))
RequireRoleManage = Depends(require_permissions("role:manage"))
RequirePermissionManage = Depends(require_permissions("permission:manage"))
RequireSystemConfig = Depends(require_permissions("system:config"))

# 常用角色检查依赖
RequireAdminRole = Depends(require_roles("admin"))
RequireManagerRole = Depends(require_roles("manager"))
RequireModeratorRole = Depends(require_roles("moderator"))

# 复合权限检查依赖
RequireUserManagement = Depends(require_permissions("user:read", "user:write"))
RequireFullAccess = Depends(require_permissions("system:admin", "user:admin", "role:admin"))
RequireContentModeration = Depends(require_any_permission("content:moderate", "content:admin"))

# 复合角色检查依赖
RequireAdminOrManager = Depends(require_roles("admin", "manager"))
RequireAllManagerRoles = Depends(require_all_roles("manager", "supervisor"))

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: simple_decorators.py
@DateTime: 2025/07/09
@Docs: 现代化权限管理 - 依赖注入为主导
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Literal
from uuid import UUID

from fastapi import Depends

from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.dao.user import UserDAO
from app.models.user import User
from app.utils.deps import OperationContext, get_operation_context
from app.utils.logger import logger


class PermissionCache:
    """权限缓存管理器 - 使用Redis缓存"""

    def __init__(self):
        self.cache_ttl = settings.PERMISSION_CACHE_TTL
        self.enable_redis = settings.ENABLE_REDIS_CACHE
        logger.info(f"权限缓存配置: Redis启用={self.enable_redis}, TTL={self.cache_ttl}秒")

    async def _get_cache_backend(self):
        """获取缓存后端"""
        if not self.enable_redis:
            logger.info("权限缓存: 配置禁用Redis，使用内存缓存")
            from app.utils.redis_cache import _memory_fallback

            return _memory_fallback

        # 配置启用Redis时尝试连接
        try:
            from app.utils.redis_cache import get_redis_cache

            redis_cache = await get_redis_cache()

            # 测试Redis连接
            test_result = await redis_cache.set("test:connection", "ok", 10)
            if test_result:
                await redis_cache.delete("test:connection")
                logger.debug("权限缓存: Redis连接测试成功，使用Redis缓存")
                return redis_cache
            else:
                raise Exception("Redis连接测试失败")

        except Exception as e:
            logger.warning(f"权限缓存: Redis不可用，降级到内存缓存: {e}")
            from app.utils.redis_cache import _memory_fallback

            return _memory_fallback

    async def get_user_permissions(self, user_id: UUID) -> set[str]:
        """获取用户权限（含缓存）"""
        cache_key = f"user:permissions:{user_id}"
        cache_backend = await self._get_cache_backend()
        backend_type = cache_backend.__class__.__name__

        # 尝试从缓存获取
        cached_permissions = await cache_backend.get(cache_key)
        if cached_permissions is not None:
            logger.info(f"权限缓存命中: 用户={user_id}, 后端={backend_type}, 权限数量={len(cached_permissions)}")
            logger.debug(f"缓存权限详情: {cached_permissions}")
            return cached_permissions

        # 缓存未命中，从数据库获取
        logger.info(f"权限缓存未命中: 用户={user_id}, 后端={backend_type}, 从数据库加载")
        permissions = await self._fetch_user_permissions(user_id)

        # 存入缓存
        success = await cache_backend.set(cache_key, permissions, self.cache_ttl)
        if success:
            logger.info(
                f"权限缓存设置成功: 用户={user_id}, 后端={backend_type}, 权限数量={len(permissions)}, TTL={self.cache_ttl}秒"
            )
            logger.debug(f"新缓存权限详情: {permissions}")
        else:
            logger.warning(f"权限缓存设置失败: 用户={user_id}, 后端={backend_type}")

        return permissions

    async def _fetch_user_permissions(self, user_id: UUID) -> set[str]:
        """从数据库获取用户的所有权限码"""
        try:
            user_dao = UserDAO()
            user = await user_dao.get_with_related(
                user_id, prefetch_related=["roles", "permissions", "roles__permissions"]
            )
            if not user:
                return set()

            all_permission_codes: set[str] = set()

            # 添加直接分配给用户的权限
            if user.permissions:
                for p in user.permissions:
                    if p.is_active:  # 只获取激活的权限
                        all_permission_codes.add(p.permission_code)

            # 添加通过角色继承的权限
            if user.roles:
                for role in user.roles:
                    if role.is_active and role.permissions:
                        for p in role.permissions:
                            if p.is_active:  # 只获取激活的权限
                                all_permission_codes.add(p.permission_code)

            return all_permission_codes
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return set()

    async def invalidate_user_cache(self, user_id: UUID):
        """清除用户权限缓存"""
        cache_key = f"user:permissions:{user_id}"
        cache_backend = await self._get_cache_backend()
        backend_type = cache_backend.__class__.__name__

        success = await cache_backend.delete(cache_key)
        if success:
            logger.info(f"用户权限缓存清除成功: 用户={user_id}, 后端={backend_type}")
        else:
            logger.warning(f"用户权限缓存清除失败: 用户={user_id}, 后端={backend_type}")

    async def invalidate_role_cache(self, role_id: UUID):
        """清除角色相关的所有用户权限缓存"""
        try:
            user_dao = UserDAO()
            user_ids = await user_dao.get_user_ids_by_role(role_id)
            if not user_ids:
                logger.info(f"没有用户使用角色 {role_id}，无需清除缓存")
                return
            cache_backend = await self._get_cache_backend()
            backend_type = cache_backend.__class__.__name__
            tasks = [self.invalidate_user_cache(user_id) for user_id in user_ids]
            await asyncio.gather(*tasks)
            logger.info(f"角色 {role_id} 相关的用户权限缓存清除完成，后端={backend_type}")
        except Exception as e:
            logger.error(f"清除角色 {role_id} 相关的用户权限缓存失败: {e}")

    async def clear_all_cache(self):
        """清除所有权限缓存"""
        cache_backend = await self._get_cache_backend()
        await cache_backend.clear_all()
        logger.info("所有权限缓存已清除")

    async def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        cache_backend = await self._get_cache_backend()
        backend_type = cache_backend.__class__.__name__

        logger.debug(f"获取缓存统计: 后端类型={backend_type}, 配置启用Redis={self.enable_redis}")

        # 检查是否为Redis缓存后端（通过类名判断）
        if backend_type == "RedisCache":
            try:
                # Redis缓存统计
                client = await cache_backend._get_client()  # type: ignore
                if client:
                    info = await client.info("memory")
                    keys_count = len(await client.keys("user:permissions:*"))
                    stats = {
                        "backend": "redis",
                        "backend_class": backend_type,
                        "permission_keys": keys_count,
                        "memory_usage": info.get("used_memory_human", "N/A"),
                        "ttl": self.cache_ttl,
                        "enable_redis_config": self.enable_redis,
                    }
                    logger.debug(f"Redis缓存统计详情: {stats}")
                    return stats
            except Exception as e:
                logger.error(f"获取Redis缓存统计失败: {e}")

        # 内存缓存统计
        stats = {
            "backend": "memory",
            "backend_class": backend_type,
            "permission_keys": len(getattr(cache_backend, "_cache", {})),
            "ttl": self.cache_ttl,
            "enable_redis_config": self.enable_redis,
        }
        logger.debug(f"内存缓存统计详情: {stats}")
        return stats


_permission_cache = PermissionCache()


class PermissionManager:
    """统一的权限管理器"""

    async def get_user_permissions(self, user: User) -> set[str]:
        """获取用户的所有权限码（直接+角色），并进行缓存"""
        if user.is_superuser:
            return {"*"}
        return await _permission_cache.get_user_permissions(user.id)

    async def check_permission(self, user: User, permission: str) -> bool:
        """检查用户是否拥有特定权限"""
        if user.is_superuser:
            logger.debug(f"超级用户 {user.username} 绕过权限检查: {permission}")
            return True

        if not user.is_active:
            logger.warning(f"非激活用户 {user.username} 拒绝权限: {permission}")
            return False

        user_permissions = await self.get_user_permissions(user)
        has_perm = "*" in user_permissions or permission in user_permissions

        if not has_perm:
            logger.warning(f"用户 {user.username} 权限不足: {permission}")

        return has_perm

    async def check_any_permission(self, user: User, permissions: list[str]) -> bool:
        """检查用户是否拥有任一权限 (OR 逻辑)"""
        if user.is_superuser:
            return True

        if not user.is_active:
            return False

        for permission in permissions:
            if await self.check_permission(user, permission):
                return True
        return False

    async def check_all_permissions(self, user: User, permissions: list[str]) -> bool:
        """检查用户是否拥有所有权限 (AND 逻辑)"""
        if user.is_superuser:
            return True

        if not user.is_active:
            return False

        for permission in permissions:
            if not await self.check_permission(user, permission):
                return False
        return True

    async def clear_user_cache(self, user_id: UUID):
        """清除指定用户的权限缓存"""
        await _permission_cache.invalidate_user_cache(user_id)

    async def clear_role_cache(self, role_id: UUID):
        """清除角色相关的权限缓存"""
        await _permission_cache.invalidate_role_cache(role_id)

    async def clear_all_cache(self):
        """清除所有权限缓存"""
        await _permission_cache.clear_all_cache()

    async def get_cache_stats(self):
        """获取缓存统计信息"""
        return await _permission_cache.get_cache_stats()


permission_manager = PermissionManager()


# ===== FastAPI 依赖注入权限控制 =====


def require_permission(permission: str):
    """权限依赖注入 - 单个权限检查"""

    async def permission_dependency(context: OperationContext = Depends(get_operation_context)) -> OperationContext:
        user = context.user

        if not await permission_manager.check_permission(user, permission):
            raise ForbiddenException(f"权限不足，需要权限: {permission}")

        logger.debug(f"用户 {user.username} 权限检查通过: {permission}")
        return context

    return permission_dependency


def require_permissions(*permissions: str, logic: Literal["AND", "OR"] = "AND"):
    """权限依赖注入 - 多权限检查"""

    async def permission_dependency(context: OperationContext = Depends(get_operation_context)) -> OperationContext:
        user = context.user

        if logic == "AND":
            if not await permission_manager.check_all_permissions(user, list(permissions)):
                raise ForbiddenException(f"权限不足，需要所有权限: {' AND '.join(permissions)}")
        elif logic == "OR":
            if not await permission_manager.check_any_permission(user, list(permissions)):
                raise ForbiddenException(f"权限不足，需要任一权限: {' OR '.join(permissions)}")
        else:
            raise ValueError(f"不支持的逻辑操作: {logic}")

        logger.debug(f"用户 {user.username} 多权限检查通过: {' ' + logic + ' '.join(permissions)}")
        return context

    return permission_dependency


def require_any_permission(*permissions: str):
    """权限依赖注入 - 任一权限检查 (OR 逻辑)"""
    return require_permissions(*permissions, logic="OR")


def require_all_permissions(*permissions: str):
    """权限依赖注入 - 所有权限检查 (AND 逻辑)"""
    return require_permissions(*permissions, logic="AND")


# ===== 工具函数版权限装饰器 (仅用于非API函数) =====


def require_permission_decorator(permission: str) -> Callable:
    """权限装饰器 - 仅用于工具函数和业务逻辑函数"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 尝试从参数中获取用户信息
            context: OperationContext | None = kwargs.get("operation_context")
            user: User | None = kwargs.get("current_user")

            if context:
                user = context.user
            elif not user:
                # 从参数中查找User对象
                for arg in args:
                    if isinstance(arg, User):
                        user = arg
                        break

            if not user:
                raise UnauthorizedException("用户未认证")

            if not await permission_manager.check_permission(user, permission):
                raise ForbiddenException(f"权限不足，需要权限: {permission}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ===== 权限常量定义 =====


class Permissions:
    """权限常量 - 避免硬编码"""

    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLES = "user:assign_roles"
    USER_ASSIGN_PERMISSIONS = "user:assign_permissions"
    USER_ACCESS = "user:access"  # 用户模块访问权限

    # 角色管理
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_ASSIGN_PERMISSIONS = "role:assign_permissions"
    ROLE_ACCESS = "role:access"  # 角色模块访问权限

    # 权限管理
    PERMISSION_CREATE = "permission:create"
    PERMISSION_READ = "permission:read"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"
    PERMISSION_ACCESS = "permission:access"  # 权限模块访问权限

    # 菜单管理
    MENU_CREATE = "menu:create"
    MENU_READ = "menu:read"
    MENU_UPDATE = "menu:update"
    MENU_DELETE = "menu:delete"
    MENU_ACCESS = "menu:access"  # 菜单模块访问权限

    # 日志管理
    LOG_VIEW = "log:view"
    LOG_DELETE = "log:delete"
    LOG_ACCESS = "log:access"  # 日志模块访问权限

    # 系统管理
    SYSTEM_CONFIG = "system:config"
    SYSTEM_ADMIN = "system:admin"

    # 后台管理
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"

    # 用户密码重置
    USER_RESET_PASSWORD = "user:reset_password"


# ===== 向后兼容函数 =====


async def has_permission(user: User, permission: str) -> bool:
    """权限检查逻辑 - 保持向后兼容"""
    return await permission_manager.check_permission(user, permission)

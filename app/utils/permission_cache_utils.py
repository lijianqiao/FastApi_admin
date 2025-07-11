"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission_cache_utils.py
@DateTime: 2025/07/11
@Docs: 权限缓存失效工具函数
"""

import functools
from collections.abc import Callable
from uuid import UUID

from app.core.permissions.simple_decorators import permission_manager
from app.utils.logger import logger


def invalidate_user_permission_cache(user_id: UUID | str):
    """权限缓存失效装饰器 - 用户权限变更后清除缓存"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            try:
                # 支持从参数中提取user_id
                target_user_id = user_id
                if isinstance(user_id, str) and user_id in kwargs:
                    target_user_id = kwargs[user_id]
                elif hasattr(args, "__len__") and len(args) > 0:
                    # 尝试从第一个参数获取
                    first_arg = args[0]
                    if hasattr(first_arg, "id"):
                        target_user_id = first_arg.id

                if target_user_id:
                    await permission_manager.clear_user_cache(UUID(str(target_user_id)))
                    logger.info(f"用户权限缓存已清除: {target_user_id}")
            except Exception as e:
                logger.error(f"清除用户权限缓存失败: {e}")

            return result

        return wrapper

    return decorator


def invalidate_role_permission_cache(role_id: UUID | str):
    """权限缓存失效装饰器 - 角色权限变更后清除相关缓存"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            try:
                # 支持从参数中提取role_id
                target_role_id = role_id
                if isinstance(role_id, str) and role_id in kwargs:
                    target_role_id = kwargs[role_id]
                elif hasattr(args, "__len__") and len(args) > 0:
                    # 尝试从第一个参数获取
                    first_arg = args[0]
                    if hasattr(first_arg, "id"):
                        target_role_id = first_arg.id

                if target_role_id:
                    await permission_manager.clear_role_cache(UUID(str(target_role_id)))
                    logger.info(f"角色权限缓存已清除: {target_role_id}")
            except Exception as e:
                logger.error(f"清除角色权限缓存失败: {e}")

            return result

        return wrapper

    return decorator


def invalidate_all_permission_cache():
    """权限缓存失效装饰器 - 清除所有权限缓存"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            try:
                await permission_manager.clear_all_cache()
                logger.info("所有权限缓存已清除")
            except Exception as e:
                logger.error(f"清除所有权限缓存失败: {e}")

            return result

        return wrapper

    return decorator


# 便捷函数
async def clear_user_permission_cache(user_id: UUID):
    """清除指定用户的权限缓存"""
    await permission_manager.clear_user_cache(user_id)


async def clear_role_permission_cache(role_id: UUID):
    """清除角色相关的权限缓存"""
    await permission_manager.clear_role_cache(role_id)


async def clear_all_permission_cache():
    """清除所有权限缓存"""
    await permission_manager.clear_all_cache()


async def get_permission_cache_stats():
    """获取权限缓存统计"""
    return await permission_manager.get_cache_stats()

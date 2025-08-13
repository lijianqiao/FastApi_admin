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
from app.dao.user import UserDAO
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


# ============== 基于权限ID的失效（影响所有拥有该权限的用户） ==============


async def clear_permission_affected_users(permission_id: UUID) -> None:
    """清除拥有某权限（直接或经由角色）的用户权限缓存。"""
    user_dao = UserDAO()
    user_ids = await user_dao.get_user_ids_by_permission_deep(permission_id)
    if not user_ids:
        return
    for uid in user_ids:
        try:
            await permission_manager.clear_user_cache(UUID(str(uid)))
        except Exception as e:
            logger.error(f"清除用户权限缓存失败 user={uid}: {e}")


def invalidate_permission_cache(permission_id_param: UUID | str):
    """装饰器：在权限被更新/删除/状态变更后，清除所有受影响用户的权限缓存。

    Args:
        permission_id_param: 可传入实际UUID，或在被装饰函数的kwargs中的参数名（str）
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            try:
                target_permission_id = permission_id_param
                if isinstance(permission_id_param, str) and permission_id_param in kwargs:
                    target_permission_id = kwargs[permission_id_param]
                elif hasattr(args, "__len__") and len(args) > 0:
                    # 尝试从第一个参数（通常是self）后的位置推断，不做复杂解析
                    pass

                if target_permission_id:
                    await clear_permission_affected_users(UUID(str(target_permission_id)))
                    logger.info(f"权限变更导致的用户缓存清除完成: permission={target_permission_id}")
            except Exception as e:
                logger.error(f"清除权限影响的用户缓存失败: {e}")

            return result

        return wrapper

    return decorator

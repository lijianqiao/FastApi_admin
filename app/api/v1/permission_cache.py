"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission_cache.py
@DateTime: 2025/07/11
@Docs: 权限缓存管理API
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import Permissions, require_permission
from app.schemas.base import BaseResponse
from app.utils.deps import OperationContext
from app.utils.permission_cache_utils import (
    clear_all_permission_cache,
    clear_role_permission_cache,
    clear_user_permission_cache,
    get_permission_cache_stats,
)

router = APIRouter(prefix="/permission-cache", tags=["权限缓存管理"])


@router.get("/stats", response_model=BaseResponse[dict], summary="获取权限缓存统计")
async def get_cache_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """获取权限缓存统计信息"""
    stats = await get_permission_cache_stats()
    return BaseResponse(data=stats)


@router.get("/test/{user_id}", response_model=BaseResponse[dict], summary="测试用户权限缓存")
async def test_user_cache(
    user_id: UUID,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """测试用户权限缓存功能 - 包含详细debug信息"""
    from app.core.permissions.simple_decorators import _permission_cache
    from app.utils.logger import logger

    logger.info(f"开始测试用户权限缓存: {user_id}")

    # 第一次获取 - 应该从数据库加载并缓存
    permissions_1 = await _permission_cache.get_user_permissions(user_id)

    # 第二次获取 - 应该从缓存命中
    permissions_2 = await _permission_cache.get_user_permissions(user_id)

    # 获取缓存统计
    stats = await _permission_cache.get_cache_stats()

    test_data = {
        "user_id": user_id,
        "first_fetch": list(permissions_1),
        "second_fetch": list(permissions_2),
        "cache_consistent": permissions_1 == permissions_2,
        "cache_stats": stats,
    }
    return BaseResponse(data=test_data)


@router.delete("/user/{user_id}", response_model=BaseResponse[dict], summary="清除用户权限缓存")
async def clear_user_cache(
    user_id: UUID,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """清除指定用户的权限缓存"""
    await clear_user_permission_cache(user_id)
    return BaseResponse(message=f"用户权限缓存已清除: {user_id}", data={})


@router.delete("/role/{role_id}", response_model=BaseResponse[dict], summary="清除角色权限缓存")
async def clear_role_cache(
    role_id: UUID,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """清除角色相关的权限缓存"""
    await clear_role_permission_cache(role_id)
    return BaseResponse(message=f"角色权限缓存已清除: {role_id}", data={})


@router.delete("/all", response_model=BaseResponse[dict], summary="清除所有权限缓存")
async def clear_all_cache(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """清除所有权限缓存"""
    await clear_all_permission_cache()
    return BaseResponse(message="所有权限缓存已清除", data={})

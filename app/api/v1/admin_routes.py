"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: admin_routes.py
@DateTime: 2025/07/10
@Docs: 管理员专用路由
"""

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.utils.deps import OperationContext

# 创建具有路由器级权限控制的路由器
admin_router = APIRouter(
    prefix="/admin",
    tags=["管理员专用"],
    dependencies=[Depends(require_permission(Permissions.SYSTEM_ADMIN))],  # 路由器级权限控制
)


@admin_router.get("/system-info", response_model=SuccessResponse, summary="获取系统信息")
async def get_system_info(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_CONFIG)),
):
    """获取系统信息 - 需要系统管理员权限和系统配置权限"""
    return SuccessResponse(message="系统信息获取成功")


@admin_router.post("/system-config", response_model=SuccessResponse, summary="更新系统配置")
async def update_system_config(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_CONFIG)),
):
    """更新系统配置 - 需要系统管理员权限和系统配置权限"""
    return SuccessResponse(message="系统配置更新成功")


@admin_router.get("/users-overview", response_model=SuccessResponse, summary="用户概览")
async def get_users_overview(
    # 这个端点只需要路由器级的系统管理员权限，不需要额外的权限
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
):
    """获取用户概览 - 只需要系统管理员权限"""
    return SuccessResponse(message="用户概览获取成功")

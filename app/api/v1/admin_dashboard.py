"""@Author: li.

@Email: lijianqiao2906@live.com
@FileName: admin_dashboard.py
@DateTime: 2025/07/10

@Docs: 后台管理系统仪表板API - 统计数据和系统监控.
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.dashboard import DashboardStats, UserPermissionCheck
from app.schemas.operation_log import OperationLogListRequest
from app.schemas.permission import PermissionListRequest
from app.schemas.role import RoleListRequest
from app.schemas.user import UserListRequest
from app.services.batch_service import BatchService
from app.services.operation_log import OperationLogService
from app.services.permission import PermissionService
from app.services.role import RoleService
from app.services.user import UserService
from app.utils.deps import (
    OperationContext,
    get_operation_log_service,
    get_permission_service,
    get_role_service,
    get_user_service,
)

router = APIRouter(prefix="/admin", tags=["后台管理仪表板"])


# 统计数据端点


@router.get("/dashboard/stats", summary="获取仪表板统计数据")
async def get_dashboard_stats(
    user_service: Annotated[UserService, Depends(get_user_service)],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    operation_log_service: Annotated[OperationLogService, Depends(get_operation_log_service)],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.ADMIN_READ))],
) -> BaseResponse[DashboardStats]:
    """获取后台管理系统的核心统计数据."""
    # 使用现有的 list 方法来获取统计数据

    # 获取各类数据的总数
    users, total_users = await user_service.get_users(UserListRequest(page=1, page_size=1), operation_context)
    roles, total_roles = await role_service.get_roles(RoleListRequest(page=1, page_size=1), operation_context)
    permissions, total_permissions = await permission_service.get_permissions(
        PermissionListRequest(page=1, page_size=1),
        operation_context,
    )
    # 获取今天的操作日志数量
    today = datetime.now(UTC)
    today_logs_request = OperationLogListRequest(page=1, page_size=1, start_date=today, end_date=today)
    today_logs, today_operations = await operation_log_service.get_logs(today_logs_request, operation_context)

    stats = DashboardStats(
        total_users=total_users,
        total_roles=total_roles,
        total_permissions=total_permissions,
        today_operations=today_operations,
    )
    return BaseResponse(data=stats)


# 权限验证端点


@router.post("/permissions/check", summary="检查用户权限")
async def check_user_permission(
    user_id: UUID,
    permission_code: str,
    user_service: Annotated[UserService, Depends(get_user_service)],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.ADMIN_READ))],
) -> BaseResponse[UserPermissionCheck]:
    """检查用户是否拥有指定权限."""
    # 获取用户信息
    user_detail = await user_service.get_user_detail(user_id, operation_context)

    # 检查用户是否拥有权限
    has_permission = False
    permission_source = None

    # 检查直接权限
    user_permissions = await user_service.get_user_permissions(user_id, operation_context)
    for perm in user_permissions:
        if perm.permission_code == permission_code:
            has_permission = True
            permission_source = "direct"
            break

    # 检查角色权限
    if not has_permission:
        user_roles = await user_service.get_user_roles(user_id, operation_context)
        for role in user_roles:
            role_permissions = await role_service.get_role_permissions(role["id"], operation_context)
            for perm in role_permissions:
                if perm["permission_code"] == permission_code:
                    has_permission = True
                    permission_source = f"role:{role['role_name']}"
                    break
            if has_permission:
                break

    permission_check = UserPermissionCheck(
        user_id=user_id,
        username=user_detail.username,
        permission_code=permission_code,
        has_permission=has_permission,
        permission_source=permission_source,
    )
    return BaseResponse(data=permission_check)


@router.get("/permissions/inheritance/{user_id}", summary="获取用户权限继承关系")
async def get_user_permission_inheritance(
    user_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.ADMIN_READ))],
) -> BaseResponse[dict]:
    """获取用户完整的权限继承关系."""
    user_detail = await user_service.get_user_detail(user_id, operation_context)
    direct_permissions = await user_service.get_user_permissions(user_id, operation_context)
    user_roles = await user_service.get_user_roles(user_id, operation_context)

    role_permissions = {}
    for role in user_roles:
        role_perms = await role_service.get_role_permissions(role["id"], operation_context)
        role_permissions[role["role_name"]] = [
            {
                "id": str(perm["id"]),
                "name": perm["permission_name"],
                "code": perm["permission_code"],
                "type": perm["permission_type"],
            }
            for perm in role_perms
        ]

    inheritance_data = {
        "user_id": str(user_id),
        "username": user_detail.username,
        "direct_permissions": [
            {
                "id": str(perm.id),
                "name": perm.permission_name,
                "code": perm.permission_code,
                "description": perm.description,
            }
            for perm in direct_permissions
        ],
        "roles": [
            {
                "id": str(role["id"]),
                "name": role["role_name"],
                "description": role.get("description", ""),
            }
            for role in user_roles
        ],
        "role_permissions": role_permissions,
    }
    return BaseResponse(data=inheritance_data)


# 快速操作端点


@router.post("/quick-actions/batch-enable-users", summary="批量启用用户")
async def batch_enable_users(
    user_ids: list[UUID],
    batch_service: Annotated[BatchService, Depends(lambda: BatchService())],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.USER_UPDATE))],
) -> SuccessResponse:
    """批量启用用户."""
    result_data = await batch_service.batch_update_user_status(
        user_ids,
        is_active=True,
        operation_context=operation_context,
    )

    return SuccessResponse(message=f"成功启用 {result_data['success_count']}/{result_data['total_count']} 个用户")


@router.post("/quick-actions/batch-disable-users", summary="批量禁用用户")
async def batch_disable_users(
    user_ids: list[UUID],
    batch_service: Annotated[BatchService, Depends(lambda: BatchService())],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.USER_UPDATE))],
) -> SuccessResponse:
    """批量禁用用户."""
    result_data = await batch_service.batch_update_user_status(
        user_ids,
        is_active=False,
        operation_context=operation_context,
    )

    return SuccessResponse(message=f"成功禁用 {result_data['success_count']}/{result_data['total_count']} 个用户")


# 数据导出端点


@router.get("/export/users", summary="导出用户数据")
async def export_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.ADMIN_READ))],
) -> BaseResponse[list[dict]]:
    """导出用户数据."""
    # 获取所有用户数据, 使用分页避免内存问题
    all_users = []
    page = 1
    page_size = 100

    while True:
        users, total = await user_service.get_users(UserListRequest(page=page, page_size=page_size), operation_context)
        if not users:
            break

        all_users.extend(
            [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "phone": user.phone,
                    "nickname": user.nickname,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
                for user in users
            ],
        )

        if len(users) < page_size:
            break
        page += 1

    return BaseResponse(data=all_users)


@router.get("/export/roles", summary="导出角色数据")
async def export_roles(
    role_service: Annotated[RoleService, Depends(get_role_service)],
    operation_context: Annotated[OperationContext, Depends(require_permission(Permissions.ADMIN_READ))],
) -> BaseResponse[list[dict]]:
    """导出角色数据."""
    # 获取所有角色
    all_roles = []
    page = 1
    page_size = 100

    while True:
        roles, total = await role_service.get_roles(RoleListRequest(page=page, page_size=page_size), operation_context)
        if not roles:
            break

        all_roles.extend(
            [
                {
                    "id": str(role.id),
                    "role_name": role.role_name,
                    "description": role.description,
                    "is_active": role.is_active,
                    "created_at": role.created_at.isoformat() if role.created_at else None,
                    "updated_at": role.updated_at.isoformat() if role.updated_at else None,
                }
                for role in roles
            ],
        )

        if len(roles) < page_size:
            break
        page += 1

    return BaseResponse(data=all_roles)

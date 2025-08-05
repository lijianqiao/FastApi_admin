"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: admin_dashboard.py
@DateTime: 2025/07/10
@Docs: 后台管理系统仪表板API - 统计数据和系统监控
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.dashboard import DashboardStats, UserPermissionCheck
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


@router.get("/dashboard/stats", response_model=DashboardStats, summary="获取仪表板统计数据")
async def get_dashboard_stats(
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    permission_service: PermissionService = Depends(get_permission_service),
    operation_log_service: OperationLogService = Depends(get_operation_log_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """获取后台管理系统的核心统计数据"""
    # 使用现有的 list 方法来获取统计数据
    from app.schemas.operation_log import OperationLogListRequest
    from app.schemas.permission import PermissionListRequest
    from app.schemas.role import RoleListRequest
    from app.schemas.user import UserListRequest

    # 获取各类数据的总数
    users, total_users = await user_service.get_users(UserListRequest(page=1, page_size=1), operation_context)
    roles, total_roles = await role_service.get_roles(RoleListRequest(page=1, page_size=1), operation_context)
    permissions, total_permissions = await permission_service.get_permissions(
        PermissionListRequest(page=1, page_size=1), operation_context
    )
    # 获取今天的操作日志数量
    today = datetime.now()
    today_logs_request = OperationLogListRequest(page=1, page_size=1, start_date=today, end_date=today)
    today_logs, today_operations = await operation_log_service.get_logs(today_logs_request, operation_context)

    return DashboardStats(
        total_users=total_users,
        total_roles=total_roles,
        total_permissions=total_permissions,
        today_operations=today_operations,
    )


# 权限验证端点


@router.post("/permissions/check", response_model=UserPermissionCheck, summary="检查用户权限")
async def check_user_permission(
    user_id: UUID,
    permission_code: str,
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """检查用户是否拥有指定权限"""
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

    return UserPermissionCheck(
        user_id=user_id,
        username=user_detail.username,
        permission_code=permission_code,
        has_permission=has_permission,
        permission_source=permission_source,
    )


@router.get("/permissions/inheritance/{user_id}", response_model=dict, summary="获取用户权限继承关系")
async def get_user_permission_inheritance(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """获取用户完整的权限继承关系"""
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

    return {
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


# 快速操作端点


@router.post("/quick-actions/batch-enable-users", response_model=SuccessResponse, summary="批量启用用户")
async def batch_enable_users(
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """批量启用用户"""
    success_count = 0
    for user_id in user_ids:
        try:
            user = await user_service.get_by_id(user_id)
            if not user:
                continue
            from app.schemas.user import UserUpdateRequest

            update_request = UserUpdateRequest(is_active=True, version=user.version)
            await user_service.update_user(user_id, update_request, operation_context)
            success_count += 1
        except Exception:
            # 记录错误但继续处理其他用户
            continue

    return SuccessResponse(message=f"成功启用 {success_count}/{len(user_ids)} 个用户")


@router.post("/quick-actions/batch-disable-users", response_model=SuccessResponse, summary="批量禁用用户")
async def batch_disable_users(
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """批量禁用用户"""
    success_count = 0
    for user_id in user_ids:
        try:
            user = await user_service.get_by_id(user_id)
            if not user:
                continue
            from app.schemas.user import UserUpdateRequest

            update_request = UserUpdateRequest(is_active=False, version=user.version)
            await user_service.update_user(user_id, update_request, operation_context)
            success_count += 1
        except Exception:
            # 记录错误但继续处理其他用户
            continue

    return SuccessResponse(message=f"成功禁用 {success_count}/{len(user_ids)} 个用户")


# 数据导出端点


@router.get("/export/users", response_model=list[dict], summary="导出用户数据")
async def export_users(
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """导出用户数据"""
    from app.schemas.user import UserListRequest

    # 获取所有用户（分页获取以避免内存问题）
    all_users = []
    page = 1
    page_size = 100

    while True:
        users, total = await user_service.get_users(UserListRequest(page=page, page_size=page_size), operation_context)
        if not users:
            break

        for user in users:
            all_users.append(
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
            )

        if len(users) < page_size:
            break
        page += 1

    return all_users


@router.get("/export/roles", response_model=list[dict], summary="导出角色数据")
async def export_roles(
    role_service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ADMIN_READ)),
):
    """导出角色数据"""
    from app.schemas.role import RoleListRequest

    # 获取所有角色
    all_roles = []
    page = 1
    page_size = 100

    while True:
        roles, total = await role_service.get_roles(RoleListRequest(page=page, page_size=page_size), operation_context)
        if not roles:
            break

        for role in roles:
            all_roles.append(
                {
                    "id": str(role.id),
                    "role_name": role.role_name,
                    "description": role.description,
                    "is_active": role.is_active,
                    "created_at": role.created_at.isoformat() if role.created_at else None,
                    "updated_at": role.updated_at.isoformat() if role.updated_at else None,
                }
            )

        if len(roles) < page_size:
            break
        page += 1

    return all_roles

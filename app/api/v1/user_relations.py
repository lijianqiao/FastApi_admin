"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user_relations.py
@DateTime: 2025/07/10
@Docs: 用户关系管理专用API端点 - 批量操作和复杂查询
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import SuccessResponse
from app.schemas.dashboard import BatchUserPermissionRequest, BatchUserRoleRequest, UserRolePermissionSummary
from app.schemas.user import UserResponse
from app.services.user import UserService
from app.utils.deps import OperationContext, get_user_service

router = APIRouter(prefix="/user-relations", tags=["用户关系管理"])


# 批量操作端点


@router.post("/batch/users/roles/assign", response_model=SuccessResponse, summary="批量分配用户角色")
async def batch_assign_user_roles(
    request: BatchUserRoleRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """批量为多个用户分配相同的角色"""
    for user_id in request.user_ids:
        await user_service.assign_roles(user_id, request.role_ids, operation_context)
    return SuccessResponse(message=f"成功为 {len(request.user_ids)} 个用户分配角色")


@router.post("/batch/users/roles/add", response_model=SuccessResponse, summary="批量添加用户角色")
async def batch_add_user_roles(
    request: BatchUserRoleRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """批量为多个用户添加相同的角色"""
    for user_id in request.user_ids:
        await user_service.add_user_roles(user_id, request.role_ids, operation_context)
    return SuccessResponse(message=f"成功为 {len(request.user_ids)} 个用户添加角色")


@router.delete("/batch/users/roles/remove", response_model=SuccessResponse, summary="批量移除用户角色")
async def batch_remove_user_roles(
    request: BatchUserRoleRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """批量从多个用户移除相同的角色"""
    for user_id in request.user_ids:
        await user_service.remove_user_roles(user_id, request.role_ids, operation_context)
    return SuccessResponse(message=f"成功从 {len(request.user_ids)} 个用户移除角色")


@router.post("/batch/users/permissions/assign", response_model=SuccessResponse, summary="批量分配用户权限")
async def batch_assign_user_permissions(
    request: BatchUserPermissionRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_PERMISSIONS)),
):
    """批量为多个用户分配相同的权限"""
    for user_id in request.user_ids:
        await user_service.add_user_permissions(user_id, request.permission_ids, operation_context)
    return SuccessResponse(message=f"成功为 {len(request.user_ids)} 个用户分配权限")


# 复杂查询端点（需要在服务层实现对应方法）


@router.get("/roles/{role_id}/users", response_model=list[UserResponse], summary="获取角色下的所有用户")
async def get_users_by_role(
    role_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取拥有指定角色的所有用户"""
    return await user_service.get_users_by_role_id(role_id, operation_context)


@router.get("/permissions/{permission_id}/users", response_model=list[UserResponse], summary="获取权限下的所有用户")
async def get_users_by_permission(
    permission_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取拥有指定权限的所有用户（直接权限或通过角色继承）"""
    return await user_service.get_user_permissions(permission_id, operation_context)


@router.get("/users/{user_id}/summary", response_model=UserRolePermissionSummary, summary="获取用户权限汇总")
async def get_user_permission_summary(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户的完整权限汇总，包括直接权限和通过角色继承的权限"""
    user_detail = await user_service.get_user_detail(user_id, operation_context)
    user_roles = await user_service.get_user_roles(user_id, operation_context)
    user_permissions = await user_service.get_user_permissions(user_id, operation_context)

    return UserRolePermissionSummary(
        user_id=user_detail.id,
        username=user_detail.username,
        roles=user_roles,
        direct_permissions=[
            {"id": p.id, "name": p.permission_name, "code": p.permission_code} for p in user_permissions
        ],
        total_permissions=[
            {"id": p.id, "name": p.permission_name, "code": p.permission_code} for p in user_detail.permissions
        ],
    )


# 角色用户管理端点（需要在服务层实现对应方法）

# @router.get("/roles/{role_id}/users/count", response_model=dict, summary="获取角色用户数量")
# async def get_role_user_count(
#     role_id: UUID,
#     user_service: UserService = Depends(get_user_service),
#     operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
# ):
#     """获取拥有指定角色的用户数量"""
#     count = await user_service.count_users_by_role(role_id, operation_context)
#     return {"role_id": role_id, "user_count": count}


@router.post("/roles/{role_id}/users/assign", response_model=SuccessResponse, summary="为角色批量分配用户")
async def assign_users_to_role(
    role_id: UUID,
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """为指定角色批量分配用户"""
    for user_id in user_ids:
        await user_service.add_user_roles(user_id, [role_id], operation_context)
    return SuccessResponse(message=f"成功为角色分配 {len(user_ids)} 个用户")


@router.delete("/roles/{role_id}/users/remove", response_model=SuccessResponse, summary="从角色批量移除用户")
async def remove_users_from_role(
    role_id: UUID,
    user_ids: list[UUID],
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """从指定角色批量移除用户"""
    for user_id in user_ids:
        await user_service.remove_user_roles(user_id, [role_id], operation_context)
    return SuccessResponse(message=f"成功从角色移除 {len(user_ids)} 个用户")


# 权限继承查询端点

# @router.get("/permissions/inheritance/check", response_model=dict, summary="检查权限继承关系")
# async def check_permission_inheritance(
#     user_id: UUID,
#     permission_code: str,
#     user_service: UserService = Depends(get_user_service),
#     operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
# ):
#     """检查用户是否拥有指定权限以及获取方式（直接权限还是角色继承）"""
#     # 需要在服务层实现更完善的权限检查逻辑
#     pass

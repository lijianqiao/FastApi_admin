"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: users.py
@DateTime: 2025/07/08
@Docs: 用户管理API端点
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.permission import PermissionResponse
from app.schemas.user import (
    UserAssignPermissionsRequest,
    UserAssignRolesRequest,
    UserCreateRequest,
    UserDetailResponse,
    UserListRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user import UserService
from app.utils.deps import OperationContext, get_user_service

router = APIRouter(prefix="/users", tags=["用户管理"])

UserListResponse = PaginatedResponse[UserResponse]


@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def list_users(
    query: UserListRequest = Depends(),
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户列表（分页）"""
    users, total = await user_service.get_users(query, operation_context=operation_context)
    return UserListResponse(data=users, total=total, page=query.page, page_size=query.page_size)


@router.get("/{user_id}", response_model=UserDetailResponse, summary="获取用户详情")
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户详情"""
    return await user_service.get_user_detail(user_id, operation_context=operation_context)


@router.post("", response_model=UserResponse, summary="创建用户", status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_CREATE)),
):
    """创建新用户"""
    return await user_service.create_user(user_data, operation_context=operation_context)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """更新用户信息"""
    return await user_service.update_user(user_id, user_data, operation_context=operation_context)


@router.delete("/{user_id}", response_model=SuccessResponse, summary="删除用户")
async def delete_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_DELETE)),
):
    """删除用户"""
    await user_service.delete_user(user_id, operation_context=operation_context)
    return SuccessResponse()


@router.put("/{user_id}/status", response_model=SuccessResponse, summary="更新用户状态")
async def update_user_status(
    user_id: UUID,
    is_active: bool,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_UPDATE)),
):
    """更新用户状态"""
    await user_service.update_user_status(user_id, is_active, operation_context=operation_context)
    return SuccessResponse()


@router.post("/{user_id}/roles", response_model=UserDetailResponse, summary="分配用户角色")
async def assign_user_roles(
    user_id: UUID,
    role_data: UserAssignRolesRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """分配用户角色（全量设置）"""
    return await user_service.assign_roles(user_id, role_data.role_ids, operation_context=operation_context)


# 用户角色关系管理端点


@router.post("/{user_id}/roles/add", response_model=UserDetailResponse, summary="为用户添加角色")
async def add_user_roles(
    user_id: UUID,
    role_data: UserAssignRolesRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """为用户增量添加角色"""
    return await user_service.add_user_roles(user_id, role_data.role_ids, operation_context=operation_context)


@router.delete("/{user_id}/roles/remove", response_model=UserDetailResponse, summary="移除用户角色")
async def remove_user_roles(
    user_id: UUID,
    role_data: UserAssignRolesRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_ROLES)),
):
    """移除用户的指定角色"""
    return await user_service.remove_user_roles(user_id, role_data.role_ids, operation_context=operation_context)


@router.get("/{user_id}/roles", response_model=list[dict], summary="获取用户角色列表")
async def get_user_roles(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户的角色列表"""
    return await user_service.get_user_roles(user_id, operation_context=operation_context)


# 用户权限关系管理端点


@router.post("/{user_id}/permissions", response_model=UserDetailResponse, summary="设置用户权限")
async def assign_user_permissions(
    user_id: UUID,
    permission_data: UserAssignPermissionsRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_PERMISSIONS)),
):
    """为用户分配直接权限（全量设置）"""
    return await user_service.assign_permissions_to_user(user_id, permission_data, operation_context=operation_context)


@router.post("/{user_id}/permissions/add", response_model=UserDetailResponse, summary="为用户添加权限")
async def add_user_permissions(
    user_id: UUID,
    permission_data: UserAssignPermissionsRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_PERMISSIONS)),
):
    """为用户增量添加权限"""
    return await user_service.add_user_permissions(
        user_id, permission_data.permission_ids, operation_context=operation_context
    )


@router.delete("/{user_id}/permissions/remove", response_model=UserDetailResponse, summary="移除用户权限")
async def remove_user_permissions(
    user_id: UUID,
    permission_data: UserAssignPermissionsRequest,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_ASSIGN_PERMISSIONS)),
):
    """移除用户的指定权限"""
    return await user_service.remove_user_permissions(
        user_id, permission_data.permission_ids, operation_context=operation_context
    )


@router.get("/{user_id}/permissions", response_model=list[PermissionResponse], summary="获取用户权限列表")
async def get_user_permissions(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.USER_READ)),
):
    """获取用户的直接权限列表"""
    return await user_service.get_user_permissions(user_id, operation_context=operation_context)

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: roles.py
@DateTime: 2025/07/08
@Docs: 角色管理API端点 - 使用依赖注入权限控制
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.permissions.simple_decorators import (
    Permissions,
    require_permission,
)
from app.schemas.base import BaseResponse, SuccessResponse
from app.schemas.role import (
    RoleCreateRequest,
    RoleDetailResponse,
    RoleListRequest,
    RoleListResponse,
    RolePermissionAssignRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.role import RoleService
from app.utils.deps import OperationContext, get_role_service

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("", response_model=RoleListResponse, summary="获取角色列表")
async def list_roles(
    query: RoleListRequest = Depends(),
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色列表（分页），支持搜索和筛选"""
    roles, total = await service.get_roles(query, _operation_context=operation_context)
    return RoleListResponse(data=roles, total=total, page=query.page, page_size=query.page_size)


@router.get("/{role_id}", response_model=BaseResponse[RoleDetailResponse], summary="获取角色详情")
async def get_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色详情，包含其所有权限"""
    role_detail = await service.get_role_detail(role_id, _operation_context=operation_context)
    return BaseResponse(data=role_detail)


@router.post("", response_model=BaseResponse[RoleResponse], status_code=status.HTTP_201_CREATED, summary="创建角色")
async def create_role(
    role_data: RoleCreateRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_CREATE)),
):
    """创建新角色"""
    role = await service.create_role(role_data, operation_context=operation_context)
    return BaseResponse(data=role, message="角色创建成功")


@router.put("/{role_id}", response_model=BaseResponse[RoleResponse], summary="更新角色")
async def update_role(
    role_id: UUID,
    role_data: RoleUpdateRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_UPDATE)),
):
    """更新角色信息"""
    role = await service.update_role(role_id, role_data, operation_context=operation_context)
    return BaseResponse(data=role, message="角色更新成功")


@router.delete("/{role_id}", response_model=SuccessResponse, summary="删除角色")
async def delete_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_DELETE)),
):
    """删除角色"""
    await service.delete_role(role_id, operation_context=operation_context)
    return SuccessResponse()


@router.put("/{role_id}/status", response_model=SuccessResponse, summary="更新角色状态")
async def update_role_status(
    role_id: UUID,
    is_active: bool,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_UPDATE)),
):
    """更新角色状态"""
    await service.update_role_status(role_id, is_active=is_active, operation_context=operation_context)
    return SuccessResponse()


@router.post("/{role_id}/permissions", response_model=BaseResponse[RoleDetailResponse], summary="分配角色权限")
async def assign_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """分配角色权限（全量设置）"""
    role_detail = await service.assign_permissions_to_role(
        role_id, permission_data, operation_context=operation_context
    )
    return BaseResponse(data=role_detail, message="角色权限分配成功")


# 角色权限关系管理端点


@router.post("/{role_id}/permissions/add", response_model=BaseResponse[RoleDetailResponse], summary="为角色添加权限")
async def add_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """为角色增量添加权限"""
    role_detail = await service.add_role_permissions(
        role_id, permission_data.permission_ids, operation_context=operation_context
    )
    return BaseResponse(data=role_detail, message="角色权限添加成功")


@router.delete("/{role_id}/permissions/remove", response_model=BaseResponse[RoleDetailResponse], summary="移除角色权限")
async def remove_role_permissions(
    role_id: UUID,
    permission_data: RolePermissionAssignRequest,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_ASSIGN_PERMISSIONS)),
):
    """移除角色的指定权限"""
    role_detail = await service.remove_role_permissions(
        role_id, permission_data.permission_ids, operation_context=operation_context
    )
    return BaseResponse(data=role_detail, message="角色权限移除成功")


@router.get("/{role_id}/permissions", response_model=BaseResponse[list[dict]], summary="获取角色权限列表")
async def get_role_permissions(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    operation_context: OperationContext = Depends(require_permission(Permissions.ROLE_READ)),
):
    """获取角色的权限列表"""
    permissions = await service.get_role_permissions(role_id, _operation_context=operation_context)
    return BaseResponse(data=permissions)

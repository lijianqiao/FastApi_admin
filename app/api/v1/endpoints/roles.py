"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: roles.py
@DateTime: 2025/06/05
@Docs: 角色相关API端点
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    BatchOperationResponse,
    RoleCreate,
    RoleQuery,
    RoleResponse,
    RoleUpdate,
    RoleWithPermission,
    RoleWithUsers,
    UserRoleAssignRequest,
)
from app.services.services import ServiceFactory, get_service_factory

router = APIRouter(prefix="/roles", tags=["角色"])


@router.post("/", response_model=RoleResponse, summary="创建角色", description="创建新角色")
async def create_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_data: RoleCreate,
) -> RoleResponse:
    """
    创建新角色

    - **role_data**: 角色创建数据
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.create_role(role_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", summary="角色列表", description="分页获取角色列表")
async def list_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    keyword: str = Query(None, description="搜索关键字"),
    is_active: bool | None = Query(None, description="是否激活"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_desc: bool = Query(True, description="降序排序"),
) -> dict:
    """
    分页获取角色列表

    - **keyword**: 搜索关键字
    - **is_active**: 是否激活
    - **page**: 页码
    - **size**: 每页数量
    - **sort_by**: 排序字段
    - **sort_desc**: 是否降序排序
    """
    try:
        role_service = service_factory.get_role_service()
        query = RoleQuery(
            keyword=keyword,
            is_active=is_active,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            include_deleted=False,
        )
        roles, total = await role_service.list_roles(query)
        return {"data": roles, "total": total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{role_id}", response_model=RoleResponse, summary="角色详情", description="根据ID获取角色信息")
async def get_role_by_id(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
) -> RoleResponse:
    """
    根据ID获取角色信息

    - **role_id**: 角色ID
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.get_role_by_id(role_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{role_id}", response_model=RoleResponse, summary="更新角色", description="更新角色信息")
async def update_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
    role_data: RoleUpdate,
) -> RoleResponse:
    """
    更新角色信息

    - **role_id**: 角色ID
    - **role_data**: 角色更新数据
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.update_role(role_id, role_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{role_id}", response_model=RoleResponse, summary="删除角色", description="删除角色")
async def delete_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
    hard_delete: bool = Query(False, description="是否硬删除"),
) -> RoleResponse:
    """
    删除角色

    - **role_id**: 角色ID
    - **hard_delete**: 是否硬删除
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.delete_role(role_id, hard_delete)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{role_id}/assign-users", response_model=RoleWithUsers, summary="为角色分配用户", description="为角色分配用户"
)
async def assign_users_to_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
    user_ids: list[UUID],
) -> RoleWithUsers:
    """
    为角色分配用户

    - **role_id**: 角色ID
    - **user_ids**: 用户ID列表
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.assign_users_to_role(role_id, user_ids)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{role_id}/remove-users", response_model=RoleWithUsers, summary="从角色移除用户", description="从角色移除用户"
)
async def remove_users_from_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
    user_ids: list[UUID],
) -> RoleWithUsers:
    """
    从角色移除用户

    - **role_id**: 角色ID
    - **user_ids**: 用户ID列表
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.remove_users_from_role(role_id, user_ids)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{role_id}/users", response_model=RoleWithUsers, summary="获取角色及用户", description="获取角色及其关联的用户信息"
)
async def get_role_with_users(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
) -> RoleWithUsers:
    """
    获取角色及其关联的用户信息

    - **role_id**: 角色ID
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.get_role_with_users(role_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{role_id}/permissions",
    response_model=RoleWithPermission,
    summary="获取角色及权限",
    description="获取角色及其关联的权限信息",
)
async def get_role_with_permissions(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
) -> RoleWithPermission:
    """
    获取角色及其关联的权限信息

    - **role_id**: 角色ID
    """
    try:
        role_service = service_factory.get_role_service()
        return await role_service.get_role_with_permissions(role_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/assign-user-roles",
    response_model=BatchOperationResponse,
    summary="批量分配用户角色",
    description="批量分配用户角色",
)
async def assign_user_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    assign_request: UserRoleAssignRequest,
) -> BatchOperationResponse:
    """
    批量分配用户角色

    - **assign_request**: 用户角色分配请求
    """
    try:
        role_service = service_factory.get_role_service()
        await role_service.assign_user_roles(assign_request)
        return BatchOperationResponse(success_count=1, failed_count=0, total_count=1, failed_ids=[])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

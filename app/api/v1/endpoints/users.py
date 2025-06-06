"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: users.py
@DateTime: 2025/06/05
@Docs: 用户相关API端点
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    BatchDeleteRequest,
    BatchOperationResponse,
    BatchUpdateRequest,
    UserCreate,
    UserQuery,
    UserResponse,
    UserUpdate,
    UserWithRoles,
)
from app.services.services import ServiceFactory, get_service_factory

router = APIRouter(prefix="/users", tags=["用户"])


@router.post("/", response_model=UserResponse, summary="创建用户", description="创建新用户")
async def create_user(
    _: Annotated[User, Depends(get_current_user)],
    user_data: UserCreate,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserResponse:
    """
    创建新用户

    - **user_data**: 用户数据
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", summary="用户列表", description="分页获取用户列表")
async def list_users(
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
    分页获取用户列表

    - **keyword**: 搜索关键字
    - **is_active**: 是否激活
    - **page**: 页码
    - **size**: 每页数量
    - **sort_by**: 排序字段
    - **sort_desc**: 是否降序排序
    """
    try:
        user_service = service_factory.get_user_service()
        query = UserQuery(
            keyword=keyword,
            is_active=is_active,
            is_superuser=None,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            include_deleted=False,
        )
        users, total = await user_service.search_users(query)
        return {"data": users, "total": total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/active", summary="活跃用户列表", description="获取活跃用户列表")
async def get_active_users(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_desc: bool = Query(True, description="降序排序"),
) -> dict:
    """
    获取活跃用户列表

    - **page**: 页码
    - **size**: 每页数量
    - **sort_by**: 排序字段
    - **sort_desc**: 是否降序排序
    """
    try:
        user_service = service_factory.get_user_service()
        query = UserQuery(
            keyword=None,
            is_active=True,
            is_superuser=None,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            include_deleted=False,
        )
        users, total = await user_service.get_active_users(query)
        return {"data": users, "total": total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{user_id}", response_model=UserResponse, summary="用户详情", description="根据ID获取用户信息")
async def get_user_by_id(
    _: Annotated[User, Depends(get_current_user)],
    user_id: UUID,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserResponse:
    """
    根据ID获取用户信息

    - **user_id**: 用户ID
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.get_user_by_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/by-username/{username}",
    response_model=UserResponse,
    summary="根据用户名获取用户",
    description="根据用户名获取用户信息",
)
async def get_user_by_username(
    _: Annotated[User, Depends(get_current_user)],
    username: str,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserResponse:
    """
    根据用户名获取用户信息

    - **username**: 用户名
    """
    try:
        user_service = service_factory.get_user_service()
        user = await user_service.get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/by-email/{email}", response_model=UserResponse, summary="根据邮箱获取用户", description="根据邮箱获取用户信息"
)
async def get_user_by_email(
    _: Annotated[User, Depends(get_current_user)],
    email: str,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserResponse:
    """
    根据邮箱获取用户信息

    - **email**: 邮箱地址
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.get_user_by_email(email)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户", description="更新用户信息")
async def update_user(
    _: Annotated[User, Depends(get_current_user)],
    user_id: UUID,
    user_data: UserUpdate,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserResponse:
    """
    更新用户信息

    - **user_id**: 用户ID
    - **user_data**: 用户数据
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.update_user(user_id, user_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{user_id}", summary="删除用户", description="删除用户")
async def delete_user(
    _: Annotated[User, Depends(get_current_user)],
    user_id: UUID,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    hard_delete: bool = Query(False, description="是否硬删除"),
) -> dict:
    """
    删除用户

    - **user_id**: 用户ID
    - **hard_delete**: 是否硬删除
    """
    try:
        user_service = service_factory.get_user_service()
        success = await user_service.delete_user(user_id, hard_delete)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/batch-delete", summary="批量删除用户", description="批量删除用户")
async def batch_delete_users(
    _: Annotated[User, Depends(get_current_user)],
    request: BatchDeleteRequest,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> BatchOperationResponse:
    """
    批量删除用户

    - **request**: 批量删除请求
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.batch_delete_users(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/batch-update-status", summary="批量更新用户状态", description="批量更新用户状态")
async def batch_update_user_status(
    _: Annotated[User, Depends(get_current_user)],
    request: BatchUpdateRequest,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> BatchOperationResponse:
    """
    批量更新用户状态

    - **request**: 批量更新状态请求
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.batch_update_user_status(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/check-username/{username}", summary="检查用户名可用", description="检查用户名是否可用")
async def check_username(
    _: Annotated[User, Depends(get_current_user)],
    username: str,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> dict:
    """
    检查用户名是否可用

    - **username**: 用户名
    """
    try:
        user_service = service_factory.get_user_service()
        available = await user_service.check_username_available(username)
        return {"available": available}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/check-email/{email}", summary="检查邮箱可用", description="检查邮箱是否可用")
async def check_email(
    _: Annotated[User, Depends(get_current_user)],
    email: str,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> dict:
    """
    检查邮箱是否可用

    - **email**: 邮箱地址
    """
    try:
        user_service = service_factory.get_user_service()
        available = await user_service.check_email_available(email)
        return {"available": available}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{user_id}/roles", summary="获取用户所有角色", description="获取用户的所有角色信息")
async def get_user_roles(
    _: Annotated[User, Depends(get_current_user)],
    user_id: UUID,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> dict:
    """
    获取用户的所有角色信息

    - **user_id**: 用户ID
    """
    try:
        user_service = service_factory.get_user_service()
        roles = await user_service.get_user_roles(user_id)
        return {"data": roles}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{user_id}/with-roles", response_model=UserWithRoles, summary="获取用户及角色", description="获取用户信息及其角色"
)
async def get_user_with_roles(
    _: Annotated[User, Depends(get_current_user)],
    user_id: UUID,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserWithRoles:
    """
    获取用户信息及其角色

    - **user_id**: 用户ID
    """
    try:
        user_service = service_factory.get_user_service()
        return await user_service.get_user_with_roles(user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

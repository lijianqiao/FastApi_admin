"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permissions.py
@DateTime: 2025/06/05
@Docs: 权限相关API端点
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    BatchOperationResponse,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    PermissionWithRoles,
)
from app.services.services import ServiceFactory, get_service_factory

router = APIRouter(prefix="/permissions", tags=["权限"])


@router.post("/", response_model=PermissionResponse, summary="创建权限", description="创建新权限")
async def create_permission(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_data: PermissionCreate,
) -> PermissionResponse:
    """
    创建新权限

    - **权限名称**: 权限的名称
    - **权限描述**: 对权限的详细描述
    - **资源类型**: 权限所针对的资源类型
    - **操作类型**: 权限允许的操作类型
    - **权限代码**: 权限的唯一标识符
    - **是否启用**: 权限是否处于启用状态
    - **父级权限**: 权限的上级权限ID
    - **排序**: 权限在同级权限中的排序值
    - **备注**: 其他备注信息
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.create_permission(permission_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", summary="权限列表", description="分页获取权限列表")
async def list_permissions(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    resource: str | None = Query(None, description="资源类型"),
    action: str | None = Query(None, description="操作类型"),
    keyword: str | None = Query(None, description="搜索关键字"),
    include_deleted: bool = Query(False, description="是否包含已删除"),
) -> dict:
    """
    分页获取权限列表

    - **跳过数量**: 用于分页的跳过记录数
    - **每页数量**: 每页显示的权限数量
    - **资源类型**: 可选，按资源类型过滤权限
    - **操作类型**: 可选，按操作类型过滤权限
    - **搜索关键字**: 可选，按关键字搜索权限
    - **是否包含已删除**: 是否在列表中包含已删除的权限
    """
    try:
        permission_service = service_factory.get_permission_service()
        result = await permission_service.list_permissions(
            skip=skip, limit=limit, resource=resource, action=action, keyword=keyword, include_deleted=include_deleted
        )
        if hasattr(result, "model_dump"):
            return result.model_dump()
        elif hasattr(result, "dict"):
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected response type")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{permission_id}", response_model=PermissionResponse, summary="权限详情", description="根据ID获取权限信息")
async def get_permission_by_id(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
) -> PermissionResponse:
    """
    根据ID获取权限信息

    - **权限ID**: 要查询的权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.get_permission_by_id(permission_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{permission_id}", response_model=PermissionResponse, summary="更新权限", description="更新权限信息")
async def update_permission(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
    permission_data: PermissionUpdate,
) -> PermissionResponse:
    """
    更新权限信息

    - **权限ID**: 要更新的权限的唯一标识符
    - **权限名称**: 权限的名称
    - **权限描述**: 对权限的详细描述
    - **资源类型**: 权限所针对的资源类型
    - **操作类型**: 权限允许的操作类型
    - **权限代码**: 权限的唯一标识符
    - **是否启用**: 权限是否处于启用状态
    - **父级权限**: 权限的上级权限ID
    - **排序**: 权限在同级权限中的排序值
    - **备注**: 其他备注信息
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.update_permission(permission_id, permission_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{permission_id}", response_model=PermissionResponse, summary="删除权限", description="删除权限")
async def delete_permission(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
    hard_delete: bool = Query(False, description="是否硬删除"),
) -> PermissionResponse:
    """
    删除权限

    - **权限ID**: 要删除的权限的唯一标识符
    - **是否硬删除**: 是否执行硬删除（彻底删除，不可恢复）
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.delete_permission(permission_id, hard_delete)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/by-code/{code}",
    response_model=PermissionResponse,
    summary="根据权限代码获取权限",
    description="根据权限代码获取权限信息",
)
async def get_permission_by_code(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    code: str,
) -> PermissionResponse:
    """
    根据权限代码获取权限信息

    - **权限代码**: 权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.get_permission_by_code(code)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/by-resource-action",
    response_model=PermissionResponse,
    summary="根据资源和操作获取权限",
    description="根据资源和操作获取权限信息",
)
async def get_permission_by_resource_action(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    resource: str,
    action: str,
) -> PermissionResponse:
    """
    根据资源和操作获取权限信息

    - **资源类型**: 权限所针对的资源类型
    - **操作类型**: 权限允许的操作类型
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.get_permission_by_resource_and_action(resource, action)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/exists/{permission_id}", summary="检查权限是否存在", description="检查权限是否存在")
async def check_permission_exists(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
) -> dict:
    """
    检查权限是否存在

    - **权限ID**: 要检查的权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        exists = await permission_service.check_permission_exists(permission_id)
        return {"exists": exists}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/code-exists/{code}", summary="检查权限代码是否存在", description="检查权限代码是否存在")
async def check_permission_code_exists(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    code: str,
    exclude_id: UUID | None = Query(None, description="排除的权限ID"),
) -> dict:
    """
    检查权限代码是否存在

    - **权限代码**: 要检查的权限代码
    - **排除的权限ID**: 可选，排除的权限ID（用于更新时检查）
    """
    try:
        permission_service = service_factory.get_permission_service()
        exists = await permission_service.check_permission_code_exists(code, exclude_id)
        return {"exists": exists}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/validate-ids", summary="验证权限ID列表有效性", description="验证权限ID列表的有效性")
async def validate_permissions(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_ids: list[UUID],
) -> dict:
    """
    验证权限ID列表的有效性

    - **权限ID列表**: 要验证的权限ID列表
    """
    try:
        permission_service = service_factory.get_permission_service()
        valid = await permission_service.validate_permissions(permission_ids)
        return {"valid": valid}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/batch-update-status",
    response_model=BatchOperationResponse,
    summary="批量更新权限状态",
    description="批量更新权限状态",
)
async def batch_update_permission_status(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_ids: list[UUID],
    is_active: bool,
) -> BatchOperationResponse:
    """
    批量更新权限状态

    - **权限ID列表**: 要更新的权限ID列表
    - **是否启用**: 权限的新状态
    """
    try:
        permission_service = service_factory.get_permission_service()
        updated = await permission_service.batch_update_permission_status(permission_ids, is_active)
        return BatchOperationResponse(
            success_count=len(updated), failed_count=0, total_count=len(permission_ids), failed_ids=[]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/batch-delete", response_model=BatchOperationResponse, summary="批量删除权限", description="批量删除权限")
async def batch_delete_permissions(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_ids: list[UUID],
    hard_delete: bool = False,
) -> BatchOperationResponse:
    """
    批量删除权限

    - **权限ID列表**: 要删除的权限ID列表
    - **是否硬删除**: 是否对每个权限执行硬删除
    """
    try:
        permission_service = service_factory.get_permission_service()
        deleted = await permission_service.batch_delete_permissions(permission_ids, hard_delete=hard_delete)
        return BatchOperationResponse(
            success_count=len(deleted), failed_count=0, total_count=len(permission_ids), failed_ids=[]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/by-codes", summary="根据权限代码列表获取权限", description="根据权限代码列表获取权限")
async def get_permissions_by_codes(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    codes: list[str],
) -> dict:
    """
    根据权限代码列表获取权限

    - **权限代码列表**: 要查询的权限代码列表
    """
    try:
        permission_service = service_factory.get_permission_service()
        permissions = await permission_service.get_permissions_by_codes(codes)
        return {"data": permissions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{permission_id}/roles",
    response_model=PermissionWithRoles,
    summary="获取权限及角色",
    description="获取权限及其关联的角色信息",
)
async def get_permission_with_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
) -> PermissionWithRoles:
    """
    获取权限及其关联的角色信息

    - **权限ID**: 要查询的权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.get_permission_with_roles(permission_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{permission_id}/assign-roles",
    response_model=PermissionWithRoles,
    summary="给角色赋予权限",
    description="给角色赋予权限",
)
async def assign_permission_to_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
    role_ids: list[UUID],
) -> PermissionWithRoles:
    """
    给角色赋予权限

    - **权限ID**: 要赋予权限的权限的唯一标识符
    - **角色ID列表**: 要赋予权限的角色ID列表
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.assign_permission_to_roles(permission_id, role_ids)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{permission_id}/remove-roles",
    response_model=PermissionWithRoles,
    summary="移除角色权限",
    description="移除角色权限",
)
async def remove_permission_from_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
    role_ids: list[UUID],
) -> PermissionWithRoles:
    """
    移除角色权限

    - **权限ID**: 要移除权限的权限的唯一标识符
    - **角色ID列表**: 要移除权限的角色ID列表
    """
    try:
        permission_service = service_factory.get_permission_service()
        return await permission_service.remove_permission_from_roles(permission_id, role_ids)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/by-role/{role_id}", summary="获取角色的权限列表", description="获取角色的权限列表")
async def get_permissions_by_role(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
) -> dict:
    """
    获取角色的权限列表

    - **角色ID**: 要查询的角色的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        permissions = await permission_service.get_permissions_by_role(role_id)
        return {"data": permissions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/role-has-permission", summary="检查角色是否具有某个权限", description="检查角色是否具有某个权限")
async def check_role_has_permission(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    role_id: UUID,
    permission_id: UUID,
) -> dict:
    """
    检查角色是否具有某个权限

    - **角色ID**: 要检查的角色的唯一标识符
    - **权限ID**: 要检查的权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        has_permission = await permission_service.check_role_has_permission(role_id, permission_id)
        return {"has_permission": has_permission}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/batch-assign-permissions", summary="批量分配权限给角色", description="批量分配权限给角色")
async def batch_assign_permissions_to_roles(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_role_mapping: dict,
) -> dict:
    """
    批量分配权限给角色

    - **权限与角色的映射关系**: 包含权限ID和角色ID列表的字典
    """
    try:
        permission_service = service_factory.get_permission_service()
        updated = await permission_service.batch_assign_permissions_to_roles(permission_role_mapping)
        return {"data": updated}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{permission_id}/role-ids", summary="获取拥有指定权限的角色ID列表", description="获取拥有指定权限的角色ID列表"
)
async def get_roles_by_permission(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    permission_id: UUID,
) -> dict:
    """
    获取拥有指定权限的角色ID列表

    - **权限ID**: 要查询的权限的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        role_ids = await permission_service.get_roles_by_permission(permission_id)
        return {"role_ids": role_ids}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/user-permissions/{user_id}", summary="获取用户的所有权限", description="获取用户的所有权限（通过角色）")
async def get_user_permissions(
    _: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    user_id: UUID,
) -> dict:
    """
    获取用户的所有权限（通过角色）

    - **用户ID**: 要查询的用户的唯一标识符
    """
    try:
        permission_service = service_factory.get_permission_service()
        permissions = await permission_service.get_user_permissions(user_id)
        return {"data": permissions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

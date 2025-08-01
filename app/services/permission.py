"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/07/08
@Docs: 权限服务层 - 专注业务逻辑
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.models.permission import Permission
from app.schemas.permission import (
    PermissionCreateRequest,
    PermissionListRequest,
    PermissionResponse,
    PermissionUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)


class PermissionService(BaseService[Permission]):
    """权限服务"""

    def __init__(self):
        super().__init__(PermissionDAO())
        self.role_dao = RoleDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查权限编码唯一性"""
        if "permission_code" in data and await self.dao.exists(permission_code=data["permission_code"]):
            raise BusinessException("权限编码已存在")
        return data

    async def before_update(self, obj: Permission, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查权限编码唯一性"""
        if "permission_code" in data and await self.dao.exists(permission_code=data["permission_code"], id__not=obj.id):
            raise BusinessException("权限编码已存在")
        return data

    @log_create_with_context("permission")
    async def create_permission(
        self, request: PermissionCreateRequest, operation_context: OperationContext
    ) -> PermissionResponse:
        """创建权限"""
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        permission = await self.create(operation_context=operation_context, **create_data)
        if not permission:
            raise BusinessException("权限创建失败")
        return PermissionResponse.model_validate(permission)

    @log_update_with_context("permission")
    async def update_permission(
        self, permission_id: UUID, request: PermissionUpdateRequest, operation_context: OperationContext
    ) -> PermissionResponse:
        """更新权限"""
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_permission = await self.update(
            permission_id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_permission:
            raise BusinessException("权限更新失败或版本冲突")
        return PermissionResponse.model_validate(updated_permission)

    @log_delete_with_context("permission")
    async def delete_permission(self, permission_id: UUID, operation_context: OperationContext) -> None:
        """删除权限，先检查是否被角色使用"""
        role_count = await self.role_dao.count(permissions__id=permission_id)
        if role_count > 0:
            raise BusinessException(f"该权限正在被 {role_count} 个角色使用，无法删除")
        await self.delete(permission_id, operation_context=operation_context)

    @log_query_with_context("permission")
    async def get_permissions(
        self, query: PermissionListRequest, operation_context: OperationContext
    ) -> tuple[list[PermissionResponse], int]:
        """获取权限列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        PERMISSION_MODEL_FIELDS = {"permission_type", "is_active"}
        search_fields = ["permission_name", "permission_code", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, PERMISSION_MODEL_FIELDS)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        permissions, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )

        if not permissions:
            return [], 0
        result = [PermissionResponse.model_validate(p) for p in permissions]
        return result, total

    @log_query_with_context("permission")
    async def get_all_permissions(self, operation_context: OperationContext) -> list[PermissionResponse]:
        """获取所有权限（通常用于前端权限树）"""
        permissions = await self.dao.get_all(order_by=["permission_type", "created_at"])
        return [PermissionResponse.model_validate(p) for p in permissions]

    @log_query_with_context("permission")
    async def get_permission_detail(
        self, permission_id: UUID, operation_context: OperationContext
    ) -> PermissionResponse:
        """根据ID获取权限详情"""
        permission = await self.dao.get_by_id(permission_id, include_deleted=False)
        if not permission:
            raise BusinessException("权限未找到")
        return PermissionResponse.model_validate(permission)

    async def update_permission_status(
        self, permission_id: UUID, is_active: bool, operation_context: OperationContext
    ) -> None:
        """更新权限状态"""
        await self.update(permission_id, is_active=is_active, operation_context=operation_context)

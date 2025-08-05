"""@Author: li.

@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/07/08
@Docs: 角色服务层 - 使用操作上下文依赖注入.
"""

from typing import Any
from uuid import UUID

from app.core.exceptions import BusinessException
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.models.role import Role
from app.schemas.role import (
    RoleCreateRequest,
    RoleDetailResponse,
    RoleListRequest,
    RolePermissionAssignRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)
from app.utils.permission_cache_utils import invalidate_role_permission_cache
from app.utils.query_utils import list_query_to_orm_filters


class RoleService(BaseService[Role]):
    """角色服务."""

    def __init__(self) -> None:
        """初始化角色服务."""
        self.dao = RoleDAO()
        super().__init__(self.dao)
        self.permission_dao = PermissionDAO()
        self.user_dao = UserDAO()

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子: 检查角色名称和编码唯一性.

        Args:
            data: 创建数据

        Returns:
            dict[str, Any]: 验证后的创建数据

        Raises:
            BusinessException: 当角色编码或名称已存在时

        """
        if "role_code" in data and await self.dao.exists(role_code=data["role_code"]):
            msg = "角色编码已存在"
            raise BusinessException(msg)
        if "role_name" in data and await self.dao.exists(role_name=data["role_name"]):
            msg = "角色名称已存在"
            raise BusinessException(msg)
        return data

    async def before_update(self, obj: Role, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子: 检查角色名称和编码唯一性.

        Args:
            obj: 角色对象
            data: 更新数据

        Returns:
            dict[str, Any]: 验证后的更新数据

        Raises:
            BusinessException: 当角色编码或名称已存在时

        """
        if "role_code" in data and await self.dao.exists(role_code=data["role_code"], id__not=obj.id):
            msg = "角色编码已存在"
            raise BusinessException(msg)
        if "role_name" in data and await self.dao.exists(role_name=data["role_name"], id__not=obj.id):
            msg = "角色名称已存在"
            raise BusinessException(msg)
        return data

    @log_create_with_context("role")
    async def create_role(self, request: RoleCreateRequest, operation_context: OperationContext) -> RoleResponse:
        """创建角色.

        Args:
            request: 角色创建请求
            operation_context: 操作上下文

        Returns:
            RoleResponse: 创建的角色信息

        Raises:
            BusinessException: 当角色创建失败时

        """
        create_data = request.model_dump(exclude_unset=True)
        create_data["creator_id"] = operation_context.user.id
        role = await self.create(operation_context=operation_context, **create_data)
        if not role:
            msg = "角色创建失败"
            raise BusinessException(msg)
        return RoleResponse.model_validate(role)

    @log_update_with_context("role")
    async def update_role(
        self, role_id: UUID, request: RoleUpdateRequest, operation_context: OperationContext,
    ) -> RoleResponse:
        """更新角色.

        Args:
            role_id: 角色ID
            request: 角色更新请求
            operation_context: 操作上下文

        Returns:
            RoleResponse: 更新后的角色信息

        Raises:
            BusinessException: 当更新失败或版本冲突时

        """
        update_data = request.model_dump(exclude_unset=True)

        version = update_data.pop("version", None)
        if version is None:
            msg = "更新请求必须包含 version 字段。"
            raise BusinessException(msg)

        updated_role = await self.update(role_id, operation_context=operation_context, version=version, **update_data)
        if not updated_role:
            msg = "角色更新失败或版本冲突"
            raise BusinessException(msg)
        return RoleResponse.model_validate(updated_role)

    @log_delete_with_context("role")
    async def delete_role(self, role_id: UUID, operation_context: OperationContext) -> None:
        """删除角色, 检查是否仍有用户关联.

        Args:
            role_id: 角色ID
            operation_context: 操作上下文

        Raises:
            BusinessException: 当角色未找到或仍有用户关联时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)
        # 检查是否有用户正在使用此角色
        user_count = await self.user_dao.count(roles__id=role_id)
        if user_count > 0:
            msg = f"角色 '{role.role_name}' 正在被 {user_count} 个用户使用, 无法删除"
            raise BusinessException(msg)
        await self.delete(role_id, operation_context=operation_context)

    @log_query_with_context("role")
    async def get_roles(
        self, query: RoleListRequest, _operation_context: OperationContext,
    ) -> tuple[list[RoleResponse], int]:
        """获取角色列表.

        Args:
            query: 角色列表查询请求
            operation_context: 操作上下文

        Returns:
            tuple[list[RoleResponse], int]: 角色列表和总数

        """
        query_dict = query.model_dump(exclude_unset=True)

        role_model_fields = {"role_code", "is_active"}
        search_fields = ["role_name", "description"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, role_model_fields)

        order_by = [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

        q_objects = model_filters.pop("q_objects", [])

        roles, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )
        return [RoleResponse.model_validate(role) for role in roles], total

    @log_query_with_context("role")
    async def get_role_detail(self, role_id: UUID, _operation_context: OperationContext) -> RoleDetailResponse:
        """获取带权限的角色详情.

        Args:
            role_id: 角色ID
            operation_context: 操作上下文

        Returns:
            RoleDetailResponse: 角色详情信息

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_with_related(role_id, prefetch_related=["permissions"], include_deleted=False)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)
        return RoleDetailResponse.model_validate(role)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def assign_permissions_to_role(
        self, role_id: UUID, request: RolePermissionAssignRequest, operation_context: OperationContext,
    ) -> RoleDetailResponse:
        """为角色分配权限(全量设置).

        Args:
            role_id: 角色ID
            request: 角色权限分配请求
            operation_context: 操作上下文

        Returns:
            RoleDetailResponse: 更新后的角色详情

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)

        # 使用 DAO 层的全量设置方法
        await self.dao.set_permissions(role_id, request.permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def add_role_permissions(
        self, role_id: UUID, permission_ids: list[UUID], operation_context: OperationContext,
    ) -> RoleDetailResponse:
        """为角色增量添加权限.

        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表
            operation_context: 操作上下文

        Returns:
            RoleDetailResponse: 更新后的角色详情

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)

        await self.dao.add_permissions(role_id, permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    @log_update_with_context("role")
    @invalidate_role_permission_cache("role_id")
    async def remove_role_permissions(
        self, role_id: UUID, permission_ids: list[UUID], operation_context: OperationContext,
    ) -> RoleDetailResponse:
        """移除角色的指定权限.

        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表
            operation_context: 操作上下文

        Returns:
            RoleDetailResponse: 更新后的角色详情

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)

        await self.dao.remove_permissions(role_id, permission_ids)
        return await self.get_role_detail(role_id, operation_context)

    async def get_role_permissions(self, role_id: UUID, _operation_context: OperationContext) -> list[dict]:
        """获取角色的权限列表.

        Args:
            role_id: 角色ID
            operation_context: 操作上下文

        Returns:
            list[dict]: 角色权限列表

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)

        permissions = await self.dao.get_role_permissions(role_id)
        return [
            {
                "id": perm.id,
                "permission_name": perm.permission_name,
                "permission_code": perm.permission_code,
                "permission_type": perm.permission_type,
            }
            for perm in permissions
        ]

    @log_query_with_context("role")
    async def get_role_by_code(self, role_code: str, _operation_context: OperationContext) -> RoleResponse:
        """根据编码获取角色.

        Args:
            role_code: 角色编码
            operation_context: 操作上下文

        Returns:
            RoleResponse: 角色信息

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.get_one(role_code=role_code)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)
        return RoleResponse.model_validate(role)

    @log_update_with_context("role")
    async def update_role_status(self, role_id: UUID, *, is_active: bool, operation_context: OperationContext) -> None:
        """更新角色状态.

        Args:
            role_id: 角色ID
            is_active: 激活状态
            operation_context: 操作上下文

        Raises:
            BusinessException: 当角色未找到时

        """
        role = await self.dao.get_by_id(role_id)
        if not role:
            msg = "角色未找到"
            raise BusinessException(msg)
        await self.update(role_id, operation_context=operation_context, version=role.version, is_active=is_active)

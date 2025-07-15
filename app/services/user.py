"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/01/01
@Docs: 用户服务层 - 集成 Pydantic schemas 进行数据校验和序列化
"""

from typing import Any
from uuid import UUID

from tortoise.exceptions import NoValuesFetched

from app.core.exceptions import BusinessException
from app.core.security import hash_password, verify_password
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import PermissionResponse
from app.schemas.user import (
    UserAssignPermissionsRequest,
    UserCreateRequest,
    UserDetailResponse,
    UserListRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext
from app.utils.operation_logger import (
    log_create_with_context,
    log_delete_with_context,
    log_query_with_context,
    log_update_with_context,
)
from app.utils.permission_cache_utils import invalidate_user_permission_cache


class UserService(BaseService[User]):
    """用户服务"""

    def __init__(self):
        self.dao = UserDAO()
        self.role_dao = RoleDAO()
        self.permission_dao = PermissionDAO()
        super().__init__(self.dao)

    async def before_create(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建前置钩子：检查用户名和手机号唯一性"""
        if "username" in data and await self.dao.exists(username=data["username"]):
            raise BusinessException("用户名已存在")
        if "phone" in data and data["phone"] and await self.dao.exists(phone=data["phone"]):
            raise BusinessException("手机号已被注册")
        return data

    async def before_update(self, obj: User, data: dict[str, Any]) -> dict[str, Any]:
        """更新前置钩子：检查用户名和手机号唯一性"""
        if "username" in data and await self.dao.exists(username=data["username"], id__not=obj.id):
            raise BusinessException("用户名已存在")
        if "phone" in data and data["phone"] and await self.dao.exists(phone=data["phone"], id__not=obj.id):
            raise BusinessException("手机号已被注册")
        return data

    @log_create_with_context("user")
    async def create_user(self, request: UserCreateRequest, operation_context: OperationContext) -> UserResponse:
        """创建用户，并可选择性地关联角色"""
        current_user = operation_context.user
        create_data = request.model_dump(exclude={"role_ids", "password"}, exclude_unset=True)
        create_data["password_hash"] = hash_password(request.password)
        create_data["creator_id"] = current_user.id
        create_data["is_active"] = True

        user = await self.create(operation_context=operation_context, **create_data)
        if not user:
            raise BusinessException("用户创建失败")

        if request.role_ids:
            roles = await self.role_dao.get_by_ids(request.role_ids)
            await user.roles.add(*roles)

        return UserResponse.model_validate(user)

    @log_update_with_context("user")
    async def update_user(
        self, user_id: UUID, request: UserUpdateRequest, operation_context: OperationContext
    ) -> UserResponse:
        """更新用户信息"""
        update_data = request.model_dump(exclude_unset=True)
        
        version = update_data.pop("version", None)
        if version is None:
            raise BusinessException("更新请求必须包含 version 字段。")

        updated_user = await self.update(user_id, operation_context=operation_context, version=version, **update_data)
        if not updated_user:
            raise BusinessException("用户更新失败或版本冲突")

        return UserResponse.model_validate(updated_user)

    @log_delete_with_context("user")
    async def delete_user(self, user_id: UUID, operation_context: OperationContext) -> None:
        """删除用户"""
        await self.delete(user_id, operation_context=operation_context)

    @log_query_with_context("user")
    async def get_user_detail(self, user_id: UUID, operation_context: OperationContext) -> UserDetailResponse:
        """获取用户详情，包含角色和所有权限"""
        # 确保不返回软删除的用户
        user = await self.dao.get_with_related(
            user_id, prefetch_related=["roles", "permissions"], include_deleted=False
        )
        if not user:
            raise BusinessException("用户未找到")

        all_permissions = await self._get_user_permissions(user)
        user_detail = UserDetailResponse.model_validate(user)
        user_detail.permissions = [PermissionResponse.model_validate(p) for p in all_permissions]
        return user_detail

    @log_query_with_context("user")
    async def get_users(
        self, query: UserListRequest, operation_context: OperationContext
    ) -> tuple[list[UserResponse], int]:
        """获取用户列表"""
        from app.utils.query_utils import list_query_to_orm_filters

        query_dict = query.model_dump(exclude_unset=True)

        USER_MODEL_FIELDS = {"is_superuser", "is_active"}

        search_fields = ["username", "phone", "nickname"]

        model_filters, dao_params = list_query_to_orm_filters(query_dict, search_fields, USER_MODEL_FIELDS)

        if query.role_code:
            role = await self.role_dao.get_one(role_code=query.role_code)
            if role:
                user_ids = await self.dao.get_user_ids_by_role(role.id)
                if not user_ids:
                    return [], 0
                model_filters["id__in"] = user_ids
            else:
                return [], 0

        order_by = (
            [f"-{query.sort_by}" if query.sort_order == "desc" else query.sort_by] if query.sort_by else ["-created_at"]
        )

        q_objects = model_filters.pop("q_objects", [])

        users, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            q_objects=q_objects,
            **dao_params,
            **model_filters,
        )
        return [UserResponse.model_validate(user) for user in users], total

    async def authenticate(self, username: str, password: str) -> User | None:
        """用户认证"""
        user = await self.dao.get_one(username=username, is_active=True)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    async def update_user_status(self, user_id: UUID, is_active: bool, operation_context: OperationContext) -> None:
        """更新用户状态"""
        current_user = operation_context.user
        if current_user.id == user_id:
            raise BusinessException("不能修改自己的状态")
        
        user_to_update = await self.dao.get_by_id(user_id)
        if not user_to_update:
            raise BusinessException("用户未找到")

        await self.update(
            user_id,
            operation_context=operation_context,
            version=user_to_update.version,
            is_active=is_active,
        )

    @invalidate_user_permission_cache("user_id")
    async def assign_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserDetailResponse:
        """为用户分配角色（全量设置）"""
        # 在服务层确保预加载关系，这是最可靠的位置
        user = await self.dao.get_with_related(user_id, prefetch_related=["roles"])
        if not user:
            raise BusinessException("用户未找到")

        # 现在 user.roles 已经被加载，可以安全地将 user 对象传递给 DAO 层
        await self.dao.set_user_roles(user, role_ids)
        return await self.get_user_detail(user_id, operation_context)

    @invalidate_user_permission_cache("user_id")
    async def add_user_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserDetailResponse:
        """为用户增量添加角色"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.add_user_roles(user_id, role_ids)
        return await self.get_user_detail(user_id, operation_context)

    @invalidate_user_permission_cache("user_id")
    async def remove_user_roles(
        self, user_id: UUID, role_ids: list[UUID], operation_context: OperationContext
    ) -> UserDetailResponse:
        """移除用户的指定角色"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.remove_user_roles(user_id, role_ids)
        return await self.get_user_detail(user_id, operation_context)

    async def get_user_roles(self, user_id: UUID, operation_context: OperationContext) -> list[dict]:
        """获取用户的角色列表"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        roles = await self.dao.get_user_roles(user_id)
        return [{"id": role.id, "role_name": role.role_name, "role_code": role.role_code} for role in roles]

    @invalidate_user_permission_cache("user_id")
    async def assign_permissions_to_user(
        self, user_id: UUID, request: UserAssignPermissionsRequest, operation_context: OperationContext
    ) -> UserDetailResponse:
        """为用户分配直接权限（全量设置）"""
        await self.dao.set_user_permissions(user_id, request.permission_ids)
        return await self.get_user_detail(user_id, operation_context)

    async def add_user_permissions(
        self, user_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> UserDetailResponse:
        """为用户增量添加权限"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.add_user_permissions(user_id, permission_ids)
        return await self.get_user_detail(user_id, operation_context)

    async def remove_user_permissions(
        self, user_id: UUID, permission_ids: list[UUID], operation_context: OperationContext
    ) -> UserDetailResponse:
        """移除用户的指定权限"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        await self.dao.remove_user_permissions(user_id, permission_ids)
        return await self.get_user_detail(user_id, operation_context)

    async def get_user_permissions(
        self, user_id: UUID, operation_context: OperationContext
    ) -> list[PermissionResponse]:
        """获取用户的直接权限列表"""
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise BusinessException("用户未找到")

        permissions = await self.dao.get_user_permissions(user_id)
        return [PermissionResponse.model_validate(perm) for perm in permissions]

    async def get_users_by_role_id(self, role_id: UUID, operation_context: OperationContext) -> list[UserResponse]:
        """根据角色ID获取用户列表"""
        users = await self.dao.find_by_fields(roles__id=role_id, include_deleted=False)
        return [UserResponse.model_validate(user) for user in users]

    async def _get_user_permissions(self, user: User) -> set[Permission]:
        """获取用户的所有权限，包括直接权限和通过角色继承的权限。"""
        if user.is_superuser:
            return set(await self.permission_dao.get_all())

        # 为确保数据最新，重新获取用户并预加载所有需要的嵌套关系
        fresh_user = await self.dao.get_with_related(
            user.id, prefetch_related=["permissions", "roles__permissions"]
        )
        if not fresh_user:
            return set()

        # 收集直接权限
        direct_permissions = set(fresh_user.permissions)

        # 收集通过角色继承的权限
        role_permissions = set()
        for role in fresh_user.roles:
            # "roles__permissions" 预加载确保了 role.permissions 已被加载
            role_permissions.update(role.permissions)

        return direct_permissions.union(role_permissions)

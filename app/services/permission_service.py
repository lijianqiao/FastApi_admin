"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission_service.py
@DateTime: 2025/06/05 14:09:24
@Docs: 提供权限相关的业务逻辑处理，包括权限创建、更新、删除、角色分配等。
"""

from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import DuplicateRecordError, RecordNotFoundError
from app.models import Permission
from app.models.models import Role, User
from app.repositories import PermissionRepository, RoleRepository, UserRepository
from app.schemas import (
    PagedResponse,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    PermissionWithRoles,
)
from app.services.base import AppBaseService
from app.utils.audit import audit_create, audit_delete, audit_update, get_permission_id
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PermissionService(AppBaseService[Permission, UUID]):
    """权限服务类

    提供权限相关的业务逻辑处理
    """

    repository_type = PermissionRepository
    create_schema = PermissionCreate
    update_schema = PermissionUpdate
    response_schema = PermissionResponse

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.permission_repo: PermissionRepository = self.repository  # type: ignore
        # 权限服务需要访问角色仓储来管理角色权限关联
        self.role_repo = RoleRepository(session=self.session)
        # 权限服务需要访问用户仓储来获取用户权限
        self.user_repo = UserRepository(session=self.session)
        # 权限服务需要访问用户仓储来获取用户权限
        self.user_repo = UserRepository(session=self.session)

    @audit_create(resource="Permission", get_id=get_permission_id)
    async def create_permission(
        self, permission_data: PermissionCreate, created_by: UUID | None = None
    ) -> PermissionResponse:
        """创建权限

        Args:
            permission_data: 权限创建数据
            created_by: 创建者ID

        Returns:
            创建的权限对象

        Raises:
            DuplicateRecordError: 当权限已存在时
        """
        logger.info(f"开始创建权限: {permission_data.name}")

        # 检查权限名称唯一性
        existing_permission = await self.permission_repo.get_one_by_field(
            field_name="name", value=permission_data.name, include_deleted=False
        )
        if existing_permission:
            raise DuplicateRecordError(f"权限名称 '{permission_data.name}' 已存在")

        # 检查权限代码唯一性
        existing_permission = await self.permission_repo.get_by_code(permission_data.code)
        if existing_permission:
            raise DuplicateRecordError(f"权限代码 '{permission_data.code}' 已存在")

        # 检查资源和操作组合是否已存在
        existing_permission = await self.permission_repo.get_by_resource_and_action(
            resource=permission_data.resource, action=permission_data.action
        )
        if existing_permission:
            raise DuplicateRecordError(
                f"资源 '{permission_data.resource}' 和操作 '{permission_data.action}' 的权限组合已存在"
            )

        # 创建权限实例
        permission_instance = Permission(**permission_data.model_dump())
        permission = await self.permission_repo.create_record(permission_instance)

        logger.info(f"权限创建成功: ID={permission.id}, Name={permission.name}")
        return PermissionResponse.model_validate(permission)

    async def get_permission_by_id(self, permission_id: UUID) -> PermissionResponse:
        """根据ID获取权限

        Args:
            permission_id: 权限ID

        Returns:
            权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        return PermissionResponse.model_validate(permission)

    async def get_permission_by_code(self, code: str) -> PermissionResponse:
        """根据权限代码获取权限

        Args:
            code: 权限代码

        Returns:
            权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        permission = await self.permission_repo.get_by_code(code)
        if not permission:
            raise RecordNotFoundError(f"权限代码不存在: {code}")

        return PermissionResponse.model_validate(permission)

    async def get_permission_by_resource_and_action(self, resource: str, action: str) -> PermissionResponse:
        """根据资源和操作获取权限

        Args:
            resource: 资源名称
            action: 操作类型

        Returns:
            权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        permission = await self.permission_repo.get_by_resource_and_action(resource=resource, action=action)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {resource}:{action}")

        return PermissionResponse.model_validate(permission)

    @audit_update(resource="Permission", get_id=get_permission_id)
    async def update_permission(
        self, permission_id: UUID, permission_data: PermissionUpdate, updated_by: UUID | None = None
    ) -> PermissionResponse:
        """更新权限

        Args:
            permission_id: 权限ID
            permission_data: 更新数据
            updated_by: 更新者ID

        Returns:
            更新后的权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
            DuplicateRecordError: 当更新数据冲突时
        """
        logger.info(f"开始更新权限: {permission_id}")

        # 检查权限是否存在
        existing_permission = await self.permission_repo.get_by_id(permission_id)
        if not existing_permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        # 检查名称唯一性（如果更改了名称）
        if permission_data.name and permission_data.name != existing_permission.name:
            duplicate_permission = await self.permission_repo.get_one_by_field(
                field_name="name", value=permission_data.name, include_deleted=False
            )
            if duplicate_permission and duplicate_permission.id != permission_id:
                raise DuplicateRecordError(f"权限名称 '{permission_data.name}' 已存在")

        # 更新权限
        update_data = permission_data.model_dump(exclude_unset=True)
        updated_permission = await self.permission_repo.update_record(permission_id, update_data)

        logger.info(f"权限更新成功: ID={permission_id}")
        return PermissionResponse.model_validate(updated_permission)

    @audit_delete(resource="Permission", get_id=get_permission_id)
    async def delete_permission(
        self, permission_id: UUID, deleted_by: UUID | None = None, hard_delete: bool = False
    ) -> PermissionResponse:
        """删除权限

        Args:
            permission_id: 权限ID
            deleted_by: 删除者ID
            hard_delete: 是否硬删除

        Returns:
            删除的权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        logger.info(f"开始删除权限: {permission_id}, 硬删除: {hard_delete}")

        # 检查权限是否存在
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        if hard_delete:
            # 硬删除：物理删除记录
            await self.permission_repo.delete_record(permission_id, hard_delete=True)
            deleted_permission = permission
        else:
            # 软删除：更新 is_deleted 字段
            deleted_permission = await self.permission_repo.update_record(permission_id, {"is_deleted": True})

        logger.info(f"权限删除成功: ID={permission_id}")
        return PermissionResponse.model_validate(deleted_permission)

    async def list_permissions(
        self,
        skip: int = 0,
        limit: int = 20,
        resource: str | None = None,
        action: str | None = None,
        keyword: str | None = None,
        include_deleted: bool = False,
    ) -> PagedResponse[PermissionResponse]:
        """获取权限列表（分页和筛选）

        Args:
            skip: 跳过数量
            limit: 限制数量
            resource: 资源筛选
            action: 操作筛选
            keyword: 关键词搜索
            include_deleted: 是否包含已删除

        Returns:
            分页的权限列表
        """
        logger.info(
            f"获取权限列表: skip={skip}, limit={limit}, resource={resource}, action={action}, keyword={keyword}"
        )

        # 构建筛选条件
        filters = []

        # 资源筛选
        if resource:
            from advanced_alchemy.filters import CollectionFilter

            filters.append(CollectionFilter(field_name="resource", values=[resource]))

        # 操作筛选
        if action:
            from advanced_alchemy.filters import CollectionFilter

            filters.append(CollectionFilter(field_name="action", values=[action]))

        # 关键词搜索（搜索名称、描述、代码字段）
        if keyword:
            from advanced_alchemy.filters import SearchFilter

            filters.append(SearchFilter(field_name="name", value=keyword, ignore_case=True))

        # 获取总数
        total = await self.repository.count_records(*filters, include_deleted=include_deleted)

        # 获取分页数据
        offset = skip

        filters.append(LimitOffset(limit=limit, offset=offset))

        # 使用预加载优化的方法获取权限列表
        records = await self.permission_repo.list_with_roles(*filters, include_deleted=include_deleted)

        # 计算页数
        pages = (total + limit - 1) // limit if total > 0 else 0
        current_page = skip // limit + 1

        # 转换为权限响应模型
        permission_responses = [PermissionResponse.model_validate(p) for p in records]

        return PagedResponse[PermissionResponse](
            items=permission_responses,
            total=total,
            page=current_page,
            size=limit,
            pages=pages,
        )

    async def check_permission_exists(self, permission_id: UUID) -> bool:
        """检查权限是否存在

        Args:
            permission_id: 权限ID

        Returns:
            是否存在
        """
        permission = await self.permission_repo.get_by_id(permission_id, include_deleted=False)
        return permission is not None

    async def check_permission_code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        """检查权限代码是否存在

        Args:
            code: 权限代码
            exclude_id: 排除的权限ID

        Returns:
            是否存在
        """
        return await self.permission_repo.check_permission_code_exists(code, exclude_id)

    async def validate_permissions(self, permission_ids: list[UUID]) -> list[PermissionResponse]:
        """验证权限ID列表的有效性

        Args:
            permission_ids: 权限ID列表

        Returns:
            有效的权限列表

        Raises:
            RecordNotFoundError: 当有权限不存在时
        """
        if not permission_ids:
            return []

        permissions = await self.permission_repo.get_permissions_by_ids(permission_ids)
        found_ids = {p.id for p in permissions}
        missing_ids = set(permission_ids) - found_ids

        if missing_ids:
            raise RecordNotFoundError(f"以下权限不存在: {list(missing_ids)}")

        return [PermissionResponse.model_validate(p) for p in permissions]

    async def batch_update_permission_status(
        self, permission_ids: list[UUID], is_active: bool, updated_by: UUID | None = None
    ) -> list[PermissionResponse]:
        """批量更新权限状态

        Args:
            permission_ids: 权限ID列表
            is_active: 激活状态
            updated_by: 更新者ID

        Returns:
            更新后的权限列表
        """
        logger.info(f"批量更新权限状态: {len(permission_ids)} 个权限")

        # 验证权限是否存在
        await self.validate_permissions(permission_ids)

        updated_permissions = []
        for permission_id in permission_ids:
            permission = await self.permission_repo.get_by_id(permission_id)
            if permission:
                updated_permission = await self.permission_repo.update_record(permission_id, {"is_active": is_active})
                updated_permissions.append(PermissionResponse.model_validate(updated_permission))

        logger.info(f"批量更新权限状态成功: {len(updated_permissions)} 个权限")
        return updated_permissions

    async def batch_delete_permissions(
        self, permission_ids: list[UUID], deleted_by: UUID | None = None, hard_delete: bool = False
    ) -> list[PermissionResponse]:
        """批量删除权限

        Args:
            permission_ids: 权限ID列表
            deleted_by: 删除者ID
            hard_delete: 是否硬删除

        Returns:
            删除的权限列表
        """
        logger.info(f"批量删除权限: {len(permission_ids)} 个权限, 硬删除: {hard_delete}")

        # 验证权限是否存在
        await self.validate_permissions(permission_ids)

        deleted_permissions = []
        for permission_id in permission_ids:
            permission = await self.permission_repo.get_by_id(permission_id)
            if permission:
                if hard_delete:
                    await self.permission_repo.delete_record(permission_id, hard_delete=True)
                    deleted_permissions.append(PermissionResponse.model_validate(permission))
                else:
                    deleted_permission = await self.permission_repo.update_record(permission_id, {"is_deleted": True})
                    deleted_permissions.append(PermissionResponse.model_validate(deleted_permission))

        logger.info(f"批量删除权限成功: {len(deleted_permissions)} 个权限")
        return deleted_permissions

    async def get_permissions_by_codes(self, codes: list[str]) -> list[PermissionResponse]:
        """根据权限代码列表获取权限

        Args:
            codes: 权限代码列表

        Returns:
            权限列表
        """
        if not codes:
            return []

        permissions = await self.permission_repo.get_permissions_by_codes(codes)
        return [PermissionResponse.model_validate(p) for p in permissions]

    # ===================== 角色权限管理功能 =====================

    async def get_permission_with_roles(self, permission_id: UUID) -> PermissionWithRoles:
        """获取权限及其关联的角色信息

        Args:
            permission_id: 权限ID

        Returns:
            带角色的权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        logger.info(f"获取权限 {permission_id} 的角色信息")

        # 使用预加载优化方法避免N+1查询
        permission = await self.permission_repo.get_with_roles(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        # 获取该权限关联的角色ID列表
        role_ids = [role.id for role in permission.roles]

        return PermissionWithRoles(**PermissionResponse.model_validate(permission).model_dump(), roles=role_ids)

    @audit_update(resource="Permission", get_id=get_permission_id)
    async def assign_permission_to_roles(
        self, permission_id: UUID, role_ids: list[UUID], updated_by: UUID | None = None
    ) -> PermissionWithRoles:
        """给角色赋予权限

        Args:
            permission_id: 权限ID
            role_ids: 角色ID列表
            updated_by: 更新者ID

        Returns:
            更新后的权限对象

        Raises:
            RecordNotFoundError: 当权限或角色不存在时
        """
        logger.info(f"为权限 {permission_id} 分配角色: {role_ids}")

        # 检查权限是否存在
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        # 验证角色是否存在
        if role_ids:
            roles = await self.role_repo.get_roles_by_ids(role_ids)
            found_role_ids = {role.id for role in roles}
            missing_role_ids = set(role_ids) - found_role_ids
            if missing_role_ids:
                raise RecordNotFoundError(f"以下角色不存在: {list(missing_role_ids)}")

        # 使用事务更新权限的角色关联
        async with self.transaction():
            # 获取新的角色对象列表
            new_roles = []
            for role_id in role_ids:
                role = await self.role_repo.get_by_id(role_id)
                if role:
                    new_roles.append(role)

            # 替换权限的角色关联
            permission.roles = new_roles
            # 保存更改
            await self.session.commit()  # 重新获取更新后的权限
        updated_permission = await self.permission_repo.get_by_id(permission_id)
        if not updated_permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        logger.info(f"权限 {permission_id} 角色分配成功")
        return PermissionWithRoles(
            **PermissionResponse.model_validate(updated_permission).model_dump(),
            roles=[role.id for role in updated_permission.roles],
        )

    @audit_update(resource="Permission", get_id=get_permission_id)
    async def remove_permission_from_roles(
        self, permission_id: UUID, role_ids: list[UUID], updated_by: UUID | None = None
    ) -> PermissionWithRoles:
        """移除角色权限

        Args:
            permission_id: 权限ID
            role_ids: 要移除的角色ID列表
            updated_by: 更新者ID

        Returns:
            更新后的权限对象

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        logger.info(f"从权限 {permission_id} 移除角色: {role_ids}")

        # 检查权限是否存在
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        # 使用事务更新权限的角色关联
        async with self.transaction():
            # 移除指定的角色
            permission.roles = [role for role in permission.roles if role.id not in role_ids]
            # 保存更改
            await self.session.commit()  # 重新获取更新后的权限
        updated_permission = await self.permission_repo.get_by_id(permission_id)
        if not updated_permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        logger.info(f"权限 {permission_id} 角色移除成功")
        return PermissionWithRoles(
            **PermissionResponse.model_validate(updated_permission).model_dump(),
            roles=[role.id for role in updated_permission.roles],
        )

    async def get_permissions_by_role(self, role_id: UUID) -> list[PermissionResponse]:
        """获取角色的权限列表

        Args:
            role_id: 角色ID

        Returns:
            权限列表

        Raises:
            RecordNotFoundError: 当角色不存在时
        """
        logger.info(f"获取角色 {role_id} 的权限列表")

        # 检查角色是否存在
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RecordNotFoundError(f"角色不存在: {role_id}")

        # 获取角色的权限列表
        permissions = role.permissions
        return [PermissionResponse.model_validate(p) for p in permissions]

    async def check_role_has_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """检查角色是否具有某个权限

        Args:
            role_id: 角色ID
            permission_id: 权限ID

        Returns:
            是否具有权限
        """
        logger.info(f"检查角色 {role_id} 是否具有权限 {permission_id}")

        # 获取角色的权限列表
        try:
            permissions = await self.get_permissions_by_role(role_id)
            permission_ids = {p.id for p in permissions}
            return permission_id in permission_ids
        except RecordNotFoundError:
            return False

    @audit_update(resource="Permission", get_id=get_permission_id)
    async def batch_assign_permissions_to_roles(
        self, permission_role_mapping: dict[UUID, list[UUID]], updated_by: UUID | None = None
    ) -> list[PermissionWithRoles]:
        """批量分配权限给角色

        Args:
            permission_role_mapping: 权限ID到角色ID列表的映射
            updated_by: 更新者ID

        Returns:
            更新后的权限列表

        Raises:
            RecordNotFoundError: 当权限或角色不存在时
        """
        logger.info(f"批量分配权限给角色: {len(permission_role_mapping)} 个权限")

        updated_permissions = []
        async with self.transaction():
            for permission_id, role_ids in permission_role_mapping.items():
                updated_permission = await self.assign_permission_to_roles(permission_id, role_ids, updated_by)
                updated_permissions.append(updated_permission)
                logger.info(f"批量权限分配成功: {len(updated_permissions)} 个权限")
        return updated_permissions

    async def get_roles_by_permission(self, permission_id: UUID) -> list[UUID]:
        """获取拥有指定权限的角色ID列表

        Args:
            permission_id: 权限ID

        Returns:
            角色ID列表

        Raises:
            RecordNotFoundError: 当权限不存在时
        """
        logger.info(f"获取拥有权限 {permission_id} 的角色列表")

        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise RecordNotFoundError(f"权限不存在: {permission_id}")

        return [role.id for role in permission.roles]

    async def get_user_permissions(self, user_id: UUID) -> list[PermissionResponse]:
        """获取用户的所有权限（通过角色）- 优化版本

        Args:
            user_id: 用户ID

        Returns:
            用户权限列表

        Raises:
            RecordNotFoundError: 当用户不存在时
        """
        logger.info(f"获取用户 {user_id} 的权限列表")

        # 使用优化的预加载查询
        query = select(User).where(User.id == user_id).options(selectinload(User.roles).selectinload(Role.permissions))

        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise RecordNotFoundError(f"用户不存在: {user_id}")

        # 快速去重并收集权限
        user_permissions = {}
        for role in user.roles:
            for permission in role.permissions:
                if not permission.is_deleted:  # 过滤已删除的权限
                    user_permissions[permission.id] = permission

        permissions_list = list(user_permissions.values())
        logger.info(f"用户 {user_id} 共有 {len(permissions_list)} 个权限")
        return [PermissionResponse.model_validate(p) for p in permissions_list]

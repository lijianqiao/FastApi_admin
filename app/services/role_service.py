"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role_service.py
@DateTime: 2025/06/04
@Docs: 角色服务层

提供角色相关的业务逻辑处理，包括角色创建、更新、删除、权限分配等。
"""

from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.filters import CollectionFilter
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
)
from app.models import Role
from app.repositories import PermissionRepository, RoleRepository, UserRepository
from app.schemas import (
    RoleCreate,
    RoleQuery,
    RoleResponse,
    RoleUpdate,
    RoleWithPermission,
    RoleWithUsers,
    UserRoleAssignRequest,
    UserWithRoles,
)
from app.services.base import AppBaseService
from app.services.cache_service import cache_service
from app.utils.audit import (
    audit_create,
    audit_delete,
    audit_update,
    get_role_id,
)


class RoleService(AppBaseService[Role, UUID]):
    repository_type = RoleRepository

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.role_repo: RoleRepository = self.repository  # type: ignore
        self.permission_repo = PermissionRepository(session=self.session)
        self.user_repo = UserRepository(session=self.session)

    @audit_create(resource="Role", get_id=get_role_id)
    async def create_role(
        self,
        role_data: RoleCreate,
    ) -> RoleResponse:
        """创建新角色"""
        self.logger.info(f"尝试创建新角色: {role_data.name}")
        if await self.role_repo.check_role_name_exists(role_data.name):
            self.logger.warning(f"角色名 '{role_data.name}' 已存在。")
            raise DuplicateRecordError(resource="角色", field="name", value=role_data.name)

        new_role_orm = Role(**role_data.model_dump())
        async with self.transaction():
            created_role_orm = await self.role_repo.create_record(new_role_orm)

        self.logger.info(f"角色 {created_role_orm.name} (ID: {created_role_orm.id}) 创建成功。")
        return RoleResponse.model_validate(created_role_orm)

    async def get_role_by_id(self, role_id: UUID, include_deleted: bool = False) -> RoleResponse:
        """根据ID获取角色信息"""
        role_orm = await self.get_record_by_id(role_id, include_deleted=include_deleted)

        if not isinstance(role_orm, Role):  # 防御性检查
            raise RecordNotFoundError(resource="角色", resource_id=role_id)
        return RoleResponse.model_validate(role_orm)

    @audit_update(resource="Role", get_id=get_role_id)
    async def update_role(
        self,
        role_id: UUID,
        role_data: RoleUpdate,
    ) -> RoleResponse:
        """更新现有角色"""
        self.logger.info(f"尝试更新角色 {role_id}。")
        db_role_orm = await self.role_repo.get_by_id(role_id)
        if not db_role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        if role_data.name and role_data.name != db_role_orm.name:
            if await self.role_repo.check_role_name_exists(role_data.name, role_id_to_exclude=role_id):
                self.logger.warning(f"尝试更新角色名失败: 名称 '{role_data.name}' 已被其他角色使用。")
                raise DuplicateRecordError(resource="角色", field="name", value=role_data.name)

        update_data_dict = role_data.model_dump(exclude_unset=True)
        if not update_data_dict:
            self.logger.info(f"角色 {role_id} 无更新内容。")
            return RoleResponse.model_validate(db_role_orm)

        async with self.transaction():
            updated_role_orm = await self.role_repo.update_record(role_id, update_data_dict)
        if not updated_role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)
        self.logger.info(f"角色 {updated_role_orm.name} (ID: {role_id}) 更新成功。")

        # 清理角色相关缓存
        try:
            await cache_service.clear_role_cache(str(role_id))
        except Exception as cache_error:
            self.logger.warning(f"清理角色缓存失败: {cache_error}")

        return RoleResponse.model_validate(updated_role_orm)

    @audit_delete(resource="Role", get_id=get_role_id)
    async def delete_role(
        self,
        role_id: UUID,
        hard_delete: bool = False,
    ) -> RoleResponse:
        """删除角色"""
        self.logger.info(f"尝试删除角色 {role_id} (硬删除: {hard_delete})。")

        # 先获取角色信息以便清理用户缓存
        user_ids = []
        role_orm = await self.role_repo.get_by_id(role_id)
        if role_orm:
            user_ids = [user.id for user in role_orm.users]

        async with self.transaction():
            deleted_role_orm = await self.delete_record_svc(role_id, hard_delete=hard_delete, commit=False)

        if not deleted_role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        # 清理角色相关缓存
        try:
            await cache_service.clear_role_cache(str(role_id))
            # 清理相关用户的缓存（因为他们的角色列表已发生变化）
            for user_id in user_ids:
                await cache_service.clear_user_cache(str(user_id))
        except Exception as cache_error:
            self.logger.warning(f"清理缓存失败: {cache_error}")

        self.logger.info(f"角色 {role_id} ({deleted_role_orm.name}) 已被删除 (硬删除: {hard_delete})。")
        return RoleResponse.model_validate(deleted_role_orm)

    async def list_roles(
        self,
        query: RoleQuery,
    ) -> tuple[Sequence[RoleResponse], int]:
        """获取角色列表（分页和筛选）"""
        self.logger.debug("服务层: 正在列出角色并进行分页和筛选。")
        roles_orm, total = await self.role_repo.search_roles(
            keyword=query.keyword,
            is_active=query.is_active,
            page=query.page,
            page_size=query.size,
            sort_by=query.sort_by or "created_at",
            sort_desc=query.sort_desc,
            include_deleted=query.include_deleted,
        )
        role_responses = [RoleResponse.model_validate(role) for role in roles_orm]
        return role_responses, total

    async def list_roles_with_permissions(
        self,
        query: RoleQuery,
    ) -> tuple[Sequence[RoleWithPermission], int]:
        """获取角色列表及其权限信息（优化版 - 预加载权限关系）"""
        self.logger.debug("服务层: 正在列出角色及权限并进行分页和筛选。")

        # 首先获取分页和总数
        roles_orm, total = await self.role_repo.search_roles(
            keyword=query.keyword,
            is_active=query.is_active,
            page=query.page,
            page_size=query.size,
            sort_by=query.sort_by or "created_at",
            sort_desc=query.sort_desc,
            include_deleted=query.include_deleted,
        )

        # 为了获取权限信息，需要重新查询带权限的角色数据
        role_ids = [role.id for role in roles_orm]
        if role_ids:
            from advanced_alchemy.filters import CollectionFilter

            roles_with_permissions = await self.role_repo.list_with_permissions(
                CollectionFilter(field_name="id", values=role_ids),
                include_deleted=query.include_deleted,
            )
            # 按原顺序排列
            role_dict = {role.id: role for role in roles_with_permissions}
            roles_orm = [role_dict[role_id] for role_id in role_ids if role_id in role_dict]

        role_responses = [RoleWithPermission.model_validate(role) for role in roles_orm]
        return role_responses, total

    # ===================== 用户角色管理功能 =====================
    @audit_update(resource="Role", get_id=lambda result: str(result.role_id))
    async def assign_users_to_role(
        self,
        role_id: UUID,
        user_ids: list[UUID],
    ) -> RoleWithUsers:
        """为角色分配用户"""
        self.logger.info(f"尝试为角色 {role_id} 分配用户: {user_ids}")

        # 验证角色是否存在
        role_orm = await self.role_repo.get_by_id(role_id)
        if not role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)
        # 验证用户是否存在
        if user_ids:
            users_orm = await self.user_repo.get_all_records(CollectionFilter(field_name="id", values=user_ids))
            found_user_ids = {user.id for user in users_orm}
            missing_user_ids = set(user_ids) - found_user_ids
            if missing_user_ids:
                raise RecordNotFoundError(resource="用户", resource_id=str(list(missing_user_ids)))

        async with self.transaction():
            # 为角色分配用户
            for user_id in user_ids:
                if user_id not in [user.id for user in role_orm.users]:
                    user_orm = await self.user_repo.get_by_id(user_id)
                    if user_orm:
                        role_orm.users.append(user_orm)

            # 更新角色
            updated_role_orm = await self.role_repo.update_record(role_id, {})

        if not updated_role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        # 清理相关缓存
        try:
            await cache_service.clear_role_cache(str(role_id))
            # 清理受影响用户的缓存
            for user_id in user_ids:
                await cache_service.clear_user_cache(str(user_id))
        except Exception as cache_error:
            self.logger.warning(f"清理缓存失败: {cache_error}")

        self.logger.info(f"成功为角色 {role_id} 分配了 {len(user_ids)} 个用户")
        return RoleWithUsers.model_validate(updated_role_orm)

    @audit_update(resource="Role", get_id=lambda result: str(result.role_id))
    async def remove_users_from_role(
        self,
        role_id: UUID,
        user_ids: list[UUID],
    ) -> RoleWithUsers:
        """从角色移除用户"""
        self.logger.info(f"尝试从角色 {role_id} 移除用户: {user_ids}")

        # 验证角色是否存在
        role_orm = await self.role_repo.get_by_id(role_id)
        if not role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        async with self.transaction():
            # 从角色移除用户
            role_orm.users = [user for user in role_orm.users if user.id not in user_ids]

            # 更新角色
            updated_role_orm = await self.role_repo.update_record(role_id, {})

        if not updated_role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        # 清理相关缓存
        try:
            await cache_service.clear_role_cache(str(role_id))
            # 清理受影响用户的缓存
            for user_id in user_ids:
                await cache_service.clear_user_cache(str(user_id))
        except Exception as cache_error:
            self.logger.warning(f"清理缓存失败: {cache_error}")

        self.logger.info(f"成功从角色 {role_id} 移除了 {len(user_ids)} 个用户")
        return RoleWithUsers.model_validate(updated_role_orm)

    async def get_role_with_users(self, role_id: UUID) -> RoleWithUsers:
        """获取角色及其关联的用户信息"""
        self.logger.info(f"获取角色 {role_id} 的用户信息")

        role_orm = await self.role_repo.get_by_id(role_id)
        if not role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        return RoleWithUsers.model_validate(role_orm)

    async def get_role_with_permissions(self, role_id: UUID) -> RoleWithPermission:
        """获取角色及其关联的权限信息（优化版 - 预加载权限关系）"""
        self.logger.info(f"获取角色 {role_id} 的权限信息")

        # 使用预加载优化的方法获取角色及其权限
        role_orm = await self.role_repo.get_with_permissions(role_id)
        if not role_orm:
            raise RecordNotFoundError(resource="角色", resource_id=role_id)

        return RoleWithPermission.model_validate(role_orm)

    @audit_update(resource="User", get_id=lambda result: str(result.user_id))
    async def assign_user_roles(
        self,
        assign_request: UserRoleAssignRequest,
    ) -> UserWithRoles:
        """批量分配用户角色"""
        user_id = assign_request.user_id
        role_ids = assign_request.role_ids

        self.logger.info(f"尝试为用户 {user_id} 分配角色: {role_ids}")

        # 验证用户是否存在
        user_orm = await self.user_repo.get_by_id(user_id)
        if not user_orm:
            raise RecordNotFoundError(resource="用户", resource_id=user_id)

        # 验证角色是否存在
        if role_ids:
            roles_orm = await self.role_repo.get_roles_by_ids(role_ids)
            found_role_ids = {role.id for role in roles_orm}
            missing_role_ids = set(role_ids) - found_role_ids
            if missing_role_ids:
                raise RecordNotFoundError(resource="角色", resource_id=str(list(missing_role_ids)))
        async with self.transaction():
            # 清空现有角色，重新分配
            user_orm.roles = []

            # 分配新角色
            for role_id in role_ids:
                role_orm = await self.role_repo.get_by_id(role_id)
                if role_orm:
                    user_orm.roles.append(role_orm)

            # 更新用户
            updated_user_orm = await self.user_repo.update_record(user_id, {})
            if not updated_user_orm:
                raise RecordNotFoundError(resource="用户", resource_id=user_id)

        # 清理用户相关缓存
        try:
            await cache_service.clear_user_cache(str(user_id))
            # 清理受影响角色的缓存
            for role_id in role_ids:
                await cache_service.clear_role_cache(str(role_id))
        except Exception as cache_error:
            self.logger.warning(f"清理缓存失败: {cache_error}")

        # 使用预加载优化的方法重新获取用户及其角色信息
        final_user_orm = await self.user_repo.get_with_roles(user_id)
        if not final_user_orm:
            raise RecordNotFoundError(resource="用户", resource_id=user_id)

        self.logger.info(f"成功为用户 {user_id} 分配了 {len(role_ids)} 个角色")
        return UserWithRoles.model_validate(final_user_orm)

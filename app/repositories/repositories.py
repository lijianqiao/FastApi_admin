"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: domain_repositories.py
@DateTime: 2025/06/03
@Docs: 应用领域模型的具体仓库实现 (基于最终优化版基类更新)
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from sqlalchemy import update

from app.models import AuditLog, Permission, Role, User
from app.repositories.base import AutoIdBaseRepository, BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓库，用于处理用户数据的持久化操作。"""

    model_type = User

    async def get_by_username(self, username: str, include_deleted: bool = False) -> User | None:
        """根据用户名获取用户。

        Args:
            username: 用户名
            include_deleted: 是否包含已删除
        Returns:
            用户对象或None
        """
        return await self.get_one_by_field(field_name="username", value=username, include_deleted=include_deleted)

    async def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """根据邮箱获取用户。

        Args:
            email: 邮箱
            include_deleted: 是否包含已删除
        Returns:
            用户对象或None
        """
        return await self.get_one_by_field(field_name="email", value=email, include_deleted=include_deleted)

    async def get_by_phone(self, phone: str, include_deleted: bool = False) -> User | None:
        """根据手机号获取用户。

        Args:
            phone: 手机号
            include_deleted: 是否包含已删除
        Returns:
            用户对象或None
        """
        return await self.get_one_by_field(field_name="phone", value=phone, include_deleted=include_deleted)

    async def check_username_exists(self, username: str, user_id_to_exclude: UUID | None = None) -> bool:
        """检查用户名是否存在（用于唯一性验证），可排除特定用户ID。

        Args:
            username: 用户名
            user_id_to_exclude: 排除的用户ID
        Returns:
            存在返回True，否则False
        """
        existing_user = await self.get_one_by_field(
            field_name="username",
            value=username,
            include_deleted=False,
        )
        if not existing_user:
            return False
        if user_id_to_exclude and existing_user.id == user_id_to_exclude:
            return False
        return True

    async def check_email_exists(self, email: str, user_id_to_exclude: UUID | None = None) -> bool:
        """检查邮箱是否存在（用于唯一性验证），可排除特定用户ID。

        Args:
            email: 邮箱
            user_id_to_exclude: 排除的用户ID
        Returns:
            存在返回True，否则False
        """
        existing_user = await self.get_one_by_field(field_name="email", value=email, include_deleted=False)
        if not existing_user:
            return False
        if user_id_to_exclude and existing_user.id == user_id_to_exclude:
            return False
        return True

    async def search_users(
        self,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        include_deleted: bool = False,
    ) -> tuple[Sequence[User], int]:
        """搜索用户，支持关键词和激活状态筛选。

        Args:
            keyword: 关键词
            is_active: 是否激活
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_desc: 是否降序
            include_deleted: 是否包含已删除
        Returns:
            用户列表和总数
        """
        filters: list[FilterTypes] = []
        if keyword:
            filters.append(
                SearchFilter(field_name={"username", "email", "nickname", "phone"}, value=keyword, ignore_case=True)
                # 修正: 使用 field_name 并传入 set
            )
        if is_active is not None:
            filters.append(CollectionFilter(field_name="is_active", values=[is_active]))

        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=offset))
        filters.append(OrderBy(field_name=sort_by, sort_order="desc" if sort_desc else "asc"))

        users = await self.get_all_records(*filters, include_deleted=include_deleted)
        return users, total_count

    async def get_active_users(
        self, page: int = 1, page_size: int = 20, sort_by: str = "created_at", sort_desc: bool = True
    ) -> tuple[Sequence[User], int]:
        """获取激活用户列表。

        Args:
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_desc: 是否降序
        Returns:
            用户列表和总数
        """
        active_filter = CollectionFilter(field_name="is_active", values=[True])
        total_count = await self.count_records(active_filter, include_deleted=False)

        offset = (page - 1) * page_size
        order_filter = OrderBy(field_name=sort_by, sort_order="desc" if sort_desc else "asc")
        pagination_filter = LimitOffset(limit=page_size, offset=offset)

        users = await self.get_all_records(active_filter, order_filter, pagination_filter, include_deleted=False)
        return users, total_count

    async def batch_update_status(self, user_ids: list[UUID], is_active: bool) -> int:
        """批量更新用户激活状态。

        Args:
            user_ids: 用户ID列表
            is_active: 激活状态
        Returns:
            受影响的用户数量
        """
        if not user_ids:
            return 0
        stmt = (
            update(self.model_type)
            .where(self.model_type.id.in_(user_ids))  # type: ignore[attr-defined]
            .values(is_active=is_active, updated_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount if result.rowcount is not None else 0


class RoleRepository(BaseRepository[Role]):
    """角色仓库，用于处理角色数据的持久化操作。"""

    model_type = Role

    async def get_by_name(self, name: str, include_deleted: bool = False) -> Role | None:
        """根据角色名获取角色。

        Args:
            name: 角色名
            include_deleted: 是否包含已删除
        Returns:
            角色对象或None
        """
        return await self.get_one_by_field(field_name="name", value=name, include_deleted=include_deleted)

    async def check_role_name_exists(self, name: str, role_id_to_exclude: UUID | None = None) -> bool:
        """检查角色名是否存在（用于唯一性验证），可排除特定角色ID。

        Args:
            name: 角色名
            role_id_to_exclude: 排除的角色ID
        Returns:
            存在返回True，否则False
        """
        existing_role = await self.get_one_by_field(field_name="name", value=name, include_deleted=False)
        if not existing_role:
            return False
        if role_id_to_exclude and existing_role.id == role_id_to_exclude:
            return False
        return True

    async def get_roles_by_ids(self, role_ids: list[UUID], include_deleted: bool = False) -> Sequence[Role]:
        """根据一组ID获取多个角色。

        Args:
            role_ids: 角色ID列表
            include_deleted: 是否包含已删除
        Returns:
            角色对象列表
        """
        if not role_ids:
            return []
        id_filter = CollectionFilter(field_name="id", values=role_ids)
        return await self.get_all_records(id_filter, include_deleted=include_deleted)

    async def search_roles(
        self,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        include_deleted: bool = False,
    ) -> tuple[Sequence[Role], int]:
        """搜索角色，支持关键词（名称、描述）和激活状态筛选。

        Args:
            keyword: 关键词
            is_active: 是否激活
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_desc: 是否降序
            include_deleted: 是否包含已删除
        Returns:
            角色列表和总数
        """
        filters: list[FilterTypes] = []
        if keyword:
            filters.append(
                SearchFilter(field_name={"name", "description"}, value=keyword, ignore_case=True)
            )  # 修正: 使用 field_name 并传入 set
        if is_active is not None:
            filters.append(CollectionFilter(field_name="is_active", values=[is_active]))

        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=offset))
        filters.append(OrderBy(field_name=sort_by, sort_order="desc" if sort_desc else "asc"))

        roles = await self.get_all_records(*filters, include_deleted=include_deleted)
        return roles, total_count

    async def get_roles_by_permission_id(self, permission_id: UUID, include_deleted: bool = False) -> Sequence[Role]:
        """根据权限ID获取相关角色。

        Args:
            permission_id: 权限ID
            include_deleted: 是否包含已删除
        Returns:
            角色对象列表
        """
        # 通过查询角色表并过滤关联的权限来实现
        # 这里使用简化的方法，实际应该通过join查询role_permissions表
        all_roles = await self.get_all_records(include_deleted=include_deleted)
        result_roles = []

        for role in all_roles:
            # 检查角色是否包含指定权限
            permission_ids = [perm.id for perm in role.permissions]
            if permission_id in permission_ids:
                result_roles.append(role)

        return result_roles


class PermissionRepository(BaseRepository[Permission]):
    """权限仓库，用于处理权限数据的持久化操作。"""

    model_type = Permission

    async def get_by_code(self, code: str, include_deleted: bool = False) -> Permission | None:
        """根据权限代码获取权限。

        Args:
            code: 权限代码
            include_deleted: 是否包含已删除
        Returns:
            权限对象或None
        """
        return await self.get_one_by_field(field_name="code", value=code, include_deleted=include_deleted)

    async def check_permission_code_exists(self, code: str, permission_id_to_exclude: UUID | None = None) -> bool:
        """检查权限代码是否存在（用于唯一性验证），可排除特定权限ID。

        Args:
            code: 权限代码
            permission_id_to_exclude: 排除的权限ID
        Returns:
            存在返回True，否则False
        """
        existing_permission = await self.get_one_by_field(field_name="code", value=code, include_deleted=False)
        if not existing_permission:
            return False
        if permission_id_to_exclude and existing_permission.id == permission_id_to_exclude:
            return False
        return True

    async def get_permissions_by_ids(
        self, permission_ids: list[UUID], include_deleted: bool = False
    ) -> Sequence[Permission]:
        """根据一组ID获取多个权限。

        Args:
            permission_ids: 权限ID列表
            include_deleted: 是否包含已删除
        Returns:
            权限对象列表
        """
        if not permission_ids:
            return []
        id_filter = CollectionFilter(field_name="id", values=permission_ids)
        return await self.get_all_records(id_filter, include_deleted=include_deleted)

    async def get_permissions_by_codes(self, codes: list[str], include_deleted: bool = False) -> Sequence[Permission]:
        """根据一组权限代码获取多个权限。

        Args:
            codes: 权限代码列表
            include_deleted: 是否包含已删除
        Returns:
            权限对象列表
        """
        if not codes:
            return []
        code_filter = CollectionFilter(field_name="code", values=codes)
        return await self.get_all_records(code_filter, include_deleted=include_deleted)

    async def get_by_resource_and_action(
        self, resource: str, action: str, include_deleted: bool = False, auto_expunge: bool = True
    ) -> Permission | None:
        """根据资源和操作获取权限。

        Args:
            resource: 资源名
            action: 操作名
            include_deleted: 是否包含已删除
            auto_expunge: 是否自动expunge
        Returns:
            权限对象或None
        """
        business_filters: list[FilterTypes] = [
            CollectionFilter(field_name="resource", values=[resource]),
            CollectionFilter(field_name="action", values=[action]),
        ]
        results = await self.get_all_records(
            *business_filters, include_deleted=include_deleted, auto_expunge=auto_expunge
        )
        return results[0] if results else None


class AuditLogRepository(AutoIdBaseRepository[AuditLog]):
    """审计日志仓库，用于处理审计日志数据的持久化操作。"""

    model_type = AuditLog

    async def get_by_user_id(
        self, user_id: UUID, include_deleted: bool = False, limit: int = 50, offset: int = 0
    ) -> Sequence[AuditLog]:
        """根据用户ID获取审计日志列表。

        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除
            limit: 限制数量
            offset: 偏移量
        Returns:
            审计日志对象列表
        """
        additional_filters: list[FilterTypes] = [
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]
        return await self.get_all_by_field(
            field_name="user_id", value=user_id, include_deleted=include_deleted, other_filters=additional_filters
        )

    async def query_logs_with_filters(
        self,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_name: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = "created_at",
        sort_desc: bool = True,
        include_deleted: bool = False,
    ) -> tuple[Sequence[AuditLog], int]:
        """根据多条件过滤查询审计日志。

        Args:
            user_id: 用户ID
            action: 操作类型
            resource_name: 资源名
            status: 状态
            start_date: 开始时间
            end_date: 结束时间
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_desc: 是否降序
            include_deleted: 是否包含已删除
        Returns:
            审计日志列表和总数
        """
        filters: list[FilterTypes] = []
        if user_id:
            filters.append(CollectionFilter(field_name="user_id", values=[user_id]))
        if action:
            filters.append(CollectionFilter(field_name="action", values=[action]))
        if resource_name:
            filters.append(CollectionFilter(field_name="resource", values=[resource_name]))
        if status:
            filters.append(CollectionFilter(field_name="status", values=[status]))

        if start_date or end_date:
            filters.append(BeforeAfter(field_name="created_at", after=start_date, before=end_date))

        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        current_offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=current_offset))

        filters.append(
            OrderBy(field_name=sort_by if sort_by else "created_at", sort_order="desc" if sort_desc else "asc")
        )

        logs = await self.get_all_records(*filters, include_deleted=include_deleted)
        return logs, total_count

    async def get_latest_logs(self, limit: int = 10, include_deleted: bool = False) -> Sequence[AuditLog]:
        """获取最新的审计日志。

        Args:
            limit: 限制数量
            include_deleted: 是否包含已删除
        Returns:
            审计日志对象列表
        """
        filters: list[FilterTypes] = [
            OrderBy(field_name="created_at", sort_order="desc"),
            LimitOffset(limit=limit, offset=0),
        ]
        return await self.get_all_records(*filters, include_deleted=include_deleted)

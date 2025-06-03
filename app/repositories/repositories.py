"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: repositories.py
@DateTime: 2025/06/03
@Docs: 应用领域模型的具体仓库实现
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from advanced_alchemy.filters import (
    BeforeAfter,
    CollectionFilter,
    FilterTypes,
    LimitOffset,
    OrderBy,
)

from app.models import AuditLog, Permission, Role, User
from app.repositories.base import AutoIdBaseRepository, BaseRepository


# --- 用户仓库 (UserRepository) ---
class UserRepository(BaseRepository[User]):
    """
    用户仓库，用于处理用户数据的持久化操作。
    """

    model_type = User

    async def get_by_username(self, username: str, include_deleted: bool = False) -> User | None:
        """根据用户名获取用户。"""
        return await self.get_one_by_field(field_name="username", value=username, include_deleted=include_deleted)

    async def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """根据邮箱获取用户。"""
        return await self.get_one_by_field(field_name="email", value=email, include_deleted=include_deleted)

    async def get_by_phone(self, phone: str, include_deleted: bool = False) -> User | None:
        """根据手机号获取用户。"""
        return await self.get_one_by_field(field_name="phone", value=phone, include_deleted=include_deleted)


# --- 角色仓库 (RoleRepository) ---
class RoleRepository(BaseRepository[Role]):
    """
    角色仓库，用于处理角色数据的持久化操作。
    """

    model_type = Role

    async def get_by_name(self, name: str, include_deleted: bool = False) -> Role | None:
        """根据角色名称获取角色。"""
        return await self.get_one_by_field(field_name="name", value=name, include_deleted=include_deleted)


# --- 权限仓库 (PermissionRepository) ---
class PermissionRepository(BaseRepository[Permission]):
    """
    权限仓库，用于处理权限数据的持久化操作。
    """

    model_type = Permission

    async def get_by_code(self, code: str, include_deleted: bool = False) -> Permission | None:
        """根据权限代码获取权限。"""
        return await self.get_one_by_field(field_name="code", value=code, include_deleted=include_deleted)

    async def get_by_resource_and_action(
        self, resource: str, action: str, include_deleted: bool = False, auto_expunge: bool = True
    ) -> Permission | None:
        """
        根据资源和操作获取权限。
        使用基类的 get_all_records 以确保软删除逻辑被应用。
        """
        business_filters: list[FilterTypes] = [
            CollectionFilter(field_name="resource", values=[resource]),
            CollectionFilter(field_name="action", values=[action]),
        ]
        # get_all_records 会处理软删除过滤
        results = await self.get_all_records(
            *business_filters, include_deleted=include_deleted, auto_expunge=auto_expunge
        )
        return results[0] if results else None


# --- 审计日志仓库 (AuditLogRepository) ---
class AuditLogRepository(AutoIdBaseRepository[AuditLog]):
    """
    审计日志仓库，用于处理审计日志数据的持久化操作。
    """

    model_type = AuditLog

    async def get_by_user_id(  # 保持方法名与你之前版本一致
        self, user_id: UUID, include_deleted: bool = False, limit: int = 50, offset: int = 0
    ) -> Sequence[AuditLog]:
        """根据用户ID获取审计日志列表。"""
        additional_filters: list[FilterTypes] = [
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]
        # get_all_by_field 会处理软删除过滤
        return await self.get_all_by_field(
            field_name="user_id", value=user_id, include_deleted=include_deleted, *additional_filters
        )

    async def query_logs_with_filters(
        self,
        user_id: UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = "created_at",
        sort_desc: bool = True,
        include_deleted: bool = False,
    ) -> tuple[Sequence[AuditLog], int]:
        """
        根据提供的查询参数筛选审计日志。
        """
        filters: list[FilterTypes] = []
        if user_id:
            filters.append(CollectionFilter(field_name="user_id", values=[user_id]))
        if action:
            filters.append(CollectionFilter(field_name="action", values=[action]))
        if resource:
            filters.append(CollectionFilter(field_name="resource", values=[resource]))
        if status:
            filters.append(CollectionFilter(field_name="status", values=[status]))

        if start_date or end_date:
            filters.append(BeforeAfter(field_name="created_at", after=start_date, before=end_date))

        # 基类的 count_records 会处理软删除逻辑
        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        # 添加分页和排序过滤器
        current_offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=current_offset))

        order_by_field = sort_by if sort_by else "created_at"
        order_direction = "desc" if sort_desc else "asc"
        filters.append(OrderBy(field_name=order_by_field, sort_order=order_direction))

        # 基类的 get_all_records 会处理软删除逻辑
        logs = await self.get_all_records(*filters, include_deleted=include_deleted)
        return logs, total_count

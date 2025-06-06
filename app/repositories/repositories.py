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
            )
        if is_active is not None:
            filters.append(CollectionFilter(field_name="is_active", values=[is_active]))

        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=offset))
        filters.append(OrderBy(field_name=sort_by, sort_order="desc" if sort_desc else "asc"))
        users = await self.get_all_records(*filters, include_deleted=include_deleted)
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

    async def get_with_roles(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        """获取用户及其关联的角色信息（预加载优化）

        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除
        Returns:
            用户对象（包含角色信息）或None
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(User).options(selectinload(User.roles))
        stmt = stmt.where(User.id == user_id)

        if not include_deleted:
            stmt = stmt.where(~User.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_roles(
            self,
            *filters: FilterTypes,
            include_deleted: bool = False,
            auto_expunge: bool = True,
    ) -> Sequence[User]:
        """获取用户列表及其关联的角色信息（预加载优化）

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除
            auto_expunge: 是否自动expunge
        Returns:
            用户对象列表（包含角色信息）
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 构建基础查询
        stmt = select(User).options(selectinload(User.roles))

        # 应用软删除过滤
        if not include_deleted:
            stmt = stmt.where(~User.is_deleted)

        # 应用其他过滤器
        for filter_obj in filters:
            stmt = filter_obj.append_to_statement(stmt, User)

        result = await self.session.execute(stmt)
        return result.scalars().all()


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

    async def get_with_permissions(self, role_id: UUID, include_deleted: bool = False) -> Role | None:
        """获取角色及其关联的权限信息（预加载优化）

        Args:
            role_id: 角色ID
            include_deleted: 是否包含已删除
        Returns:
            角色对象（包含权限信息）或None
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(Role).options(selectinload(Role.permissions))
        stmt = stmt.where(Role.id == role_id)

        if not include_deleted:
            stmt = stmt.where(~Role.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_permissions(
            self,
            *filters: FilterTypes,
            include_deleted: bool = False,
            auto_expunge: bool = True,
    ) -> Sequence[Role]:
        """获取角色列表及其关联的权限信息（预加载优化）

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除
            auto_expunge: 是否自动expunge
        Returns:
            角色对象列表（包含权限信息）
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 构建基础查询
        stmt = select(Role).options(selectinload(Role.permissions))

        # 应用软删除过滤
        if not include_deleted:
            stmt = stmt.where(~Role.is_deleted)

        # 应用其他过滤器
        for filter_obj in filters:
            stmt = filter_obj.append_to_statement(stmt, Role)

        result = await self.session.execute(stmt)
        return result.scalars().all()


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

    async def get_with_roles(self, permission_id: UUID, include_deleted: bool = False) -> Permission | None:
        """获取权限及其关联的角色信息（预加载优化）

        Args:
            permission_id: 权限ID
            include_deleted: 是否包含已删除
        Returns:
            权限对象（包含角色信息）或None
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(Permission).options(selectinload(Permission.roles))
        stmt = stmt.where(Permission.id == permission_id)

        if not include_deleted:
            stmt = stmt.where(~Permission.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_roles(
            self,
            *filters: FilterTypes,
            include_deleted: bool = False,
            auto_expunge: bool = True,
    ) -> Sequence[Permission]:
        """获取权限列表及其关联的角色信息（预加载优化）

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除
            auto_expunge: 是否自动expunge
        Returns:
            权限对象列表（包含角色信息）
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 构建基础查询
        stmt = select(Permission).options(selectinload(Permission.roles))

        # 应用软删除过滤
        if not include_deleted:
            stmt = stmt.where(~Permission.is_deleted)

        # 应用其他过滤器
        for filter_obj in filters:
            stmt = filter_obj.append_to_statement(stmt, Permission)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_permissions(
            self,
            keyword: str | None = None,
            resource: str | None = None,
            action: str | None = None,
            page: int = 1,
            page_size: int = 20,
            sort_by: str = "created_at",
            sort_desc: bool = True,
            include_deleted: bool = False,
    ) -> tuple[Sequence[Permission], int]:
        """搜索权限，支持关键词（名称、代码、描述）和条件筛选。

        Args:
            keyword: 关键词
            resource: 资源筛选
            action: 操作筛选
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_desc: 是否降序
            include_deleted: 是否包含已删除
        Returns:
            权限列表和总数
        """
        filters: list[FilterTypes] = []

        if keyword:
            filters.append(SearchFilter(field_name={"name", "code", "description"}, value=keyword, ignore_case=True))
        if resource:
            filters.append(CollectionFilter(field_name="resource", values=[resource]))
        if action:
            filters.append(CollectionFilter(field_name="action", values=[action]))

        total_count = await self.count_records(*filters, include_deleted=include_deleted)

        offset = (page - 1) * page_size
        filters.append(LimitOffset(limit=page_size, offset=offset))
        filters.append(OrderBy(field_name=sort_by, sort_order="desc" if sort_desc else "asc"))

        permissions = await self.get_all_records(*filters, include_deleted=include_deleted)
        return permissions, total_count


class AuditLogRepository(AutoIdBaseRepository[AuditLog]):
    """审计日志仓库，用于处理审计日志数据的持久化操作。"""

    model_type = AuditLog

    async def count_by_action(self, action: str, include_deleted: bool = False) -> int:
        """直接统计指定操作类型的日志数量

        Args:
            action: 操作类型
            include_deleted: 是否包含已删除

        Returns:
            日志数量
        """
        from sqlalchemy import func, select

        stmt = select(func.count(AuditLog.id)).where(AuditLog.action == action)
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_by_user(self, user_id: UUID, include_deleted: bool = False) -> int:
        """直接统计指定用户的日志数量

        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除

        Returns:
            日志数量
        """
        from sqlalchemy import func, select

        stmt = select(func.count(AuditLog.id)).where(AuditLog.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_by_status(self, status: str, include_deleted: bool = False) -> int:
        """直接统计指定状态的日志数量

        Args:
            status: 状态
            include_deleted: 是否包含已删除

        Returns:
            日志数量
        """
        from sqlalchemy import func, select

        stmt = select(func.count(AuditLog.id)).where(AuditLog.status == status)
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_by_date_range(
            self, start_date: datetime | None = None, end_date: datetime | None = None, include_deleted: bool = False
    ) -> int:
        """直接统计指定日期范围的日志数量

        Args:
            start_date: 开始日期
            end_date: 结束日期
            include_deleted: 是否包含已删除

        Returns:
            日志数量
        """
        from sqlalchemy import func, select

        stmt = select(func.count(AuditLog.id))
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_audit_summary_stats(self, include_deleted: bool = False) -> dict:
        """使用单个查询获取审计日志统计摘要

        Args:
            include_deleted: 是否包含已删除

        Returns:
            统计摘要字典
        """
        from sqlalchemy import case, func, select

        # 获取今天的时间范围
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(day=today.day + 1)

        # 使用聚合查询一次性获取所有统计数据
        stmt = select(
            func.count(AuditLog.id).label("total_logs"),
            func.sum(case((AuditLog.status == "SUCCESS", 1), else_=0)).label("success_logs"),
            func.sum(case((AuditLog.status == "FAILED", 1), else_=0)).label("failed_logs"),
            func.sum(case(((AuditLog.created_at >= today) & (AuditLog.created_at < tomorrow), 1), else_=0)).label(
                "today_logs"
            ),
        )

        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return {"total_logs": 0, "success_logs": 0, "failed_logs": 0, "today_logs": 0, "success_rate": 0}
        total_logs = row.total_logs or 0
        success_logs = row.success_logs or 0
        failed_logs = row.failed_logs or 0
        today_logs = row.today_logs or 0

        return {
            "total_logs": total_logs,
            "success_logs": success_logs,
            "failed_logs": failed_logs,
            "today_logs": today_logs,
            "success_rate": round(success_logs / total_logs * 100, 2) if total_logs > 0 else 0,
        }

    async def get_with_user(self, log_id: int, include_deleted: bool = False) -> AuditLog | None:
        """获取审计日志并预加载用户信息

        Args:
            log_id: 日志ID
            include_deleted: 是否包含已删除

        Returns:
            审计日志对象，如果不存在则返回None
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(AuditLog).options(selectinload(AuditLog.user)).where(AuditLog.id == log_id)
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_user(
            self,
            *filters: FilterTypes,
            include_deleted: bool = False,
            auto_expunge: bool = True,
    ) -> Sequence[AuditLog]:
        """获取审计日志列表并预加载用户信息

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除
            auto_expunge: 是否自动expunge

        Returns:
            审计日志列表
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 构建基础查询
        stmt = select(AuditLog).options(selectinload(AuditLog.user))

        # 应用软删除过滤
        if not include_deleted:
            stmt = stmt.where(~AuditLog.is_deleted)

        # 应用其他过滤器
        for filter_obj in filters:
            stmt = filter_obj.append_to_statement(stmt, AuditLog)

        result = await self.session.execute(stmt)
        return result.scalars().all()

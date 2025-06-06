"""
审计日志服务 - 提供审计日志查询功能
由于审计日志主要由装饰器自动记录，服务主要提供查询相关功能
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.repositories import AuditLogRepository
from app.schemas import AuditLogQuery, AuditLogResponse, PagedResponse
from app.services.base import AppBaseService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditLogService(AppBaseService[AuditLog, int]):
    """审计日志服务类

    提供审计日志查询相关的业务逻辑
    """

    repository_type = AuditLogRepository
    response_schema = AuditLogResponse

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.audit_repo: AuditLogRepository = self.repository  # type: ignore

    async def get_audit_log_by_id(self, log_id: int) -> AuditLogResponse:
        """根据ID获取审计日志并预加载用户信息

        Args:
            log_id: 日志ID

        Returns:
            审计日志对象

        Raises:
            RecordNotFoundError: 当日志不存在时
        """
        # 使用预加载用户信息的方法
        log = await self.audit_repo.get_with_user(log_id)
        if not log:
            from app.exceptions import RecordNotFoundError

            raise RecordNotFoundError(f"审计日志不存在: {log_id}")

        return AuditLogResponse.model_validate(log)

    async def get_user_audit_logs(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[AuditLogResponse]:
        """获取用户的审计日志并预加载用户信息

        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            用户审计日志列表
        """
        logger.info(f"获取用户 {user_id} 的审计日志")

        # 使用优化的查询方法
        from advanced_alchemy.filters import CollectionFilter, LimitOffset, OrderBy

        filters = [
            CollectionFilter(field_name="user_id", values=[user_id]),
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_latest_audit_logs(self, limit: int = 10) -> list[AuditLogResponse]:
        """获取最新的审计日志并预加载用户信息

        Args:
            limit: 限制数量

        Returns:
            最新审计日志列表
        """
        logger.info(f"获取最新 {limit} 条审计日志")

        # 使用优化的查询方法
        from advanced_alchemy.filters import LimitOffset, OrderBy

        filters = [LimitOffset(limit=limit, offset=0), OrderBy(field_name="created_at", sort_order="desc")]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def query_audit_logs(self, query: AuditLogQuery) -> PagedResponse[AuditLogResponse]:
        """根据条件查询审计日志（使用优化的count和预加载）

        Args:
            query: 查询条件

        Returns:
            分页的审计日志列表
        """
        logger.info(f"查询审计日志: page={query.page}, size={query.size}")

        # 构建过滤器
        from advanced_alchemy.filters import BeforeAfter, CollectionFilter, LimitOffset, OrderBy

        filters = []
        count_filters = []

        if query.user_id:
            filter_obj = CollectionFilter(field_name="user_id", values=[query.user_id])
            filters.append(filter_obj)
            count_filters.append(filter_obj)

        if query.action:
            filter_obj = CollectionFilter(field_name="action", values=[query.action])
            filters.append(filter_obj)
            count_filters.append(filter_obj)

        if query.resource:
            filter_obj = CollectionFilter(field_name="resource", values=[query.resource])
            filters.append(filter_obj)
            count_filters.append(filter_obj)

        if query.status:
            filter_obj = CollectionFilter(field_name="status", values=[query.status])
            filters.append(filter_obj)
            count_filters.append(filter_obj)

        if query.start_date or query.end_date:
            filter_obj = BeforeAfter(field_name="created_at", after=query.start_date, before=query.end_date)
            filters.append(filter_obj)
            count_filters.append(filter_obj)

        # 获取总数（使用优化的count查询）
        total_count = await self.audit_repo.count_records(*count_filters, include_deleted=query.include_deleted)

        # 添加分页和排序
        current_offset = (query.page - 1) * query.size
        filters.append(LimitOffset(limit=query.size, offset=current_offset))
        filters.append(
            OrderBy(
                field_name=query.sort_by if query.sort_by else "created_at",
                sort_order="desc" if query.sort_desc else "asc",
            )
        )

        # 获取数据（使用预加载）
        logs = await self.audit_repo.list_with_user(*filters, include_deleted=query.include_deleted)

        # 转换为响应模型
        log_responses = [AuditLogResponse.model_validate(log) for log in logs]

        # 计算总页数
        total_pages = (total_count + query.size - 1) // query.size

        return PagedResponse[AuditLogResponse](
            items=log_responses, total=total_count, page=query.page, size=query.size, pages=total_pages
        )

    async def get_audit_logs_by_action(self, action: str, limit: int = 50, offset: int = 0) -> list[AuditLogResponse]:
        """根据操作类型获取审计日志

        Args:
            action: 操作类型
            limit: 限制数量
            offset: 偏移量

        Returns:
            审计日志列表
        """
        logger.info(f"获取操作类型为 {action} 的审计日志")

        # 使用优化的预加载方法
        from advanced_alchemy.filters import CollectionFilter, LimitOffset, OrderBy

        filters = [
            CollectionFilter(field_name="action", values=[action]),
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_audit_logs_by_resource(
        self, resource: str, limit: int = 50, offset: int = 0
    ) -> list[AuditLogResponse]:
        """根据资源类型获取审计日志（使用预加载优化）

        Args:
            resource: 资源类型
            limit: 限制数量
            offset: 偏移量

        Returns:
            审计日志列表
        """
        logger.info(f"获取资源类型为 {resource} 的审计日志")

        # 使用优化的预加载方法
        from advanced_alchemy.filters import CollectionFilter, LimitOffset, OrderBy

        filters = [
            CollectionFilter(field_name="resource", values=[resource]),
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_failed_operations(self, limit: int = 50, offset: int = 0) -> list[AuditLogResponse]:
        """获取失败的操作日志（使用预加载优化）

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            失败操作日志列表
        """
        logger.info("获取失败的操作日志")

        # 使用优化的预加载方法
        from advanced_alchemy.filters import CollectionFilter, LimitOffset, OrderBy

        filters = [
            CollectionFilter(field_name="status", values=["FAILED"]),
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_audit_logs_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 50, offset: int = 0
    ) -> list[AuditLogResponse]:
        """根据日期范围获取审计日志（使用预加载优化）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量

        Returns:
            审计日志列表
        """
        logger.info(f"获取 {start_date} 到 {end_date} 的审计日志")

        # 使用优化的预加载方法
        from advanced_alchemy.filters import BeforeAfter, LimitOffset, OrderBy

        filters = [
            BeforeAfter(field_name="created_at", after=start_date, before=end_date),
            LimitOffset(limit=limit, offset=offset),
            OrderBy(field_name="created_at", sort_order="desc"),
        ]

        logs = await self.audit_repo.list_with_user(*filters)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def count_logs_by_action(self, action: str) -> int:
        """统计指定操作类型的日志数量

        Args:
            action: 操作类型

        Returns:
            日志数量
        """
        # 使用优化的直接count查询方法
        return await self.audit_repo.count_by_action(action)

    async def count_logs_by_user(self, user_id: UUID) -> int:
        """统计指定用户的日志数量

        Args:
            user_id: 用户ID

        Returns:
            日志数量
        """
        # 使用优化的直接count查询方法
        return await self.audit_repo.count_by_user(user_id)

    async def count_logs_by_status(self, status: str) -> int:
        """统计指定状态的日志数量（使用直接count查询优化）

        Args:
            status: 状态

        Returns:
            日志数量
        """
        return await self.audit_repo.count_by_status(status)

    async def count_logs_by_date_range(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> int:
        """统计指定日期范围的日志数量（使用直接count查询优化）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日志数量
        """
        return await self.audit_repo.count_by_date_range(start_date, end_date)

    async def get_audit_summary(self) -> dict:
        """获取审计日志统计摘要（使用聚合查询优化）

        Returns:
            统计摘要数据
        """
        logger.info("获取审计日志统计摘要")

        # 使用优化的聚合查询一次性获取所有统计数据
        return await self.audit_repo.get_audit_summary_stats()

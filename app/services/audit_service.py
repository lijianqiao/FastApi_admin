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
        """根据ID获取审计日志

        Args:
            log_id: 日志ID

        Returns:
            审计日志对象

        Raises:
            RecordNotFoundError: 当日志不存在时
        """
        log = await self.audit_repo.get_by_id(log_id)
        if not log:
            from app.exceptions import RecordNotFoundError

            raise RecordNotFoundError(f"审计日志不存在: {log_id}")

        return AuditLogResponse.model_validate(log)

    async def get_user_audit_logs(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[AuditLogResponse]:
        """获取用户的审计日志

        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            用户审计日志列表
        """
        logger.info(f"获取用户 {user_id} 的审计日志")

        logs = await self.audit_repo.get_by_user_id(user_id=user_id, limit=limit, offset=offset)

        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_latest_audit_logs(self, limit: int = 10) -> list[AuditLogResponse]:
        """获取最新的审计日志

        Args:
            limit: 限制数量

        Returns:
            最新审计日志列表
        """
        logger.info(f"获取最新 {limit} 条审计日志")

        logs = await self.audit_repo.get_latest_logs(limit=limit)
        return [AuditLogResponse.model_validate(log) for log in logs]

    async def query_audit_logs(self, query: AuditLogQuery) -> PagedResponse[AuditLogResponse]:
        """根据条件查询审计日志

        Args:
            query: 查询条件

        Returns:
            分页的审计日志列表
        """
        logger.info(f"查询审计日志: page={query.page}, size={query.size}")

        logs, total_count = await self.audit_repo.query_logs_with_filters(
            user_id=query.user_id,
            action=query.action,
            resource_name=query.resource,
            status=query.status,
            start_date=query.start_date,
            end_date=query.end_date,
            page=query.page,
            page_size=query.size,
            sort_by=query.sort_by,
            sort_desc=query.sort_desc,
            include_deleted=query.include_deleted,
        )

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

        # 使用query_logs_with_filters方法
        logs, _ = await self.audit_repo.query_logs_with_filters(
            action=action, page=offset // limit + 1, page_size=limit
        )

        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_audit_logs_by_resource(
        self, resource: str, limit: int = 50, offset: int = 0
    ) -> list[AuditLogResponse]:
        """根据资源类型获取审计日志

        Args:
            resource: 资源类型
            limit: 限制数量
            offset: 偏移量

        Returns:
            审计日志列表
        """
        logger.info(f"获取资源类型为 {resource} 的审计日志")

        logs, _ = await self.audit_repo.query_logs_with_filters(
            resource_name=resource, page=offset // limit + 1, page_size=limit
        )

        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_failed_operations(self, limit: int = 50, offset: int = 0) -> list[AuditLogResponse]:
        """获取失败的操作日志

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            失败操作日志列表
        """
        logger.info("获取失败的操作日志")

        logs, _ = await self.audit_repo.query_logs_with_filters(
            status="FAILED", page=offset // limit + 1, page_size=limit
        )

        return [AuditLogResponse.model_validate(log) for log in logs]

    async def get_audit_logs_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 50, offset: int = 0
    ) -> list[AuditLogResponse]:
        """根据日期范围获取审计日志

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量

        Returns:
            审计日志列表
        """
        logger.info(f"获取 {start_date} 到 {end_date} 的审计日志")

        logs, _ = await self.audit_repo.query_logs_with_filters(
            start_date=start_date, end_date=end_date, page=offset // limit + 1, page_size=limit
        )

        return [AuditLogResponse.model_validate(log) for log in logs]

    async def count_logs_by_action(self, action: str) -> int:
        """统计指定操作类型的日志数量

        Args:
            action: 操作类型

        Returns:
            日志数量
        """
        _, count = await self.audit_repo.query_logs_with_filters(action=action, page=1, page_size=1)
        return count

    async def count_logs_by_user(self, user_id: UUID) -> int:
        """统计指定用户的日志数量

        Args:
            user_id: 用户ID

        Returns:
            日志数量
        """
        _, count = await self.audit_repo.query_logs_with_filters(user_id=user_id, page=1, page_size=1)
        return count

    async def get_audit_summary(self) -> dict:
        """获取审计日志统计摘要

        Returns:
            统计摘要数据
        """
        logger.info("获取审计日志统计摘要")

        # 获取总数
        _, total_count = await self.audit_repo.query_logs_with_filters(page=1, page_size=1)

        # 获取成功操作数
        _, success_count = await self.audit_repo.query_logs_with_filters(status="SUCCESS", page=1, page_size=1)

        # 获取失败操作数
        _, failed_count = await self.audit_repo.query_logs_with_filters(status="FAILED", page=1, page_size=1)

        # 获取今天的日志数量
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(day=today.day + 1)
        _, today_count = await self.audit_repo.query_logs_with_filters(
            start_date=today, end_date=tomorrow, page=1, page_size=1
        )

        return {
            "total_logs": total_count,
            "success_logs": success_count,
            "failed_logs": failed_count,
            "today_logs": today_count,
            "success_rate": round(success_count / total_count * 100, 2) if total_count > 0 else 0,
        }

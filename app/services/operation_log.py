"""@Author: li.

@Email: lijianqiao2906@live.com
@FileName: operation_log.py
@DateTime: 2025/07/08
@Docs: 操作日志服务层.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from tortoise.expressions import Q
from tortoise.functions import Avg, Count
from tortoise.queryset import QuerySet

from app.core.exceptions import BusinessException
from app.dao.operation_log import OperationLogDAO
from app.dao.user import UserDAO
from app.models.operation_log import OperationLog
from app.schemas.operation_log import (
    OperationLogListRequest,
    OperationLogResponse,
    OperationLogStatisticsRequest,
    OperationLogStatisticsResponse,
)
from app.services.base import BaseService
from app.utils.deps import OperationContext


class OperationLogService(BaseService[OperationLog]):
    """操作日志服务类."""

    def __init__(self) -> None:
        """初始化操作日志服务."""
        super().__init__(OperationLogDAO())
        self.user_dao = UserDAO()

    async def get_logs(
        self,
        query: OperationLogListRequest,
        _operation_context: OperationContext,
    ) -> tuple[list[OperationLogResponse], int]:
        """获取操作日志列表."""
        filters, q_filters = await self._build_filters(query)
        if filters is None:
            return [], 0

        order_by = self._build_order_by(query)
        logs, total = await self.get_paginated_with_related(
            page=query.page,
            page_size=query.page_size,
            order_by=order_by,
            prefetch_related=["user"],
            **filters,
        )

        return self._build_log_responses(logs), total

    async def _build_filters(self, query: OperationLogListRequest) -> tuple[dict[str, Any] | None, list]:
        """构建查询过滤器."""
        filters: dict[str, Any] = {}
        q_filters = []

        # 先处理用户名搜索, 获取用户 ID
        if query.username:
            matching_users = await self.user_dao.search_users(keyword=query.username)
            user_ids = [user.id for user in matching_users]
            if not user_ids:
                return None, []  # 未找到用户, 因此没有日志
            filters["user_id__in"] = user_ids

        if query.keyword:
            q_filters.append(
                Q(module__icontains=query.keyword)
                | Q(action__icontains=query.keyword)
                | Q(path__icontains=query.keyword)
                | Q(ip_address__icontains=query.keyword),
            )

        if query.status == "success":
            filters["response_code__gte"] = 200
            filters["response_code__lt"] = 300
        elif query.status == "fail":
            filters["response_code__gte"] = 400

        if query.start_date:
            filters["created_at__gte"] = query.start_date
        if query.end_date:
            filters["created_at__lte"] = query.end_date + timedelta(days=1)

        if q_filters:
            filters["Q_filter"] = Q(*q_filters, join_type="AND")

        return filters, q_filters

    def _build_order_by(self, query: OperationLogListRequest) -> list[str]:
        """构建排序字段."""
        return [f"{'-' if query.sort_order == 'desc' else ''}{query.sort_by}"] if query.sort_by else ["-created_at"]

    def _build_log_responses(self, logs: list[OperationLog]) -> list[OperationLogResponse]:
        """构建日志响应列表."""
        log_responses = []
        for log in logs:
            log_resp = OperationLogResponse.model_validate(log)
            if log.user:
                log_resp.username = log.user.username
            log_responses.append(log_resp)
        return log_responses

    async def get_statistics(
        self,
        request: OperationLogStatisticsRequest,
        _operation_context: OperationContext,
    ) -> OperationLogStatisticsResponse:
        """获取操作统计."""
        filters: dict[str, Any] = {"created_at__gte": request.start_date, "created_at__lte": request.end_date}
        if request.user_ids:
            filters["user_id__in"] = request.user_ids

        query = self.dao.model.filter(**filters)

        stats: Any = await query.annotate(
            total_operations=Count("id"),
            unique_users=Count("user_id", distinct=True),
            success_operations=Count("id", _filter=Q(response_code__gte=200, response_code__lt=300)),
            failed_operations=Count("id", _filter=Q(response_code__gte=400)),
            avg_response_time=Avg("response_time"),
        ).first()

        if not stats or stats.total_operations == 0:
            return OperationLogStatisticsResponse(data={})

        action_dist = await self._get_grouped_dist(query, "action")
        module_dist = await self._get_grouped_dist(query, "module")

        return OperationLogStatisticsResponse(
            data={
                "total_operations": stats.total_operations,
                "unique_users": stats.unique_users,
                "success_operations": stats.success_operations,
                "failed_operations": stats.failed_operations,
                "avg_response_time": round(stats.avg_response_time, 2) if stats.avg_response_time else 0,
                "action_distribution": action_dist,
                "module_distribution": module_dist,
            },
        )

    async def _get_grouped_dist(self, query: QuerySet[OperationLog], field: str) -> dict:
        """分组分发的帮助程序."""
        dist = await query.group_by(field).annotate(count=Count("id")).values(field, "count")
        return {item[field]: item["count"] for item in dist}

    async def cleanup_logs(self, days: int, _operation_context: OperationContext) -> int:
        """清理指定天数前的旧操作日志(物理删除)."""
        if days <= 0:
            msg = "天数必须为正整数"
            raise BusinessException(msg)
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Fetch log IDs to delete details for
        log_ids_to_delete = await self.dao.model.filter(created_at__lt=cutoff_date).values_list("id", flat=True)
        if not log_ids_to_delete:
            return 0

        return await self.dao.delete_by_filter(id__in=log_ids_to_delete)

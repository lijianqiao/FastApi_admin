"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log.py
@DateTime: 2025/01/01
@Docs: 操作日志数据访问层
"""

from datetime import datetime, timedelta
from uuid import UUID

from app.dao.base import BaseDAO
from app.models.operation_log import OperationLog
from app.utils.logger import logger


class OperationLogDAO(BaseDAO[OperationLog]):
    """操作日志数据访问层"""

    def __init__(self):
        super().__init__(OperationLog)

    async def get_by_user(self, user_id: UUID, limit: int = 50) -> list[OperationLog]:
        """根据用户ID获取操作日志"""
        try:
            return await self.model.filter(user_id=user_id).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"根据用户获取操作日志失败: {e}")
            return []

    async def get_by_module(self, module: str, limit: int = 100) -> list[OperationLog]:
        """根据模块获取操作日志"""
        try:
            return await self.model.filter(module=module).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"根据模块获取操作日志失败: {e}")
            return []

    async def get_by_action(self, action: str, limit: int = 100) -> list[OperationLog]:
        """根据操作类型获取日志"""
        try:
            return await self.model.filter(action=action).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"根据操作类型获取日志失败: {e}")
            return []

    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> list[OperationLog]:
        """根据时间范围获取日志"""
        try:
            return (
                await self.model.filter(created_at__gte=start_date, created_at__lte=end_date)
                .order_by("-created_at")
                .all()
            )
        except Exception as e:
            logger.error(f"根据时间范围获取日志失败: {e}")
            return []

    async def get_error_logs(self, limit: int = 100) -> list[OperationLog]:
        """获取错误日志（响应码>=400）"""
        try:
            return await self.model.filter(response_code__gte=400).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"获取错误日志失败: {e}")
            return []

    async def get_slow_requests(self, threshold_ms: int = 2000, limit: int = 100) -> list[OperationLog]:
        """获取慢请求日志"""
        try:
            return (
                await self.model.filter(response_time__gte=threshold_ms).order_by("-response_time").limit(limit).all()
            )
        except Exception as e:
            logger.error(f"获取慢请求日志失败: {e}")
            return []

    async def get_by_ip(self, ip_address: str, limit: int = 100) -> list[OperationLog]:
        """根据IP地址获取日志"""
        try:
            return await self.model.filter(ip_address=ip_address).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"根据IP获取日志失败: {e}")
            return []

    async def search_logs(
        self,
        user_id: UUID | None = None,
        module: str | None = None,
        action: str | None = None,
        ip_address: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[OperationLog]:
        """搜索操作日志"""
        try:
            filters = {}

            if user_id:
                filters["user_id"] = user_id
            if module:
                filters["module"] = module
            if action:
                filters["action"] = action
            if ip_address:
                filters["ip_address"] = ip_address
            if start_date:
                filters["created_at__gte"] = start_date
            if end_date:
                filters["created_at__lte"] = end_date

            return await self.model.filter(**filters).order_by("-created_at").limit(limit).all()
        except Exception as e:
            logger.error(f"搜索操作日志失败: {e}")
            return []

    async def count_by_user(self, user_id: UUID, days: int = 7) -> int:
        """统计用户最近几天的操作次数"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            return await self.model.filter(user_id=user_id, created_at__gte=cutoff_time).count()
        except Exception as e:
            logger.error(f"统计用户操作次数失败: {e}")
            return 0

    async def count_by_ip(self, ip_address: str, hours: int = 24) -> int:
        """统计IP最近几小时的操作次数"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return await self.model.filter(ip_address=ip_address, created_at__gte=cutoff_time).count()
        except Exception as e:
            logger.error(f"统计IP操作次数失败: {e}")
            return 0

    async def get_operation_stats_by_date_range(self, start_date: datetime, end_date: datetime) -> dict[str, int]:
        """根据日期范围获取操作统计"""
        try:
            # 使用ORM实现统计查询
            logs = await self.model.filter(created_at__gte=start_date, created_at__lte=end_date, is_deleted=False).all()

            stats = {}
            for log in logs:
                stats[log.action] = stats.get(log.action, 0) + 1
            return stats

        except Exception as e:
            logger.error(f"获取操作统计失败: {e}")
            return {}

    # 关联查询优化方法
    async def get_operation_logs_with_details(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[OperationLog], int]:
        """获取操作日志及详情（关联查询优化）"""
        try:
            # 预加载关联的详情记录
            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                select_related=["user"],
                prefetch_related=["detail"],  # 预加载详情
                order_by=["-created_at"],
                is_deleted=False,
            )
        except Exception as e:
            logger.error(f"获取操作日志及详情失败: {e}")
            return [], 0

    async def get_user_operations_optimized(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[OperationLog], int]:
        """获取用户操作日志"""
        try:
            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                select_related=["user"],
                prefetch_related=["detail"],
                order_by=["-created_at"],
                user_id=user_id,
                is_deleted=False,
            )
        except Exception as e:
            logger.error(f"获取用户操作日志失败: {e}")
            return [], 0

    async def get_operations_by_module_optimized(
        self, module: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[OperationLog], int]:
        """根据模块获取操作日志"""
        try:
            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                select_related=["user"],
                prefetch_related=["detail"],
                order_by=["-created_at"],
                module=module,
                is_deleted=False,
            )
        except Exception as e:
            logger.error(f"根据模块获取操作日志失败: {e}")
            return [], 0

    async def get_recent_operations_optimized(self, limit: int = 50) -> list[OperationLog]:
        """获取最近操作记录"""
        try:
            logs = (
                await self.model.filter(is_deleted=False)
                .select_related("user")
                .prefetch_related("detail")
                .order_by("-created_at")
                .limit(limit)
            )
            return list(logs)
        except Exception as e:
            logger.error(f"获取最近操作记录失败: {e}")
            return []

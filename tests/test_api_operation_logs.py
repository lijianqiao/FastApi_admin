"""
@FileName: test_api_operation_logs.py
@Docs: 测试操作日志管理 API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import OperationLog, User

pytestmark = pytest.mark.asyncio


async def test_get_operation_logs(authenticated_client: AsyncClient):
    """测试获取操作日志列表"""
    # 触发一个操作来确保有日志产生
    await authenticated_client.get(f"{settings.API_PREFIX}/v1/users")

    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/operation-logs")
    assert response.status_code == 200
    response_data = response.json()
    # PaginatedResponse直接包含total字段，不需要通过data访问
    assert response_data["total"] >= 1


async def test_get_operation_log_statistics(authenticated_client: AsyncClient):
    """测试获取操作日志统计"""
    await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles") # 产生日志
    # 注意：统计接口需要日期范围
    from datetime import date, timedelta
    today = date.today()
    start_date = today - timedelta(days=1)
    end_date = today + timedelta(days=1)

    response = await authenticated_client.get(
        f"{settings.API_PREFIX}/v1/operation-logs/statistics?start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    # 统计数据在data.data中，因为OperationLogStatisticsResponse包含data字段
    stats = data["data"]
    assert stats["total_operations"] > 0


async def test_cleanup_logs(authenticated_client: AsyncClient):
    """测试清理操作日志"""
    # 该接口会物理删除，所以在一个隔离的测试中进行
    user = await User.filter(is_superuser=True).first()
    from datetime import datetime, timedelta, timezone
    # 创建一个旧的日志
    await OperationLog.create(
        user=user,
        module="test", action="cleanup", path="/", method="DELETE",
        response_code=200, response_time=10, ip_address="127.0.0.1",
        created_at=datetime.now(timezone.utc) - timedelta(days=40)
    )
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/operation-logs/cleanup?days=30")
    assert response.status_code == 200

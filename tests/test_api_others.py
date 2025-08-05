"""
@FileName: test_api_others.py
@Docs: 测试操作日志、管理后台等其他 API 端点
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
    # PaginatedResponse直接包含total字段
    assert response_data["total"] >= 1


async def test_get_dashboard_stats(authenticated_client: AsyncClient):
    """测试获取仪表盘统计数据"""
    # 触发操作以确保有日志
    await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles")

    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/admin/dashboard/stats")

    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert "total_users" in data
    assert data["total_users"] >= 1  # 至少有超级用户
    assert data["today_operations"] > 0

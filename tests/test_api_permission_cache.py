"""
@FileName: test_api_permission_cache.py
@Docs: 测试权限缓存管理 API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import User

pytestmark = pytest.mark.asyncio


async def test_get_cache_stats(authenticated_client: AsyncClient):
    """测试获取缓存统计"""
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/permission-cache/stats")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "backend" in data
    assert "permission_keys" in data


async def test_clear_all_cache(authenticated_client: AsyncClient):
    """测试清除所有缓存"""
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/permission-cache/all")
    assert response.status_code == 200
    assert response.json()["message"] == "所有权限缓存已清除"


async def test_clear_user_cache(authenticated_client: AsyncClient):
    """测试清除用户缓存"""
    user = await User.create(username="cache_user", password_hash="p", phone="13844440000")
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/permission-cache/user/{user.id}")
    assert response.status_code == 200

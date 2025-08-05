"""
@FileName: test_api_admin_dashboard.py
@Docs: 测试管理后台仪表盘 API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import Permission, Role, User

pytestmark = pytest.mark.asyncio


async def test_get_dashboard_stats(authenticated_client: AsyncClient):
    """测试获取仪表盘统计数据"""
    await authenticated_client.get(f"{settings.API_PREFIX}/v1/users") # 产生日志
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/admin/dashboard/stats")
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["total_users"] >= 1
    assert data["today_operations"] > 0


async def test_check_user_permission(authenticated_client: AsyncClient):
    """测试检查用户权限"""
    user = await User.create(username="perm_check_user", password_hash="p", phone="13899999999")
    perm = await Permission.create(permission_name="检查权限", permission_code="perm:check", permission_type="test")
    await user.permissions.add(perm)

    response = await authenticated_client.post(
        f"{settings.API_PREFIX}/v1/admin/permissions/check?user_id={user.id}&permission_code=perm:check"
    )
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["has_permission"] is True


async def test_batch_enable_disable_users(authenticated_client: AsyncClient):
    """测试批量启/禁用用户"""
    user1 = await User.create(username="user_a", password_hash="p", phone="13800001111", is_active=True)
    user2 = await User.create(username="user_b", password_hash="p", phone="13800002222", is_active=True)

    # 批量禁用
    disable_data = [str(user1.id), str(user2.id)]
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/admin/quick-actions/batch-disable-users", json=disable_data)
    assert response.status_code == 200

    # 验证
    u1_after = await User.get(id=user1.id)
    assert u1_after.is_active is False

    # 批量启用
    enable_data = [str(user1.id), str(user2.id)]
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/admin/quick-actions/batch-enable-users", json=enable_data)
    assert response.status_code == 200
    u1_after_enable = await User.get(id=user1.id)
    assert u1_after_enable.is_active is True

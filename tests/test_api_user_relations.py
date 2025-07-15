"""
@FileName: test_api_user_relations.py
@Docs: 测试用户关系管理 API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import Role, User

pytestmark = pytest.mark.asyncio


async def test_batch_assign_user_roles(authenticated_client: AsyncClient):
    """测试批量为用户分配角色"""
    user1 = await User.create(username="batch_user1", password_hash="p", phone="13811110000")
    user2 = await User.create(username="batch_user2", password_hash="p", phone="13822220000")
    role1 = await Role.create(role_name="批量角色1", role_code="batch_role1")
    role2 = await Role.create(role_name="批量角色2", role_code="batch_role2")

    assign_data = {
        "user_ids": [str(user1.id), str(user2.id)],
        "role_ids": [str(role1.id), str(role2.id)],
    }
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/user-relations/batch/users/roles/assign", json=assign_data)
    assert response.status_code == 200

    # 验证
    u1_after = await User.get(id=user1.id).prefetch_related("roles")
    assert len(u1_after.roles) == 2


async def test_get_users_by_role(authenticated_client: AsyncClient):
    """测试根据角色查找用户"""
    user = await User.create(username="role_user_1", password_hash="p", phone="13833330000")
    role = await Role.create(role_name="查找角色", role_code="find_role")
    await user.roles.add(role)

    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/user-relations/roles/{role.id}/users")
    assert response.status_code == 200
    assert len(response.json()) > 0

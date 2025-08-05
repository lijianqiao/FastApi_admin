"""
@FileName: test_api_users.py
@Docs: 测试用户管理 (Users) API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import Permission, Role, User

pytestmark = pytest.mark.asyncio


# --- 辅助函数 ---
async def create_test_user(username="testuser1", phone="13800000011") -> User:
    """辅助函数：创建一个用于测试的普通用户"""
    return await User.create(
        username=username,
        password_hash="testpassword",
        phone=phone,
        is_active=True,
    )


# --- 核心 CRUD 测试 ---
async def test_create_user(authenticated_client: AsyncClient):
    """测试创建用户"""
    user_data = {
        "username": "newuser",
        "password": "newpassword123",
        "phone": "13800000012",
        "nickname": "小新",
    }
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/users", json=user_data)
    assert response.status_code == 201
    response_data = response.json()
    data = response_data["data"]
    assert data["username"] == "newuser"


async def test_get_users(authenticated_client: AsyncClient):
    """测试获取用户列表"""
    await create_test_user()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


async def test_get_user_detail(authenticated_client: AsyncClient):
    """测试获取单个用户详情"""
    user = await create_test_user()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users/{user.id}")
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["id"] == str(user.id)


async def test_update_user(authenticated_client: AsyncClient):
    """测试更新用户信息"""
    user = await create_test_user()
    update_data = {"nickname": "更新后的昵称", "is_active": False, "version": user.version}
    response = await authenticated_client.put(
        f"{settings.API_PREFIX}/v1/users/{user.id}",
        json=update_data,
    )
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["nickname"] == "更新后的昵称"
    assert data["isActive"] is False


async def test_delete_user(authenticated_client: AsyncClient):
    """测试删除用户"""
    user = await create_test_user()
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/users/{user.id}")
    assert response.status_code == 200
    get_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users/{user.id}")
    assert get_response.status_code == 400


# --- 状态和关系测试 ---
async def test_update_user_status(authenticated_client: AsyncClient):
    """测试更新用户状态"""
    user = await create_test_user()
    response = await authenticated_client.put(f"{settings.API_PREFIX}/v1/users/{user.id}/status?is_active=false")
    assert response.status_code == 200

    detail_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users/{user.id}")
    detail_data = detail_response.json()["data"]
    assert detail_data["isActive"] is False


async def test_assign_user_roles_full(authenticated_client: AsyncClient):
    """测试为用户全量分配角色"""
    user = await create_test_user()
    role1 = await Role.create(role_name="角色1", role_code="role1")
    role2 = await Role.create(role_name="角色2", role_code="role2")

    assign_data = {"role_ids": [str(role1.id), str(role2.id)]}
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/users/{user.id}/roles", json=assign_data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert len(data["roles"]) == 2


async def test_add_user_roles_incremental(authenticated_client: AsyncClient):
    """测试为用户增量添加角色"""
    user = await create_test_user()
    role1 = await Role.create(role_name="角色1", role_code="role1")
    await user.roles.add(role1)

    role2 = await Role.create(role_name="角色2", role_code="role2")
    add_data = {"role_ids": [str(role2.id)]}
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/users/{user.id}/roles/add", json=add_data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert len(data["roles"]) == 2


async def test_remove_user_roles(authenticated_client: AsyncClient):
    """测试移除用户角色"""
    user = await create_test_user()
    role1 = await Role.create(role_name="角色1", role_code="role1")
    role2 = await Role.create(role_name="角色2", role_code="role2")
    await user.roles.add(role1, role2)

    remove_data = {"role_ids": [str(role1.id)]}
    response = await authenticated_client.request(
        "DELETE", f"{settings.API_PREFIX}/v1/users/{user.id}/roles/remove", json=remove_data
    )
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert len(data["roles"]) == 1
    assert data["roles"][0]["roleCode"] == "role2"


async def test_get_user_roles(authenticated_client: AsyncClient):
    """测试获取用户的角色列表"""
    user = await create_test_user()
    role = await Role.create(role_name="角色1", role_code="role1")
    await user.roles.add(role)

    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users/{user.id}/roles")
    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert len(data) == 1
    assert data[0]["role_code"] == "role1"


async def test_assign_user_permissions(authenticated_client: AsyncClient):
    """测试为用户分配直接权限"""
    user = await create_test_user()
    perm = await Permission.create(permission_name="直接权限", permission_code="direct:perm", permission_type="test")

    assign_data = {"permission_ids": [str(perm.id)]}
    response = await authenticated_client.post(
        f"{settings.API_PREFIX}/v1/users/{user.id}/permissions", json=assign_data
    )
    assert response.status_code == 200

    # 验证权限是否真的被添加
    detail_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/users/{user.id}/permissions")
    assert len(detail_response.json()) > 0

"""
@FileName: test_api_roles.py
@Docs: 测试角色管理 (Roles) API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import Permission, Role, User

pytestmark = pytest.mark.asyncio


# --- 辅助函数 ---
async def create_test_role(code="test_role") -> Role:
    return await Role.create(role_name=f"角色_{code}", role_code=code)


# --- 核心 CRUD 测试 ---
async def test_create_role(authenticated_client: AsyncClient):
    """测试创建角色"""
    role_data = {"role_name": "新角色", "role_code": "new_role"}
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/roles", json=role_data)
    assert response.status_code == 201
    assert response.json()["roleCode"] == "new_role"


async def test_get_roles(authenticated_client: AsyncClient):
    """测试获取角色列表"""
    await create_test_role()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


async def test_get_role_detail(authenticated_client: AsyncClient):
    """测试获取角色详情"""
    role = await create_test_role()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles/{role.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(role.id)


async def test_update_role(authenticated_client: AsyncClient):
    """测试更新角色"""
    role = await create_test_role()
    update_data = {"description": "更新后的描述", "version": role.version}
    response = await authenticated_client.put(f"{settings.API_PREFIX}/v1/roles/{role.id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "更新后的描述"


async def test_delete_role(authenticated_client: AsyncClient):
    """测试删除角色"""
    role = await create_test_role()
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/roles/{role.id}")
    assert response.status_code == 200
    get_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles/{role.id}")
    assert get_response.status_code == 400


# --- 状态和关系测试 ---
async def test_update_role_status(authenticated_client: AsyncClient):
    """测试更新角色状态"""
    role = await create_test_role()
    response = await authenticated_client.put(f"{settings.API_PREFIX}/v1/roles/{role.id}/status?is_active=false")
    assert response.status_code == 200
    detail_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles/{role.id}")
    assert detail_response.json()["isActive"] is False


async def test_assign_permissions_to_role_full(authenticated_client: AsyncClient):
    """测试为角色全量分配权限"""
    role = await create_test_role()
    perm1 = await Permission.create(permission_name="权限1", permission_code="p1", permission_type="test")
    perm2 = await Permission.create(permission_name="权限2", permission_code="p2", permission_type="test")
    assign_data = {"permission_ids": [str(perm1.id), str(perm2.id)]}
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/roles/{role.id}/permissions", json=assign_data)
    assert response.status_code == 200
    assert len(response.json()["permissions"]) == 2


async def test_add_permissions_to_role_incremental(authenticated_client: AsyncClient):
    """测试为角色增量添加权限"""
    role = await create_test_role()
    perm1 = await Permission.create(permission_name="权限1", permission_code="p1", permission_type="test")
    await role.permissions.add(perm1)
    perm2 = await Permission.create(permission_name="权限2", permission_code="p2", permission_type="test")
    add_data = {"permission_ids": [str(perm2.id)]}
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/roles/{role.id}/permissions/add", json=add_data)
    assert response.status_code == 200
    assert len(response.json()["permissions"]) == 2


async def test_remove_permissions_from_role(authenticated_client: AsyncClient):
    """测试移除角色权限"""
    role = await create_test_role()
    perm1 = await Permission.create(permission_name="权限1", permission_code="p1", permission_type="test")
    perm2 = await Permission.create(permission_name="权限2", permission_code="p2", permission_type="test")
    await role.permissions.add(perm1, perm2)
    remove_data = {"permission_ids": [str(perm1.id)]}
    response = await authenticated_client.request("DELETE", f"{settings.API_PREFIX}/v1/roles/{role.id}/permissions/remove", json=remove_data)
    assert response.status_code == 200
    assert len(response.json()["permissions"]) == 1


async def test_get_role_permissions(authenticated_client: AsyncClient):
    """测试获取角色的权限列表"""
    role = await create_test_role()
    perm = await Permission.create(permission_name="权限1", permission_code="p1", permission_type="test")
    await role.permissions.add(perm)
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/roles/{role.id}/permissions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["permission_code"] == "p1"

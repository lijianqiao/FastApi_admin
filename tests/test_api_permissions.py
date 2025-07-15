"""
@FileName: test_api_permissions.py
@Docs: 测试权限管理 (Permissions) API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models import Permission

pytestmark = pytest.mark.asyncio


# --- 辅助函数 ---
async def create_test_permission(code="test:perm", name="测试权限") -> Permission:
    return await Permission.create(
        permission_name=name,
        permission_code=code,
        permission_type="module",
    )


# --- 核心 CRUD 测试 ---
async def test_create_permission(authenticated_client: AsyncClient):
    """测试创建权限"""
    perm_data = {
        "permission_name": "新权限",
        "permission_code": "new:permission",
        "permission_type": "module",
    }
    response = await authenticated_client.post(f"{settings.API_PREFIX}/v1/permissions", json=perm_data)
    assert response.status_code == 201
    assert response.json()["permissionCode"] == "new:permission"


async def test_get_permissions(authenticated_client: AsyncClient):
    """测试获取权限列表"""
    await create_test_permission()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/permissions")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


async def test_get_permission_detail(authenticated_client: AsyncClient):
    """测试获取权限详情"""
    perm = await create_test_permission()
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/permissions/{perm.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(perm.id)


async def test_update_permission(authenticated_client: AsyncClient):
    """测试更新权限"""
    perm = await create_test_permission()
    update_data = {"description": "更新后的描述", "version": perm.version}
    response = await authenticated_client.put(f"{settings.API_PREFIX}/v1/permissions/{perm.id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "更新后的描述"


async def test_delete_permission(authenticated_client: AsyncClient):
    """测试删除权限"""
    perm = await create_test_permission()
    response = await authenticated_client.delete(f"{settings.API_PREFIX}/v1/permissions/{perm.id}")
    assert response.status_code == 200
    get_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/permissions/{perm.id}")
    assert get_response.status_code == 400

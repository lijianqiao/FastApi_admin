"""
@FileName: test_api_auth.py
@Docs: 测试认证管理 (Auth) API 端点
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import hash_password
from app.models import User

# 将所有测试标记为异步测试
pytestmark = pytest.mark.asyncio


async def test_login(client: AsyncClient):
    """测试用户登录接口"""
    # 在测试函数内部创建所需数据，确保隔离
    await User.create(
        username="testuser",
        password_hash=hash_password("testpassword"),
        phone="13800000001",
        is_active=True,
    )

    response = await client.post(
        f"{settings.API_PREFIX}/v1/auth/login",
        json={"username": "testuser", "password": "testpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


async def test_login_wrong_credentials(client: AsyncClient):
    """测试使用错误凭证登录"""
    response = await client.post(
        f"{settings.API_PREFIX}/v1/auth/login",
        json={"username": "wronguser", "password": "wrongpassword"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["code"] == 404


async def test_get_profile(authenticated_client: AsyncClient):
    """测试获取当前用户信息接口"""
    response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/auth/profile")

    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["username"] == settings.SUPERUSER_USERNAME
    assert data["isSuperuser"] is True


async def test_update_profile(authenticated_client: AsyncClient):
    """测试更新当前用户信息接口"""
    profile_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/auth/profile")
    current_version = profile_response.json()["data"]["version"]

    update_data = {
        "nickname": "新的昵称",
        "bio": "这是我的新简介",
        "version": current_version,
    }

    response = await authenticated_client.put(
        f"{settings.API_PREFIX}/v1/auth/profile",
        json=update_data,
    )

    assert response.status_code == 200
    response_data = response.json()
    data = response_data["data"]
    assert data["nickname"] == "新的昵称"

    profile_response_after = await authenticated_client.get(f"{settings.API_PREFIX}/v1/auth/profile")
    after_data = profile_response_after.json()["data"]
    assert after_data["nickname"] == "新的昵称"
    assert after_data["version"] == current_version + 1


async def test_change_password(authenticated_client: AsyncClient):
    """测试修改密码接口"""
    profile_response = await authenticated_client.get(f"{settings.API_PREFIX}/v1/auth/profile")
    current_version = profile_response.json()["data"]["version"]

    password_data = {
        "old_password": settings.SUPERUSER_PASSWORD,
        "new_password": "new_strong_password",
        "confirm_password": "new_strong_password",
        "version": current_version,
    }

    response = await authenticated_client.put(
        f"{settings.API_PREFIX}/v1/auth/password",
        json=password_data,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "成功"

    # 使用同一个客户端（现在是未认证状态）和新密码尝试重新登录
    authenticated_client.headers.pop("Authorization") # 移除旧令牌
    login_response = await authenticated_client.post(
        f"{settings.API_PREFIX}/v1/auth/login",
        json={"username": settings.SUPERUSER_USERNAME, "password": "new_strong_password"},
    )
    assert login_response.status_code == 200

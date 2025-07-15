"""
@FileName: conftest.py
@Docs: Pytest 配置文件，提供测试固件 (fixtures)
"""

# 重要提示：这必须在任何应用程序代码导入之前放在最顶部。
import os
os.environ["ENVIRONMENT"] = "testing"

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import httpx
from tortoise import Tortoise

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.main import app as main_app
from app.models import User

# 定义测试数据库配置
TEST_DB_CONFIG = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """为整个测试会话创建一个事件循环。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def initialize_database() -> AsyncGenerator[None, None]:
    """
    为每个测试函数初始化一个全新的、隔离的内存数据库。
    `autouse=True` 确保它在每个测试函数运行之前自动执行。
    """
    await Tortoise.init(config=TEST_DB_CONFIG)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """提供一个标准的、未经认证的 HTTPX 客户端。"""
    # 由于 initialize_database 是 autouse=True，所以这里无需显式依赖
    transport = httpx.ASGITransport(app=main_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def authenticated_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    提供一个已认证的客户端。
    数据库已由 `initialize_database` fixture 自动清理和准备就绪。
    """
    superuser = await User.create(
        username=settings.SUPERUSER_USERNAME,
        password_hash=hash_password(settings.SUPERUSER_PASSWORD),
        phone=settings.SUPERUSER_PHONE,
        is_active=True,
        is_superuser=True,
    )

    token_payload = {"sub": str(superuser.id)}
    access_token = create_access_token(data=token_payload)
    client.headers["Authorization"] = f"Bearer {access_token}"

    return client
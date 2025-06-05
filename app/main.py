"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: app.py
@DateTime: 2025/05/29 19:41:07
@Docs: FastAPI 应用程序入口点
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.config import settings
from app.db.session import database_manager
from app.metrics import setup_metrics
from app.middleware import setup_middlewares


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 应用启动时检查数据库连接
        connected = await database_manager.check_connection()
        if not connected:
            raise RuntimeError("数据库连接失败，应用无法启动")
        # 启动限流redis
        yield
        # 应用关闭时关闭数据库连接
        await database_manager.close()

    app = FastAPI(
        title=settings.app_name,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        version=settings.app_version,
        description=settings.app_description,
        debug=settings.debug,
        contact={
            "name": "li",
            "email": "lijianqiao2906@live.com",
            "url": "https://gitee.com/lijianqiao",
        },
        lifespan=lifespan,
    )

    # 设置所有中间件（包括CORS、限流、审计、错误处理等）
    setup_middlewares(app)

    # 设置 Prometheus 指标
    setup_metrics(app)

    # 包含 API 路由
    app.include_router(api_router)

    return app


app = create_app()  # 如果您全局实例化应用程序，请确保设置指标和错误处理程序。

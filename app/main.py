"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: app.py
@DateTime: 2025/05/29 19:41:07
@Docs: FastAPI 应用程序入口点
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router_v1
from app.config import settings
from app.core.redis import redis_manager
from app.metrics import setup_metrics
from app.middleware import setup_middlewares


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行
    # 例如：初始化数据库连接池，Redis连接等
    # await sqlalchemy_config.create_engine() # 如果需要
    # await redis_manager.get_client() # 如果需要在启动时就初始化连接池
    yield
    # 应用关闭时执行
    await redis_manager.close()
    # await sqlalchemy_config.dispose_engine() # 如果需要


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # 设置所有中间件（包括CORS、限流、审计、错误处理等）
    setup_middlewares(app)

    # 设置 Prometheus 指标
    setup_metrics(app)

    # 包含 API 路由
    app.include_router(api_router_v1, prefix=settings.API_V1_STR)

    return app


app = create_app()  # 如果您全局实例化应用程序，请确保设置指标和错误处理程序。

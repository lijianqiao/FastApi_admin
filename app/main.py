"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: app.py
@DateTime: 2025/05/29 19:41:07
@Docs: FastAPI 应用程序入口点
"""

from fastapi import FastAPI

from app.config import settings
from app.metrics import setup_metrics
from app.middleware import setup_middlewares


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.app_name,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    # 设置所有中间件（包括CORS、限流、审计、错误处理等）
    setup_middlewares(app)

    # 设置 Prometheus 指标
    setup_metrics(app)

    # 包含 API 路由
    # app.include_router(api_router_v1, prefix=settings.api_v1_prefix, tags=["v1"])

    return app


app = create_app()  # 如果您全局实例化应用程序，请确保设置指标和错误处理程序。

"""
-*- coding: utf-8 -*-
@Author: li
@ProjectName: netmon
@Email: lijianqiao2906@live.com
@FileName: main.py
@DateTime: 2025/03/08 04:50:00
@Docs: 应用程序入口
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.events import lifespan
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middlewares
from app.utils.metrics import metrics_collector


def register_routes(app: FastAPI) -> None:
    """注册API路由"""
    from app.api import api_router

    app.include_router(api_router, prefix=settings.API_PREFIX)


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=f"{settings.API_PREFIX}/docs" if settings.ENABLE_DOCS else None,
        redoc_url=f"{settings.API_PREFIX}/redoc" if settings.ENABLE_DOCS else None,
        openapi_url=f"{settings.API_PREFIX}/openapi.json" if settings.ENABLE_DOCS else None,
        swagger_ui_oauth2_redirect_url=f"{settings.API_PREFIX}/docs/oauth2-redirect",
        swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": True},
    )

    # 中间件与异常处理
    setup_middlewares(app)
    setup_exception_handlers(app)

    # 路由
    register_routes(app)

    # 根路由（可选）
    @app.get("/", tags=["系统"])
    async def root():
        """根路由"""
        return {"message": "欢迎来到网络自动化管理平台系统!"}

    # Prometheus 指标暴露
    if settings.ENABLE_METRICS:

        @app.get(settings.METRICS_PATH, include_in_schema=False)
        async def metrics():
            body, content_type = metrics_collector.prometheus_exposition()
            return PlainTextResponse(body, media_type=content_type)

    return app


# 供 ASGI 服务器加载
app = create_app()

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
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import settings
from app.core.events import lifespan
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middlewares


def create_app() -> FastAPI:
    """创建FastAPI应用实例

    Returns:
        FastAPI: FastAPI应用实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=f"{settings.API_PREFIX}/docs" if settings.ENABLE_DOCS else None,
        redoc_url=f"{settings.API_PREFIX}/redoc" if settings.ENABLE_DOCS else None,
        openapi_url=f"{settings.API_PREFIX}/openapi.json" if settings.ENABLE_DOCS else None,
        # 配置 Swagger UI 的 OAuth2 认证
        swagger_ui_oauth2_redirect_url=f"{settings.API_PREFIX}/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )

    # 设置中间件
    setup_middlewares(app)

    # 设置异常处理器
    setup_exception_handlers(app)

    # 注册路由
    register_routes(app)

    # 注册Tortoise ORM
    register_tortoise_orm(app)

    return app


def register_routes(app: FastAPI) -> None:
    """注册API路由

    Args:
        app (FastAPI): FastAPI应用实例
    """
    # 导入路由模块
    from app.api import api_router

    # 注册主路由
    app.include_router(api_router, prefix=settings.API_PREFIX)


def register_tortoise_orm(app: FastAPI) -> None:
    """注册Tortoise ORM

    Args:
        app (FastAPI): FastAPI应用实例
    """
    register_tortoise(
        app,
        config=settings.TORTOISE_ORM_CONFIG,
        generate_schemas=False,  # 不自动生成数据库结构，使用Aerich进行迁移
    )


# 创建FastAPI应用实例
app = create_app()


# 根路由
@app.get("/", tags=["系统"])
async def root():
    """根路由"""
    return {"message": "Welcome to the Fastapi Admin Template API!"}

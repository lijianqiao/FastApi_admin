"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/05
@Docs: API路由初始化
"""

from datetime import datetime

from fastapi import APIRouter

from app.api.v1 import v1_router
from app.core.config import settings

# 创建主路由
api_router = APIRouter()

# 注册版本路由
api_router.include_router(v1_router, prefix="/v1")

# 这里可以添加其他版本的路由
# api_router.include_router(v2_router, prefix="/v2")


# 健康检查路由
@api_router.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(),
    }

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/05
@Docs: API路由初始化
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.v1 import v1_router
from app.core.config import settings
from app.models.user import User
from app.utils.deps import get_current_active_user

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


# 监控指标路由
@api_router.get("/metrics", tags=["监控"])
async def get_metrics(_: User = Depends(get_current_active_user)):
    """获取应用监控指标"""
    if not settings.ENABLE_METRICS:
        return {"error": "监控功能未启用"}

    try:
        from app.utils.metrics import get_system_metrics, metrics_collector

        app_metrics = metrics_collector.get_metrics()
        system_metrics = get_system_metrics()

        return {
            "timestamp": time.time(),
            "application": app_metrics,
            "system": system_metrics,
        }
    except ImportError:
        return {"error": "监控模块未安装"}

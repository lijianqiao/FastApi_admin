"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/05/29 19:39:42
@Docs: API路由总入口 - 管理所有API版本
"""

from fastapi import APIRouter

from app.api.v1 import api_router as v1_router

# 创建API总路由
api_router = APIRouter(prefix="/api")

# 注册各个版本的API路由
api_router.include_router(v1_router)

# 可以在这里添加其他版本的路由
# api_router.include_router(v2_router)

# 导出路由以供主应用使用
__all__ = ["api_router"]

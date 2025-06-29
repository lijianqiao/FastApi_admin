"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/05/29 19:39:42
@Docs: API v1版本路由注册
"""

from fastapi import APIRouter

from app.api.v1.endpoints import audit_logs, auth, permissions, roles, users

# 创建v1版本的主路由
api_router = APIRouter(prefix="/v1")

# 注册各个功能模块的路由
api_router.include_router(audit_logs.router)
api_router.include_router(auth.router)
api_router.include_router(permissions.router)
api_router.include_router(roles.router)
api_router.include_router(users.router)

# 导出路由以供主应用使用
__all__ = ["api_router"]

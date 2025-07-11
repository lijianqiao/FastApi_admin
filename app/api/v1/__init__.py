"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/07/08
@Docs: API v1 路由注册
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin_dashboard,
    admin_routes,
    auth,
    operation_logs,
    permission_cache,
    permissions,
    roles,
    user_relations,
    users,
)

# 创建 API v1 路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, tags=["认证管理"])
api_router.include_router(users.router, tags=["用户管理"])
api_router.include_router(roles.router, tags=["角色管理"])
api_router.include_router(permissions.router, tags=["权限管理"])
api_router.include_router(operation_logs.router, tags=["操作日志管理"])
api_router.include_router(user_relations.router, tags=["用户关系管理"])
api_router.include_router(admin_dashboard.router, tags=["后台管理仪表板"])
api_router.include_router(admin_routes.admin_router, tags=["管理员专用"])
api_router.include_router(permission_cache.router, tags=["权限缓存管理"])

# 保持向后兼容
v1_router = api_router

__all__ = ["api_router", "v1_router"]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dashboard.py
@DateTime: 2025/07/10 23:45:24
@Docs:
"""

from uuid import UUID

from pydantic import BaseModel


# 响应模型
class DashboardStats(BaseModel):
    """仪表板统计数据"""

    total_users: int
    total_roles: int
    total_permissions: int
    today_operations: int


class UserPermissionCheck(BaseModel):
    """用户权限检查结果"""

    user_id: UUID
    username: str
    permission_code: str
    has_permission: bool
    permission_source: str | None


# 请求模型
class BatchUserRoleRequest(BaseModel):
    """批量用户角色操作请求"""

    user_ids: list[UUID]
    role_ids: list[UUID]


class BatchUserPermissionRequest(BaseModel):
    """批量用户权限操作请求"""

    user_ids: list[UUID]
    permission_ids: list[UUID]


class UserRolePermissionSummary(BaseModel):
    """用户角色权限汇总"""

    user_id: UUID
    username: str
    roles: list[dict]
    direct_permissions: list[dict]
    total_permissions: list[dict]

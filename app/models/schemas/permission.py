"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/06/02 02:32:03
@Docs: 权限相关的 Pydantic 模式

定义权限 API 请求和响应的数据模型
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """权限基础模式"""

    name: str = Field(..., min_length=2, max_length=100, description="权限名称")
    code: str = Field(..., min_length=2, max_length=100, description="权限代码")
    resource: str = Field(..., min_length=2, max_length=100, description="资源类型")
    action: str = Field(..., min_length=2, max_length=50, description="操作类型")
    description: str | None = Field(None, description="权限描述")
    method: str | None = Field(None, max_length=10, description="HTTP方法")
    path: str | None = Field(None, max_length=255, description="API路径")
    category: str | None = Field(None, max_length=50, description="权限分类")
    sort_order: int = Field(0, description="排序顺序")


class PermissionCreate(PermissionBase):
    """创建权限模式"""

    pass


class PermissionUpdate(BaseModel):
    """更新权限模式"""

    name: str | None = Field(None, min_length=2, max_length=100, description="权限名称")
    description: str | None = Field(None, description="权限描述")
    method: str | None = Field(None, max_length=10, description="HTTP方法")
    path: str | None = Field(None, max_length=255, description="API路径")
    category: str | None = Field(None, max_length=50, description="权限分类")
    sort_order: int | None = Field(None, description="排序顺序")


class PermissionResponse(PermissionBase):
    """权限响应模式"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="权限ID")
    is_system: bool = Field(..., description="是否系统权限")
    is_deleted: bool = Field(..., description="是否已删除")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class PermissionListResponse(BaseModel):
    """权限列表响应模式"""

    permissions: list[PermissionResponse] = Field(..., description="权限列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class PermissionGroupResponse(BaseModel):
    """权限分组响应模式"""

    category: str = Field(..., description="权限分类")
    permissions: list[PermissionResponse] = Field(..., description="权限列表")


class PermissionBatchDelete(BaseModel):
    """批量删除权限模式"""

    permission_ids: list[UUID] = Field(..., description="权限ID列表")

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/06/02 02:32:03
@Docs: 角色相关的 Pydantic 模式

定义角色 API 请求和响应的数据模型
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """角色基础模式"""

    name: str = Field(..., min_length=2, max_length=100, description="角色名称")
    code: str = Field(..., min_length=2, max_length=50, description="角色代码")
    description: str | None = Field(None, description="角色描述")
    level: int = Field(0, ge=0, le=999, description="角色等级")
    sort_order: int = Field(0, description="排序顺序")


class RoleCreate(RoleBase):
    """创建角色模式"""

    pass


class RoleUpdate(BaseModel):
    """更新角色模式"""

    name: str | None = Field(None, min_length=2, max_length=100, description="角色名称")
    description: str | None = Field(None, description="角色描述")
    level: int | None = Field(None, ge=0, le=999, description="角色等级")
    sort_order: int | None = Field(None, description="排序顺序")


class RoleResponse(RoleBase):
    """角色响应模式"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="角色ID")
    is_active: bool = Field(..., description="是否激活")
    is_system: bool = Field(..., description="是否系统角色")
    is_deleted: bool = Field(..., description="是否已删除")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class RoleDetailResponse(RoleResponse):
    """角色详细信息响应模式"""

    permissions: list["PermissionResponse"] = Field(default_factory=list, description="角色权限列表")


class RoleListResponse(BaseModel):
    """角色列表响应模式"""

    roles: list[RoleResponse] = Field(..., description="角色列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class RoleStatusUpdate(BaseModel):
    """角色状态更新模式"""

    is_active: bool = Field(..., description="是否激活")


class RolePermissionAssignment(BaseModel):
    """角色权限分配模式"""

    permission_ids: list[UUID] = Field(..., description="权限ID列表")


# 避免循环导入
from .permission import PermissionResponse

RoleDetailResponse.model_rebuild()

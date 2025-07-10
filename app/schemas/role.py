"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/01/01
@Docs: 角色管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import (
    ListQueryRequest,
    ORMBase,
    PaginatedResponse,
)
from app.schemas.permission import PermissionResponse
from app.schemas.types import ObjectUUID


class RoleBase(ORMBase):
    """角色基础字段"""

    role_name: str = Field(description="角色名称", min_length=2, max_length=50)
    role_code: str = Field(description="角色编码", min_length=2, max_length=50)
    description: str | None = Field(default=None, description="角色描述", max_length=200)
    is_active: bool = Field(default=True, description="是否激活")


class RoleCreateRequest(BaseModel):
    """创建角色请求"""

    role_name: str = Field(description="角色名称", min_length=2, max_length=50)
    role_code: str = Field(description="角色编码", min_length=2, max_length=50)
    description: str | None = Field(default=None, description="角色描述", max_length=200)


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""

    role_name: str | None = Field(default=None, description="角色名称", min_length=2, max_length=50)
    description: str | None = Field(default=None, description="角色描述", max_length=200)
    is_active: bool | None = Field(default=None, description="是否激活")
    version: int | None = Field(default=None, description="数据版本号，用于乐观锁")


class RoleResponse(RoleBase):
    """角色响应（用于列表）"""

    user_count: int = Field(default=0, description="关联的用户数量")


class RoleDetailResponse(RoleBase):
    """角色详情响应"""

    permissions: list[PermissionResponse] = Field(default_factory=list, description="关联的权限列表")


class RoleListRequest(ListQueryRequest):
    """角色列表查询请求"""

    role_code: str | None = Field(default=None, description="角色编码筛选")
    is_active: bool | None = Field(default=None, description="激活状态筛选")


class RoleListResponse(PaginatedResponse[RoleResponse]):
    """角色列表响应"""

    pass


class RolePermissionAssignRequest(BaseModel):
    """为角色分配权限的请求"""

    permission_ids: list[ObjectUUID] = Field(description="权限ID列表")

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/01/01
@Docs: 用户管理相关的Pydantic模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse, ListQueryRequest, ORMBase, PaginatedResponse
from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleResponse
from app.schemas.types import ObjectUUID


class UserBase(ORMBase):
    """用户基础字段"""

    username: str = Field(description="用户名", min_length=3, max_length=50)
    phone: str | None = Field(description="手机号", max_length=20)
    nickname: str | None = Field(default=None, description="昵称", max_length=100)
    avatar_url: str | None = Field(default=None, description="头像URL", max_length=500)
    bio: str | None = Field(default=None, description="个人简介")
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")


class UserCreateRequest(BaseModel):
    """创建用户请求"""

    username: str = Field(description="用户名", min_length=3, max_length=50)
    password: str = Field(description="密码", min_length=6, max_length=128)
    phone: str | None = Field(description="手机号", max_length=20)
    nickname: str | None = Field(default=None, description="昵称", max_length=100)
    # 创建时可选分配角色
    role_ids: list[ObjectUUID] = Field(default_factory=list, description="角色ID列表")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""

    phone: str | None = Field(default=None, description="手机号", max_length=20)
    nickname: str | None = Field(default=None, description="昵称", max_length=100)
    avatar_url: str | None = Field(default=None, description="头像URL", max_length=500)
    bio: str | None = Field(default=None, description="个人简介")
    is_active: bool | None = Field(default=None, description="是否激活")


class UserResponse(UserBase):
    """用户标准响应"""

    last_login_at: datetime | None = Field(description="最后登录时间")


class UserDetailResponse(UserResponse):
    """用户详情响应（包含完整关联信息）"""

    roles: list[RoleResponse] = Field(default_factory=list, description="关联的角色列表")
    permissions: list[PermissionResponse] = Field(
        default_factory=list, description="用户拥有的所有权限（包含角色继承）"
    )


class UserListRequest(ListQueryRequest):
    """用户列表查询请求"""

    is_superuser: bool | None = Field(default=None, description="是否超管筛选")
    role_code: str | None = Field(default=None, description="角色筛选")


class UserListResponse(PaginatedResponse[UserResponse]):
    """用户列表响应"""

    pass


class UserDetailResponseWrapper(BaseResponse[UserDetailResponse]):
    """用户详情响应包装"""

    pass


class UserAssignRolesRequest(BaseModel):
    """为用户分配角色请求"""

    role_ids: list[ObjectUUID] = Field(description="角色ID列表")


class UserAssignPermissionsRequest(BaseModel):
    """为用户分配直接权限请求"""

    permission_ids: list[ObjectUUID] = Field(description="权限ID列表")

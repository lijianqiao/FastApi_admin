"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/06/02 02:32:03
@Docs: 用户相关的 Pydantic 模式

定义用户 API 请求和响应的数据模型
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模式"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str | None = Field(None, max_length=100, description="全名")
    phone: str | None = Field(None, max_length=20, description="手机号")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")


class UserCreate(UserBase):
    """创建用户模式"""

    password: str = Field(..., min_length=8, max_length=100, description="密码")


class UserUpdate(BaseModel):
    """更新用户模式"""

    full_name: str | None = Field(None, max_length=100, description="全名")
    phone: str | None = Field(None, max_length=20, description="手机号")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")


class UserPasswordChange(BaseModel):
    """修改密码模式"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")


class UserLogin(BaseModel):
    """用户登录模式"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模式"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    email_verified: bool = Field(..., description="邮箱是否验证")
    phone_verified: bool = Field(..., description="手机号是否验证")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UserDetailResponse(UserResponse):
    """用户详细信息响应模式"""

    roles: list["RoleResponse"] = Field(default_factory=list, description="用户角色列表")


class UserListResponse(BaseModel):
    """用户列表响应模式"""

    users: list[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class UserStatusUpdate(BaseModel):
    """用户状态更新模式"""

    is_active: bool = Field(..., description="是否激活")


class UserRoleAssignment(BaseModel):
    """用户角色分配模式"""

    role_ids: list[UUID] = Field(..., description="角色ID列表")


# 避免循环导入
from .role import RoleResponse

UserDetailResponse.model_rebuild()

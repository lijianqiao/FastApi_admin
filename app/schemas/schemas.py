"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: schemas.py
@DateTime: 2025/06/02 02:32:03
@Docs: Pydantic v2 校验模型 - 现代后台管理系统最优设计
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")

# ===================== 基础模型 =====================


class BaseSchema(BaseModel):
    """基础模式类"""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=True,
    )


class TimestampMixin(BaseModel):
    """时间戳混入类"""

    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class APIResponse(BaseSchema, Generic[T]):
    """通用API响应模型"""

    code: int = Field(200, description="状态码")
    message: str = Field("操作成功", description="提示信息")
    data: T | None = Field(None, description="数据")
    success: bool = Field(True, description="是否成功")


class PagedResponse(BaseSchema, Generic[T]):
    """分页响应模型"""

    total: int = Field(..., description="总数", ge=0)
    page: int = Field(..., description="当前页", ge=1)
    size: int = Field(..., description="每页大小", ge=1, le=100)
    pages: int = Field(..., description="总页数", ge=0)
    items: list[T] = Field(..., description="数据列表")


# ===================== 查询相关模型 =====================


class BaseQuery(BaseSchema):
    """基础查询模型"""

    page: int = Field(1, description="页码", ge=1)
    size: int = Field(20, description="每页大小", ge=1, le=100)
    sort_by: str | None = Field(None, description="排序字段")
    sort_desc: bool = Field(False, description="是否降序")
    include_deleted: bool = Field(False, description="是否包含已删除数据")


class SearchQuery(BaseQuery):
    """搜索查询模型"""

    keyword: str | None = Field(None, description="搜索关键词", max_length=100)


class UserQuery(BaseQuery):
    """用户查询模型"""

    keyword: str | None = Field(None, description="搜索关键词（用户名/邮箱/昵称/手机号）")
    is_active: bool | None = Field(None, description="是否激活")
    is_superuser: bool | None = Field(None, description="是否超级用户")


class RoleQuery(BaseQuery):
    """角色查询模型"""

    keyword: str | None = Field(None, description="搜索关键词（角色名/描述）")
    is_active: bool | None = Field(None, description="是否激活")


class AuditLogQuery(BaseQuery):
    """审计日志查询模型"""

    user_id: UUID | None = Field(None, description="用户ID")
    action: str | None = Field(None, description="操作类型")
    resource: str | None = Field(None, description="资源类型")
    status: str | None = Field(None, description="操作状态")
    start_date: datetime | None = Field(None, description="开始时间")
    end_date: datetime | None = Field(None, description="结束时间")


# ===================== 批量操作模型 =====================


class BatchDeleteRequest(BaseSchema):
    """批量删除请求模型"""

    ids: list[UUID] = Field(..., description="要删除的ID列表", min_length=1)
    hard_delete: bool = Field(False, description="是否硬删除")


class BatchUpdateRequest(BaseSchema):
    """批量更新请求模型"""

    ids: list[UUID] = Field(..., description="要更新的ID列表", min_length=1)
    data: dict[str, Any] = Field(..., description="更新数据")


class BatchOperationResponse(BaseSchema):
    """批量操作响应模型"""

    success_count: int = Field(..., description="成功数量", ge=0)
    failed_count: int = Field(..., description="失败数量", ge=0)
    total_count: int = Field(..., description="总数量", ge=0)
    failed_ids: list[UUID] = Field(default_factory=list, description="失败的ID列表")


# ===================== 用户相关模型 =====================


class UserBase(BaseSchema):
    """用户基础模型"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    phone: str | None = Field(None, max_length=20, description="手机号")
    nickname: str = Field(..., max_length=100, description="昵称")
    is_active: bool = Field(True, description="是否激活")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.replace("_", "").isalnum():
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """验证手机号格式"""
        if v is None:
            return v
        # 简单的手机号验证
        if not v.isdigit() or len(v) != 11:
            raise ValueError("请输入11位手机号")
        return v


class UserCreate(UserBase):
    """创建用户请求模型"""

    password: str = Field(..., min_length=6, max_length=100, description="密码")
    is_superuser: bool = Field(False, description="是否超级用户")


class UserUpdate(BaseSchema):
    """更新用户请求模型"""

    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, max_length=20, description="手机号")
    nickname: str | None = Field(None, max_length=100, description="昵称")
    is_active: bool | None = Field(None, description="是否激活")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """验证手机号格式"""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 11:
            raise ValueError("请输入11位手机号")
        return v


class UserPasswordChange(BaseSchema):
    """修改密码请求模型"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserResponse(UserBase, TimestampMixin):
    """用户响应模型"""

    id: UUID = Field(..., description="用户ID")
    is_superuser: bool = Field(..., description="是否超级用户")
    is_deleted: bool = Field(..., description="是否已删除")
    last_login: datetime | None = Field(None, description="最后登录时间")


class UserWithRoles(UserResponse):
    """带角色的用户响应模型"""

    roles: list["RoleResponse"] = Field(default_factory=list, description="用户角色")


# ===================== 角色相关模型 =====================


class RoleBase(BaseSchema):
    """角色基础模型"""

    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=255, description="角色描述")
    is_active: bool = Field(True, description="是否激活")


class RoleCreate(RoleBase):
    """创建角色请求模型"""

    pass


class RoleUpdate(BaseSchema):
    """更新角色请求模型"""

    name: str | None = Field(None, min_length=2, max_length=50, description="角色名称")
    description: str | None = Field(None, max_length=255, description="角色描述")
    is_active: bool | None = Field(None, description="是否激活")


class RoleResponse(RoleBase, TimestampMixin):
    """角色响应模型"""

    id: UUID = Field(..., description="角色ID")
    is_deleted: bool = Field(..., description="是否已删除")


class RoleWithPermissions(RoleResponse):
    """带权限的角色响应模型"""

    permissions: list["PermissionResponse"] = Field(default_factory=list, description="角色权限")


class RoleWithUsers(RoleResponse):
    """带用户的角色响应模型"""

    users: list["UserResponse"] = Field(default_factory=list, description="角色用户")


class RoleWithPermission(RoleResponse):
    """带权限的角色响应模型"""

    permissions: list[UUID] = Field(default_factory=list, description="角色权限ID列表")


# ===================== 权限相关模型 =====================


class PermissionBase(BaseSchema):
    """权限基础模型"""

    name: str = Field(..., min_length=2, max_length=100, description="权限名称")
    code: str = Field(..., min_length=2, max_length=100, description="权限代码")
    description: str | None = Field(None, max_length=255, description="权限描述")
    resource: str = Field(..., max_length=100, description="资源名称")
    action: str = Field(..., max_length=50, description="操作类型")


class PermissionCreate(PermissionBase):
    """创建权限请求模型"""

    pass


class PermissionUpdate(BaseSchema):
    """更新权限请求模型"""

    name: str | None = Field(None, min_length=2, max_length=100, description="权限名称")
    description: str | None = Field(None, max_length=255, description="权限描述")
    resource: str | None = Field(None, max_length=100, description="资源名称")
    action: str | None = Field(None, max_length=50, description="操作类型")


class PermissionResponse(PermissionBase, TimestampMixin):
    """权限响应模型"""

    id: UUID = Field(..., description="权限ID")
    is_deleted: bool = Field(..., description="是否已删除")


class PermissionWithRoles(PermissionResponse):
    """带角色的权限响应模型"""

    roles: list[UUID] = Field(default_factory=list, description="权限关联的角色ID列表")


# ===================== 审计日志模型 =====================


class AuditLogBase(BaseSchema):
    """审计日志基础模型"""

    action: str = Field(..., max_length=50, description="操作类型")
    resource: str | None = Field(None, max_length=100, description="资源类型")
    resource_id: str | None = Field(None, max_length=100, description="资源ID")
    status: str = Field(..., max_length=20, description="操作状态")
    ip_address: str | None = Field(None, max_length=45, description="IP地址")
    user_agent: str | None = Field(None, max_length=500, description="用户代理")
    details: str | None = Field(None, description="详细信息")
    error_message: str | None = Field(None, description="错误信息")


class AuditLogCreate(AuditLogBase):
    """创建审计日志请求模型"""

    user_id: UUID | None = Field(None, description="用户ID")


class AuditLogResponse(AuditLogBase, TimestampMixin):
    """审计日志响应模型"""

    id: int = Field(..., description="日志ID")
    user_id: UUID | None = Field(None, description="用户ID")
    is_deleted: bool = Field(..., description="是否已删除")


# ===================== 认证相关模型 =====================


class LoginRequest(BaseSchema):
    """
    登录请求模型

    Attributes:
        username: 用户名
        password: 密码
    """

    identifier: str = Field(..., description="用户名、邮箱或手机号")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")


class TokenResponse(BaseSchema):
    """
    Token响应模型

    Attributes:
        access_token: 访问令牌
        token_type: 令牌类型
        expires_in: 过期时间（秒）
    """

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    refresh_token: str | None = Field(None, description="刷新令牌")


class RefreshTokenRequest(BaseSchema):
    """
    刷新Token请求模型

    Attributes:
        refresh_token: 刷新令牌
    """

    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseSchema):
    """
    注销请求模型

    Attributes:
        refresh_token: 刷新令牌
    """

    access_token: str = Field(..., description="访问令牌")
    all_devices: bool = Field(False, description="是否登出所有设备")


class LogoutResponse(BaseSchema):
    """
    注销响应模型

    Attributes:
        success: 是否注销成功
    """

    message: str = Field("登出成功", description="响应消息")
    success: bool = Field(True, description="是否成功")


class UserInfo(BaseSchema):
    """
    用户信息模型

    Attributes:
        id: 用户ID
        username: 用户名
        email: 邮箱
        nickname: 昵称
        is_active: 是否激活
        is_superuser: 是否超级用户
        roles: 角色列表
    """

    id: UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    phone: str | None = Field(None, description="手机号")
    nickname: str = Field(..., description="昵称")
    is_superuser: bool = Field(..., description="是否超级用户")
    roles: list[str] = Field(default_factory=list, description="角色列表")
    permissions: list[str] = Field(default_factory=list, description="权限列表")
    avatar: str | None = Field(None, description="头像URL")


class LoginResponse(TokenResponse):
    """
    登录响应模型
    """

    user: UserInfo = Field(..., description="用户信息")


class RefreshTokenResponse(TokenResponse):
    """
    刷新Token响应模型
    """


# ===================== 角色权限分配模型 =====================


class UserRoleAssignRequest(BaseSchema):
    """
    用户角色分配请求模型

    Attributes:
        user_id: 用户ID
        role_ids: 角色ID列表
    """

    user_id: UUID = Field(..., description="用户ID")
    role_ids: list[UUID] = Field(..., description="角色ID列表")


class RolePermissionAssignRequest(BaseSchema):
    """
    角色权限分配请求模型

    Attributes:
        role_id: 角色ID
        permission_ids: 权限ID列表
    """

    role_id: UUID = Field(..., description="角色ID")
    permission_ids: list[UUID] = Field(..., description="权限ID列表")


# ===================== 统计相关模型 =====================


class SystemStats(BaseSchema):
    """
    系统统计信息模型

    Attributes:
        user_count: 用户总数
        role_count: 角色总数
        permission_count: 权限总数
        audit_log_count: 审计日志总数
    """

    total_users: int = Field(..., description="总用户数", ge=0)
    active_users: int = Field(..., description="活跃用户数", ge=0)
    total_roles: int = Field(..., description="总角色数", ge=0)
    total_permissions: int = Field(..., description="总权限数", ge=0)
    recent_logins: int = Field(..., description="最近登录数", ge=0)


class UserActivityStats(BaseSchema):
    """
    用户活跃度统计模型

    Attributes:
        date: 日期
        active_user_count: 活跃用户数
    """

    user_id: UUID = Field(..., description="用户ID")
    login_count: int = Field(..., description="登录次数", ge=0)
    last_login: datetime | None = Field(None, description="最后登录时间")
    total_actions: int = Field(..., description="总操作数", ge=0)


# ===================== 错误处理模型 =====================


class ErrorDetail(BaseSchema):
    """
    错误详情模型

    Attributes:
        loc: 错误位置
        msg: 错误信息
        type: 错误类型
    """

    field: str | None = Field(None, description="错误字段")
    message: str = Field(..., description="错误信息")
    code: str | None = Field(None, description="错误代码")


class ValidationErrorResponse(BaseSchema):
    """
    校验错误响应模型

    Attributes:
        detail: 错误详情列表
    """

    code: int = Field(422, description="状态码")
    message: str = Field("数据验证失败", description="提示信息")
    success: bool = Field(False, description="是否成功")
    errors: list[ErrorDetail] = Field(..., description="错误详情列表")


# 解决前向引用
UserWithRoles.model_rebuild()
RoleWithPermissions.model_rebuild()
RoleWithUsers.model_rebuild()

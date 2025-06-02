"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: schemas.py
@DateTime: 2025/06/02 02:32:03
@Docs: Pydantic v2 校验模型

包含现代后台管理系统所需的所有请求/响应校验模型
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.utils.enum import AuditAction, AuditStatus, ConfigCategory, ConfigDataType

# ===================== 基础模型 =====================


class BaseSchema(BaseModel):
    """基础Schema配置"""

    model_config = ConfigDict(
        # 启用字段验证
        validate_assignment=True,
        # 允许任意类型
        arbitrary_types_allowed=True,
        # 使用枚举值
        use_enum_values=True,
        # 驼峰命名别名
        alias_generator=to_camel,
        # 验证默认值
        validate_default=True,
        # 额外属性禁止
        extra="forbid",
    )


class TimestampMixin(BaseModel):
    """时间戳混入"""

    created_at: datetime | None = Field(None, description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")


class PageQuery(BaseSchema):
    """分页查询基础模型"""

    page: int = Field(default=1, ge=1, le=10000, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: str | None = Field(None, description="排序字段")
    sort_order: str | None = Field(default="desc", pattern=r"^(asc|desc)$", description="排序方向")


class PageResponse(BaseSchema):
    """分页响应基础模型"""

    items: list[Any] = Field(description="数据列表")
    total: int = Field(ge=0, description="总数量")
    page: int = Field(ge=1, description="当前页码")
    size: int = Field(ge=1, description="每页数量")
    pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class ApiResponse(BaseSchema):
    """统一API响应模型"""

    success: bool = Field(True, description="是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: Any | None = Field(None, description="响应数据")
    error_code: str | None = Field(None, description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


# ===================== 用户相关模型 =====================


class UserBase(BaseSchema):
    """用户基础模型"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str | None = Field(None, max_length=100, description="全名")
    phone: str | None = Field(None, description="手机号")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """验证手机号格式"""
        if v is None:
            return v
        import re

        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("请输入有效的手机号码")
        return v


class UserCreate(UserBase):
    """创建用户请求模型"""

    password: str = Field(..., min_length=8, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    is_superuser: bool = Field(False, description="是否超级用户")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        import re

        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self) -> UserCreate:
        """验证密码确认"""
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class UserUpdate(BaseSchema):
    """更新用户请求模型"""

    full_name: str | None = Field(None, max_length=100, description="全名")
    phone: str | None = Field(None, description="手机号")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """验证手机号格式"""
        if v is None:
            return v
        import re

        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("请输入有效的手机号码")
        return v


class UserPasswordChange(BaseSchema):
    """修改密码请求模型"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        import re

        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self) -> UserPasswordChange:
        """验证密码确认"""
        if self.new_password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        if self.old_password == self.new_password:
            raise ValueError("新密码不能与旧密码相同")
        return self


class UserStatusUpdate(BaseSchema):
    """用户状态更新模型"""

    is_active: bool | None = Field(None, description="是否激活")
    is_superuser: bool | None = Field(None, description="是否超级用户")


class UserResponse(UserBase, TimestampMixin):
    """用户响应模型"""

    id: UUID = Field(..., description="用户ID")
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级用户")
    email_verified: bool = Field(description="邮箱是否验证")
    phone_verified: bool = Field(description="手机是否验证")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    login_count: int = Field(ge=0, description="登录次数")


class UserListQuery(PageQuery):
    """用户列表查询模型"""

    keyword: str | None = Field(None, max_length=100, description="关键词搜索")
    is_active: bool | None = Field(None, description="是否激活")
    is_superuser: bool | None = Field(None, description="是否超级用户")
    email_verified: bool | None = Field(None, description="邮箱是否验证")
    created_start: datetime | None = Field(None, description="创建时间开始")
    created_end: datetime | None = Field(None, description="创建时间结束")


class UserListResponse(PageResponse):
    """用户列表响应模型"""

    items: list[UserResponse] = Field(description="用户列表")


# ===================== 角色相关模型 =====================


class RoleBase(BaseSchema):
    """角色基础模型"""

    name: str = Field(..., min_length=2, max_length=100, description="角色名称")
    code: str = Field(..., min_length=2, max_length=50, description="角色代码")
    description: str | None = Field(None, max_length=500, description="角色描述")
    level: int = Field(default=0, ge=0, le=999, description="角色等级")
    sort_order: int = Field(default=0, description="排序顺序")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证角色代码格式"""
        import re

        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError("角色代码必须以大写字母开头，只能包含大写字母、数字和下划线")
        return v


class RoleCreate(RoleBase):
    """创建角色请求模型"""

    is_system: bool = Field(False, description="是否系统角色")


class RoleUpdate(BaseSchema):
    """更新角色请求模型"""

    name: str | None = Field(None, min_length=2, max_length=100, description="角色名称")
    description: str | None = Field(None, max_length=500, description="角色描述")
    level: int | None = Field(None, ge=0, le=999, description="角色等级")
    sort_order: int | None = Field(None, description="排序顺序")


class RoleStatusUpdate(BaseSchema):
    """角色状态更新模型"""

    is_active: bool = Field(..., description="是否激活")


class RoleResponse(RoleBase, TimestampMixin):
    """角色响应模型"""

    id: UUID = Field(..., description="角色ID")
    is_active: bool = Field(description="是否激活")
    is_system: bool = Field(description="是否系统角色")
    permission_count: int = Field(ge=0, description="权限数量")


class RoleDetailResponse(RoleResponse):
    """角色详情响应模型"""

    permissions: list[PermissionResponse] = Field(default_factory=list, description="权限列表")


class RoleListQuery(PageQuery):
    """角色列表查询模型"""

    keyword: str | None = Field(None, max_length=100, description="关键词搜索")
    is_active: bool | None = Field(None, description="是否激活")
    is_system: bool | None = Field(None, description="是否系统角色")
    level_min: int | None = Field(None, ge=0, description="最小等级")
    level_max: int | None = Field(None, le=999, description="最大等级")


class RoleListResponse(PageResponse):
    """角色列表响应模型"""

    items: list[RoleResponse] = Field(description="角色列表")


class RolePermissionUpdate(BaseSchema):
    """角色权限更新模型"""

    permission_ids: list[UUID] = Field(..., description="权限ID列表")


# ===================== 权限相关模型 =====================


class PermissionBase(BaseSchema):
    """权限基础模型"""

    name: str = Field(..., min_length=2, max_length=100, description="权限名称")
    code: str = Field(..., min_length=2, max_length=100, description="权限代码")
    resource: str = Field(..., min_length=1, max_length=100, description="资源类型")
    action: str = Field(..., min_length=1, max_length=50, description="操作类型")
    description: str | None = Field(None, max_length=500, description="权限描述")
    method: str | None = Field(None, max_length=10, description="HTTP方法")
    path: str | None = Field(None, max_length=255, description="API路径")
    category: str | None = Field(None, max_length=50, description="权限分类")
    sort_order: int = Field(default=0, description="排序顺序")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证权限代码格式"""
        import re

        if not re.match(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$", v):
            raise ValueError("权限代码必须以小写字母开头，使用点分格式")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str | None) -> str | None:
        """验证HTTP方法"""
        if v is None:
            return v
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        if v.upper() not in valid_methods:
            raise ValueError(f"HTTP方法必须是以下之一: {', '.join(valid_methods)}")
        return v.upper()


class PermissionCreate(PermissionBase):
    """创建权限请求模型"""

    is_system: bool = Field(False, description="是否系统权限")


class PermissionUpdate(BaseSchema):
    """更新权限请求模型"""

    name: str | None = Field(None, min_length=2, max_length=100, description="权限名称")
    description: str | None = Field(None, max_length=500, description="权限描述")
    category: str | None = Field(None, max_length=50, description="权限分类")
    sort_order: int | None = Field(None, description="排序顺序")


class PermissionResponse(PermissionBase, TimestampMixin):
    """权限响应模型"""

    id: UUID = Field(..., description="权限ID")
    is_system: bool = Field(description="是否系统权限")


class PermissionListQuery(PageQuery):
    """权限列表查询模型"""

    keyword: str | None = Field(None, max_length=100, description="关键词搜索")
    resource: str | None = Field(None, max_length=100, description="资源类型")
    action: str | None = Field(None, max_length=50, description="操作类型")
    category: str | None = Field(None, max_length=50, description="权限分类")
    is_system: bool | None = Field(None, description="是否系统权限")


class PermissionListResponse(PageResponse):
    """权限列表响应模型"""

    items: list[PermissionResponse] = Field(description="权限列表")


# ===================== 用户角色关联模型 =====================


class UserRoleAssign(BaseSchema):
    """用户角色分配模型"""

    role_ids: list[UUID] = Field(..., min_length=1, description="角色ID列表")
    expires_at: datetime | None = Field(None, description="过期时间")


class UserRoleUpdate(BaseSchema):
    """用户角色更新模型"""

    expires_at: datetime | None = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")


class UserRoleResponse(BaseSchema, TimestampMixin):
    """用户角色响应模型"""

    user_id: UUID = Field(..., description="用户ID")
    role_id: UUID = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")
    role_code: str = Field(..., description="角色代码")
    assigned_at: datetime = Field(..., description="分配时间")
    expires_at: datetime | None = Field(None, description="过期时间")
    is_active: bool = Field(description="是否激活")
    is_expired: bool = Field(description="是否已过期")


class UserRoleListQuery(PageQuery):
    """用户角色列表查询模型"""

    user_id: UUID | None = Field(None, description="用户ID")
    role_id: UUID | None = Field(None, description="角色ID")
    is_active: bool | None = Field(None, description="是否激活")
    is_expired: bool | None = Field(None, description="是否已过期")


class UserRoleListResponse(PageResponse):
    """用户角色列表响应模型"""

    items: list[UserRoleResponse] = Field(description="用户角色列表")


# ===================== 审计日志模型 =====================


class AuditLogQuery(PageQuery):
    """审计日志查询模型"""

    user_id: UUID | None = Field(None, description="用户ID")
    username: str | None = Field(None, max_length=50, description="用户名")
    action: AuditAction | None = Field(None, description="操作类型")
    resource: str | None = Field(None, max_length=100, description="资源类型")
    resource_id: str | None = Field(None, max_length=100, description="资源ID")
    status: AuditStatus | None = Field(None, description="操作状态")
    ip_address: str | None = Field(None, description="IP地址")
    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")


class AuditLogResponse(BaseSchema, TimestampMixin):
    """审计日志响应模型"""

    id: UUID = Field(..., description="日志ID")
    user_id: UUID | None = Field(None, description="用户ID")
    username: str | None = Field(None, description="用户名")
    action: AuditAction = Field(..., description="操作类型")
    resource: str = Field(..., description="资源类型")
    resource_id: str | None = Field(None, description="资源ID")
    resource_name: str | None = Field(None, description="资源名称")
    method: str | None = Field(None, description="HTTP方法")
    path: str | None = Field(None, description="请求路径")
    old_values: dict[str, Any] | None = Field(None, description="变更前的值")
    new_values: dict[str, Any] | None = Field(None, description="变更后的值")
    ip_address: str | None = Field(None, description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    request_id: str | None = Field(None, description="请求ID")
    session_id: str | None = Field(None, description="会话ID")
    status: AuditStatus = Field(..., description="操作状态")
    error_message: str | None = Field(None, description="错误信息")
    duration: int | None = Field(None, ge=0, description="操作耗时（毫秒）")


class AuditLogListResponse(PageResponse):
    """审计日志列表响应模型"""

    items: list[AuditLogResponse] = Field(description="审计日志列表")


# ===================== 系统配置模型 =====================


class SystemConfigBase(BaseSchema):
    """系统配置基础模型"""

    key: str = Field(..., min_length=1, max_length=100, description="配置键")
    value: dict[str, Any] | None = Field(None, description="配置值")
    description: str | None = Field(None, max_length=500, description="配置描述")
    category: ConfigCategory = Field(ConfigCategory.SYSTEM, description="配置分类")
    data_type: ConfigDataType = Field(ConfigDataType.STRING, description="数据类型")
    is_public: bool = Field(False, description="是否公开访问")
    is_encrypted: bool = Field(False, description="是否加密存储")
    validation_rule: str | None = Field(None, max_length=500, description="验证规则")
    default_value: dict[str, Any] | None = Field(None, description="默认值")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """验证配置键格式"""
        import re

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9._-]*$", v):
            raise ValueError("配置键必须以字母开头，只能包含字母、数字、点、下划线和连字符")
        return v


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置请求模型"""

    pass


class SystemConfigUpdate(BaseSchema):
    """更新系统配置请求模型"""

    value: dict[str, Any] | None = Field(None, description="配置值")
    description: str | None = Field(None, max_length=500, description="配置描述")
    is_public: bool | None = Field(None, description="是否公开访问")
    is_encrypted: bool | None = Field(None, description="是否加密存储")
    validation_rule: str | None = Field(None, max_length=500, description="验证规则")
    default_value: dict[str, Any] | None = Field(None, description="默认值")


class SystemConfigResponse(SystemConfigBase, TimestampMixin):
    """系统配置响应模型"""

    id: UUID = Field(..., description="配置ID")
    version: int = Field(ge=1, description="版本号")


class SystemConfigPublicResponse(BaseSchema):
    """公开系统配置响应模型"""

    key: str = Field(..., description="配置键")
    value: dict[str, Any] | None = Field(None, description="配置值")
    data_type: ConfigDataType = Field(..., description="数据类型")


class SystemConfigQuery(PageQuery):
    """系统配置查询模型"""

    keyword: str | None = Field(None, max_length=100, description="关键词搜索")
    category: ConfigCategory | None = Field(None, description="配置分类")
    data_type: ConfigDataType | None = Field(None, description="数据类型")
    is_public: bool | None = Field(None, description="是否公开访问")
    is_encrypted: bool | None = Field(None, description="是否加密存储")


class SystemConfigListResponse(PageResponse):
    """系统配置列表响应模型"""

    items: list[SystemConfigResponse] = Field(description="系统配置列表")


# ===================== 认证相关模型 =====================


class LoginRequest(BaseSchema):
    """登录请求模型"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=1, max_length=128, description="密码")
    remember_me: bool = Field(False, description="记住我")


class LoginResponse(BaseSchema):
    """登录响应模型"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌有效期（秒）")
    user: UserResponse = Field(..., description="用户信息")


class RefreshTokenRequest(BaseSchema):
    """刷新令牌请求模型"""

    refresh_token: str = Field(..., description="刷新令牌")


class TokenResponse(BaseSchema):
    """令牌响应模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌有效期（秒）")


# ===================== 统计分析模型 =====================


class DashboardStats(BaseSchema):
    """仪表板统计模型"""

    total_users: int = Field(ge=0, description="用户总数")
    active_users: int = Field(ge=0, description="活跃用户数")
    total_roles: int = Field(ge=0, description="角色总数")
    total_permissions: int = Field(ge=0, description="权限总数")
    today_logins: int = Field(ge=0, description="今日登录数")
    system_configs: int = Field(ge=0, description="系统配置数")


class UserStatsQuery(BaseSchema):
    """用户统计查询模型"""

    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    group_by: str = Field(default="day", pattern=r"^(day|week|month)$", description="分组方式")


class UserStatsResponse(BaseSchema):
    """用户统计响应模型"""

    date: str = Field(..., description="日期")
    new_users: int = Field(ge=0, description="新增用户数")
    active_users: int = Field(ge=0, description="活跃用户数")
    login_count: int = Field(ge=0, description="登录次数")


class AuditStatsQuery(BaseSchema):
    """审计统计查询模型"""

    start_date: datetime | None = Field(None, description="开始日期")
    end_date: datetime | None = Field(None, description="结束日期")
    action: AuditAction | None = Field(None, description="操作类型")
    resource: str | None = Field(None, description="资源类型")


class AuditStatsResponse(BaseSchema):
    """审计统计响应模型"""

    action: AuditAction = Field(..., description="操作类型")
    count: int = Field(ge=0, description="操作次数")
    success_count: int = Field(ge=0, description="成功次数")
    failure_count: int = Field(ge=0, description="失败次数")


# ===================== 导入导出模型 =====================


class ExportQuery(BaseSchema):
    """导出查询模型"""

    format: str = Field(default="xlsx", pattern=r"^(xlsx|csv|json)$", description="导出格式")
    fields: list[str] | None = Field(None, description="导出字段")
    filters: dict[str, Any] | None = Field(None, description="过滤条件")


class ImportRequest(BaseSchema):
    """导入请求模型"""

    file_type: str = Field(..., pattern=r"^(xlsx|csv|json)$", description="文件类型")
    override_existing: bool = Field(False, description="是否覆盖已存在的数据")
    validate_only: bool = Field(False, description="仅验证不导入")


class ImportResponse(BaseSchema):
    """导入响应模型"""

    total_rows: int = Field(ge=0, description="总行数")
    success_rows: int = Field(ge=0, description="成功行数")
    failed_rows: int = Field(ge=0, description="失败行数")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")
    task_id: str | None = Field(None, description="任务ID（异步导入）")


# ===================== 任务相关模型 =====================


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class TaskResponse(BaseSchema):
    """任务响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: float = Field(ge=0, le=100, description="进度百分比")
    result: dict[str, Any] | None = Field(None, description="任务结果")
    error: str | None = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    started_at: datetime | None = Field(None, description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")


# ===================== 文件管理模型 =====================


class FileUploadResponse(BaseSchema):
    """文件上传响应模型"""

    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(ge=0, description="文件大小（字节）")
    content_type: str = Field(..., description="文件类型")
    uploaded_at: datetime = Field(..., description="上传时间")


class FileListQuery(PageQuery):
    """文件列表查询模型"""

    keyword: str | None = Field(None, max_length=100, description="文件名关键词")
    content_type: str | None = Field(None, description="文件类型")
    uploaded_start: datetime | None = Field(None, description="上传开始时间")
    uploaded_end: datetime | None = Field(None, description="上传结束时间")
    min_size: int | None = Field(None, ge=0, description="最小文件大小")
    max_size: int | None = Field(None, ge=0, description="最大文件大小")


# ===================== 批量操作模型 =====================


class BatchOperation(BaseSchema):
    """批量操作基础模型"""

    ids: list[UUID] = Field(..., min_length=1, max_length=1000, description="操作对象ID列表")
    operation: str = Field(..., description="操作类型")
    params: dict[str, Any] | None = Field(None, description="操作参数")


class BatchUserOperation(BatchOperation):
    """批量用户操作模型"""

    operation: str = Field(..., pattern=r"^(activate|deactivate|delete|reset_password)$", description="操作类型")


class BatchRoleOperation(BatchOperation):
    """批量角色操作模型"""

    operation: str = Field(..., pattern=r"^(activate|deactivate|delete|assign_permissions)$", description="操作类型")


class BatchOperationResponse(BaseSchema):
    """批量操作响应模型"""

    total: int = Field(ge=0, description="总操作数")
    success: int = Field(ge=0, description="成功数")
    failed: int = Field(ge=0, description="失败数")
    failed_ids: list[UUID] = Field(default_factory=list, description="失败的ID列表")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")


# ===================== 数据字典模型 =====================


class DictTypeBase(BaseSchema):
    """字典类型基础模型"""

    type_code: str = Field(..., min_length=1, max_length=50, description="字典类型编码")
    type_name: str = Field(..., min_length=1, max_length=100, description="字典类型名称")
    description: str | None = Field(None, max_length=500, description="描述")
    is_system: bool = Field(False, description="是否系统字典")
    sort_order: int = Field(default=0, description="排序顺序")

    @field_validator("type_code")
    @classmethod
    def validate_type_code(cls, v: str) -> str:
        """验证字典类型编码格式"""
        import re

        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("字典类型编码必须以小写字母开头，只能包含小写字母、数字和下划线")
        return v


class DictTypeCreate(DictTypeBase):
    """创建字典类型请求模型"""

    pass


class DictTypeUpdate(BaseSchema):
    """更新字典类型请求模型"""

    type_name: str | None = Field(None, min_length=1, max_length=100, description="字典类型名称")
    description: str | None = Field(None, max_length=500, description="描述")
    sort_order: int | None = Field(None, description="排序顺序")


class DictTypeResponse(DictTypeBase, TimestampMixin):
    """字典类型响应模型"""

    id: UUID = Field(..., description="字典类型ID")
    is_active: bool = Field(description="是否激活")
    item_count: int = Field(ge=0, description="字典项数量")


class DictItemBase(BaseSchema):
    """字典项基础模型"""

    item_code: str = Field(..., min_length=1, max_length=50, description="字典项编码")
    item_name: str = Field(..., min_length=1, max_length=100, description="字典项名称")
    item_value: str | None = Field(None, max_length=200, description="字典项值")
    description: str | None = Field(None, max_length=500, description="描述")
    sort_order: int = Field(default=0, description="排序顺序")
    css_class: str | None = Field(None, max_length=100, description="CSS样式类")
    list_class: str | None = Field(None, max_length=100, description="列表样式类")


class DictItemCreate(DictItemBase):
    """创建字典项请求模型"""

    type_id: UUID = Field(..., description="字典类型ID")


class DictItemUpdate(BaseSchema):
    """更新字典项请求模型"""

    item_name: str | None = Field(None, min_length=1, max_length=100, description="字典项名称")
    item_value: str | None = Field(None, max_length=200, description="字典项值")
    description: str | None = Field(None, max_length=500, description="描述")
    sort_order: int | None = Field(None, description="排序顺序")
    css_class: str | None = Field(None, max_length=100, description="CSS样式类")
    list_class: str | None = Field(None, max_length=100, description="列表样式类")


class DictItemResponse(DictItemBase, TimestampMixin):
    """字典项响应模型"""

    id: UUID = Field(..., description="字典项ID")
    type_id: UUID = Field(..., description="字典类型ID")
    type_code: str = Field(..., description="字典类型编码")
    type_name: str = Field(..., description="字典类型名称")
    is_active: bool = Field(description="是否激活")


# ===================== 系统监控模型 =====================


class SystemHealthResponse(BaseSchema):
    """系统健康检查响应模型"""

    status: str = Field(..., description="系统状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="系统版本")
    uptime: int = Field(ge=0, description="运行时间（秒）")
    database: dict[str, Any] = Field(..., description="数据库状态")
    redis: dict[str, Any] = Field(..., description="Redis状态")
    memory: dict[str, Any] = Field(..., description="内存使用情况")
    disk: dict[str, Any] = Field(..., description="磁盘使用情况")


class SystemMetricsResponse(BaseSchema):
    """系统指标响应模型"""

    cpu_usage: float = Field(ge=0, le=100, description="CPU使用率")
    memory_usage: float = Field(ge=0, le=100, description="内存使用率")
    disk_usage: float = Field(ge=0, le=100, description="磁盘使用率")
    active_connections: int = Field(ge=0, description="活跃连接数")
    request_count: int = Field(ge=0, description="请求总数")
    error_count: int = Field(ge=0, description="错误总数")
    avg_response_time: float = Field(ge=0, description="平均响应时间（毫秒）")
    timestamp: datetime = Field(..., description="指标时间")


# ===================== 消息通知模型 =====================


class NotificationType(str, Enum):
    """通知类型枚举"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationBase(BaseSchema):
    """通知基础模型"""

    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., min_length=1, max_length=2000, description="通知内容")
    type: NotificationType = Field(NotificationType.INFO, description="通知类型")
    is_global: bool = Field(False, description="是否全局通知")
    expires_at: datetime | None = Field(None, description="过期时间")


class NotificationCreate(NotificationBase):
    """创建通知请求模型"""

    target_users: list[UUID] | None = Field(None, description="目标用户ID列表")
    target_roles: list[UUID] | None = Field(None, description="目标角色ID列表")


class NotificationResponse(NotificationBase, TimestampMixin):
    """通知响应模型"""

    id: UUID = Field(..., description="通知ID")
    sender_id: UUID | None = Field(None, description="发送者ID")
    sender_name: str | None = Field(None, description="发送者名称")
    read_count: int = Field(ge=0, description="已读数量")
    total_count: int = Field(ge=0, description="总发送数量")


class UserNotificationResponse(BaseSchema):
    """用户通知响应模型"""

    id: UUID = Field(..., description="通知ID")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: NotificationType = Field(..., description="通知类型")
    is_read: bool = Field(description="是否已读")
    read_at: datetime | None = Field(None, description="阅读时间")
    created_at: datetime = Field(..., description="创建时间")


# ===================== 操作日志模型 =====================


class OperationLogQuery(PageQuery):
    """操作日志查询模型"""

    user_id: UUID | None = Field(None, description="用户ID")
    module: str | None = Field(None, max_length=50, description="模块名称")
    operation: str | None = Field(None, max_length=50, description="操作类型")
    ip_address: str | None = Field(None, description="IP地址")
    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")


class OperationLogResponse(BaseSchema, TimestampMixin):
    """操作日志响应模型"""

    id: UUID = Field(..., description="日志ID")
    user_id: UUID | None = Field(None, description="用户ID")
    username: str | None = Field(None, description="用户名")
    module: str = Field(..., description="模块名称")
    operation: str = Field(..., description="操作类型")
    description: str | None = Field(None, description="操作描述")
    ip_address: str | None = Field(None, description="IP地址")
    user_agent: str | None = Field(None, description="用户代理")
    request_params: dict[str, Any] | None = Field(None, description="请求参数")
    response_data: dict[str, Any] | None = Field(None, description="响应数据")
    duration: int | None = Field(None, ge=0, description="操作耗时（毫秒）")
    status: str = Field(..., description="操作状态")


# ===================== 数据备份模型 =====================


class BackupType(str, Enum):
    """备份类型枚举"""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupCreate(BaseSchema):
    """创建备份请求模型"""

    name: str = Field(..., min_length=1, max_length=100, description="备份名称")
    type: BackupType = Field(BackupType.FULL, description="备份类型")
    description: str | None = Field(None, max_length=500, description="备份描述")
    include_files: bool = Field(True, description="是否包含文件")


class BackupResponse(BaseSchema, TimestampMixin):
    """备份响应模型"""

    id: UUID = Field(..., description="备份ID")
    name: str = Field(..., description="备份名称")
    type: BackupType = Field(..., description="备份类型")
    description: str | None = Field(None, description="备份描述")
    file_path: str = Field(..., description="备份文件路径")
    file_size: int = Field(ge=0, description="备份文件大小（字节）")
    status: str = Field(..., description="备份状态")
    progress: float = Field(ge=0, le=100, description="备份进度")
    started_at: datetime | None = Field(None, description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    error_message: str | None = Field(None, description="错误信息")


# 更新前向引用
RoleDetailResponse.model_rebuild()

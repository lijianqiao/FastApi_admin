"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:32:03
@Docs: Pydantic 模式模块 - 现代后台管理系统最优设计

Schemas模块导出，提供完整的现代后台功能模型
"""

from .schemas import (
    # 基础响应模型
    APIResponse,
    # 审计日志模型
    AuditLogBase,
    AuditLogCreate,
    AuditLogQuery,
    AuditLogResponse,
    # 查询相关模型
    BaseQuery,
    BaseSchema,
    # 批量操作模型
    BatchDeleteRequest,
    BatchOperationResponse,
    BatchUpdateRequest,
    # 错误处理模型
    ErrorDetail,
    # 文件相关模型
    FileUploadResponse,
    ImportResult,
    # 认证相关模型
    LoginRequest,
    PagedResponse,
    PaginationResponse,
    # 权限相关模型
    PermissionBase,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RefreshTokenRequest,
    ResponseModel,
    # 角色相关模型
    RoleBase,
    RoleCreate,
    RolePermissionAssignRequest,
    RoleQuery,
    RoleResponse,
    RoleUpdate,
    RoleWithPermissions,
    SearchQuery,
    # 统计相关模型
    SystemStats,
    TimestampMixin,
    TokenResponse,
    UserActivityStats,
    # 用户相关模型
    UserBase,
    UserCreate,
    UserInfo,
    UserPasswordChange,
    UserQuery,
    UserResponse,
    # 分配相关模型
    UserRoleAssignRequest,
    UserUpdate,
    UserWithRoles,
    ValidationErrorResponse,
)

__all__ = [
    # 基础响应模型
    "APIResponse",
    "BaseSchema",
    "PagedResponse",
    "ResponseModel",
    "PaginationResponse",
    "TimestampMixin",
    # 查询相关模型
    "BaseQuery",
    "SearchQuery",
    "UserQuery",
    "RoleQuery",
    "AuditLogQuery",
    # 用户相关模型
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "UserWithRoles",
    "UserInfo",
    # 角色相关模型
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    # 权限相关模型
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    # 审计日志模型
    "AuditLogBase",
    "AuditLogCreate",
    "AuditLogResponse",
    # 认证相关模型
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    # 批量操作模型
    "BatchDeleteRequest",
    "BatchUpdateRequest",
    "BatchOperationResponse",
    # 分配相关模型
    "UserRoleAssignRequest",
    "RolePermissionAssignRequest",
    # 统计相关模型
    "SystemStats",
    "UserActivityStats",
    # 文件相关模型
    "FileUploadResponse",
    "ImportResult",
    # 错误处理模型
    "ErrorDetail",
    "ValidationErrorResponse",
]

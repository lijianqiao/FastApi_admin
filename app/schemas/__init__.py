"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:32:03
@Docs: Pydantic 模式模块

Schemas模块导出，提供简洁的导入路径
使用方式：
    from app.models.schemas import UserCreate, UserResponse
    from app.models.schemas import LoginRequest, LoginResponse
"""

# 从schemas模块导入所有模型类
from .schemas import (
    ApiResponse,
    AuditLogListResponse,
    # ===================== 审计日志模型 =====================
    AuditLogQuery,
    AuditLogResponse,
    AuditStatsQuery,
    AuditStatsResponse,
    BackupCreate,
    BackupResponse,
    # ===================== 数据备份模型 =====================
    BackupType,
    # ===================== 基础模型 =====================
    BaseSchema,
    # ===================== 批量操作模型 =====================
    BatchOperation,
    BatchOperationResponse,
    BatchRoleOperation,
    BatchUserOperation,
    # ===================== 统计分析模型 =====================
    DashboardStats,
    DictItemBase,
    DictItemCreate,
    DictItemResponse,
    DictItemUpdate,
    # ===================== 数据字典模型 =====================
    DictTypeBase,
    DictTypeCreate,
    DictTypeResponse,
    DictTypeUpdate,
    # ===================== 导入导出模型 =====================
    ExportQuery,
    FileListQuery,
    # ===================== 文件管理模型 =====================
    FileUploadResponse,
    ImportRequest,
    ImportResponse,
    # ===================== 认证相关模型 =====================
    LoginRequest,
    LoginResponse,
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    # ===================== 消息通知模型 =====================
    NotificationType,
    # ===================== 操作日志模型 =====================
    OperationLogQuery,
    OperationLogResponse,
    PageQuery,
    PageResponse,
    # ===================== 权限模型 =====================
    PermissionBase,
    PermissionCreate,
    PermissionListQuery,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdate,
    RefreshTokenRequest,
    # ===================== 角色模型 =====================
    RoleBase,
    RoleCreate,
    RoleDetailResponse,
    RoleListQuery,
    RoleListResponse,
    RolePermissionUpdate,
    RoleResponse,
    RoleStatusUpdate,
    RoleUpdate,
    # ===================== 系统配置模型 =====================
    SystemConfigBase,
    SystemConfigCreate,
    SystemConfigListResponse,
    SystemConfigPublicResponse,
    SystemConfigQuery,
    SystemConfigResponse,
    SystemConfigUpdate,
    # ===================== 系统监控模型 =====================
    SystemHealthResponse,
    SystemMetricsResponse,
    TaskResponse,
    # ===================== 任务管理模型 =====================
    TaskStatus,
    TimestampMixin,
    TokenResponse,
    # ===================== 用户模型 =====================
    UserBase,
    UserCreate,
    UserListQuery,
    UserListResponse,
    UserNotificationResponse,
    UserPasswordChange,
    UserResponse,
    # ===================== 用户角色关联模型 =====================
    UserRoleAssign,
    UserRoleListQuery,
    UserRoleListResponse,
    UserRoleResponse,
    UserRoleUpdate,
    UserStatsQuery,
    UserStatsResponse,
    UserStatusUpdate,
    UserUpdate,
)

__all__ = [
    # 基础模型
    "BaseSchema",
    "TimestampMixin",
    "PageQuery",
    "PageResponse",
    "ApiResponse",
    # 用户模型
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordChange",
    "UserStatusUpdate",
    "UserResponse",
    "UserListQuery",
    "UserListResponse",
    # 角色模型
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleStatusUpdate",
    "RoleResponse",
    "RoleDetailResponse",
    "RoleListQuery",
    "RoleListResponse",
    "RolePermissionUpdate",
    # 权限模型
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionListQuery",
    "PermissionListResponse",
    # 用户角色关联模型
    "UserRoleAssign",
    "UserRoleUpdate",
    "UserRoleResponse",
    "UserRoleListQuery",
    "UserRoleListResponse",
    # 审计日志模型
    "AuditLogQuery",
    "AuditLogResponse",
    "AuditLogListResponse",
    # 系统配置模型
    "SystemConfigBase",
    "SystemConfigCreate",
    "SystemConfigUpdate",
    "SystemConfigResponse",
    "SystemConfigPublicResponse",
    "SystemConfigQuery",
    "SystemConfigListResponse",
    # 认证相关模型
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    # 统计分析模型
    "DashboardStats",
    "UserStatsQuery",
    "UserStatsResponse",
    "AuditStatsQuery",
    "AuditStatsResponse",
    # 导入导出模型
    "ExportQuery",
    "ImportRequest",
    "ImportResponse",
    # 任务管理模型
    "TaskStatus",
    "TaskResponse",
    # 文件管理模型
    "FileUploadResponse",
    "FileListQuery",
    # 批量操作模型
    "BatchOperation",
    "BatchUserOperation",
    "BatchRoleOperation",
    "BatchOperationResponse",
    # 数据字典模型
    "DictTypeBase",
    "DictTypeCreate",
    "DictTypeUpdate",
    "DictTypeResponse",
    "DictItemBase",
    "DictItemCreate",
    "DictItemUpdate",
    "DictItemResponse",
    # 系统监控模型
    "SystemHealthResponse",
    "SystemMetricsResponse",
    # 消息通知模型
    "NotificationType",
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "UserNotificationResponse",
    # 操作日志模型
    "OperationLogQuery",
    "OperationLogResponse",
    # 数据备份模型
    "BackupType",
    "BackupCreate",
    "BackupResponse",
]

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: audit_log.py
@DateTime: 2025/06/02 02:32:03
@Docs: 审计日志领域模型

审计日志领域模型包含操作审计的核心业务逻辑
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID


class AuditStatus(Enum):
    """审计状态枚举"""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    INFO = "info"


class AuditAction(Enum):
    """审计操作类型枚举"""

    # 用户操作
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"

    # 角色操作
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"

    # 权限操作
    PERMISSION_CREATE = "permission_create"
    PERMISSION_UPDATE = "permission_update"
    PERMISSION_DELETE = "permission_delete"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"

    # 系统操作
    CONFIG_UPDATE = "config_update"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"

    # 数据操作
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

    # API访问
    API_ACCESS = "api_access"
    API_ERROR = "api_error"


@dataclass
class AuditLog:
    """审计日志领域模型

    负责记录和管理系统操作的审计信息，提供完整的操作追踪
    """

    # 基本标识
    id: UUID

    # 用户信息
    user_id: UUID | None
    username: str | None

    # 操作信息
    action: AuditAction
    resource: str
    resource_id: str | None = None
    resource_name: str | None = None

    # HTTP信息
    method: str | None = None
    path: str | None = None

    # 数据变更
    old_values: dict | None = None
    new_values: dict | None = None

    # 请求信息
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    session_id: str | None = None

    # 结果信息
    status: AuditStatus = AuditStatus.SUCCESS
    error_message: str | None = None
    duration: int | None = None  # 毫秒    # 审计字段
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self):
        """初始化后的验证"""
        if isinstance(self.action, str):
            self.action = AuditAction(self.action)
        if isinstance(self.status, str):
            self.status = AuditStatus(self.status)

    @property
    def is_success(self) -> bool:
        """是否操作成功"""
        return self.status == AuditStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """是否操作失败"""
        return self.status == AuditStatus.FAILURE

    @property
    def has_data_changes(self) -> bool:
        """是否包含数据变更"""
        return self.old_values is not None or self.new_values is not None

    def add_error(self, error_message: str) -> None:
        """添加错误信息"""
        self.status = AuditStatus.FAILURE
        self.error_message = error_message

    def set_duration(self, start_time: datetime, end_time: datetime) -> None:
        """设置操作耗时"""
        duration_seconds = (end_time - start_time).total_seconds()
        self.duration = int(duration_seconds * 1000)  # 转换为毫秒

    def mask_sensitive_data(self, sensitive_fields: list[str] | None = None) -> AuditLog:
        """脱敏敏感数据

        Args:
            sensitive_fields: 需要脱敏的字段列表

        Returns:
            脱敏后的审计日志副本
        """
        if sensitive_fields is None:
            sensitive_fields = ["password", "token", "secret", "key"]

        def mask_dict(data: dict | None) -> dict | None:
            if data is None:
                return None

            masked_data = data.copy()
            for key, value in masked_data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    masked_data[key] = "***MASKED***"
                elif isinstance(value, dict):
                    masked_data[key] = mask_dict(value)
            return masked_data

        # 创建副本并脱敏
        masked_log = AuditLog(
            id=self.id,
            user_id=self.user_id,
            username=self.username,
            action=self.action,
            resource=self.resource,
            resource_id=self.resource_id,
            resource_name=self.resource_name,
            method=self.method,
            path=self.path,
            old_values=mask_dict(self.old_values),
            new_values=mask_dict(self.new_values),
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            request_id=self.request_id,
            session_id=self.session_id,
            status=self.status,
            error_message=self.error_message,
            duration=self.duration,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

        return masked_log

    def get_summary(self) -> str:
        """获取审计日志摘要"""
        action_text = self.action.value.replace("_", " ").title()
        user_text = f"User {self.username}" if self.username else "System"
        resource_text = f"{self.resource}"
        if self.resource_name:
            resource_text += f" '{self.resource_name}'"
        elif self.resource_id:
            resource_text += f" {self.resource_id}"

        return f"{user_text} {action_text} {resource_text}"

    def to_search_text(self) -> str:
        """生成用于搜索的文本"""
        search_parts = [
            self.username or "",
            self.action.value,
            self.resource,
            self.resource_name or "",
            self.resource_id or "",
            self.ip_address or "",
            self.error_message or "",
        ]
        return " ".join(filter(None, search_parts)).lower()

    def __str__(self) -> str:
        return self.get_summary()

    def __repr__(self) -> str:
        return (
            f"AuditLog(id={self.id}, action={self.action.value}, resource={self.resource}, status={self.status.value})"
        )

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: enum.py
@DateTime: 2025/06/02 13:07:28
@Docs: 枚举类型工具
"""

from enum import Enum


class Environment(str, Enum):
    """环境枚举"""

    DEVELOPMENT = "development"  # 开发环境
    STAGING = "staging"  # 预发布环境
    PRODUCTION = "production"  # 生产环境
    TESTING = "testing"  # 测试环境


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 审计日志模型


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


# 系统配置


class ConfigDataType(Enum):
    """配置数据类型枚举"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"


class ConfigCategory(Enum):
    """配置分类枚举"""

    SYSTEM = "system"
    SECURITY = "security"
    EMAIL = "email"
    SMS = "sms"
    PAYMENT = "payment"
    STORAGE = "storage"
    LOGGING = "logging"
    CACHE = "cache"
    DATABASE = "database"
    API = "api"
    UI = "ui"
    FEATURE = "feature"

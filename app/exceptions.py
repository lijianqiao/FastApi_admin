"""
全局异常定义

定义项目中使用的所有自定义异常类，提供统一的异常处理机制。
"""

from typing import Any

from fastapi import HTTPException, status


class BaseAppException(Exception):
    """
    应用基础异常类

    所有自定义异常的基类，提供统一的错误处理接口。
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，便于API响应"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ================ 数据库相关异常 ================


class DatabaseError(BaseAppException):
    """数据库操作异常基类"""

    def __init__(self, message: str, operation: str = "", **kwargs):
        super().__init__(
            message=f"数据库操作失败: {message}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs
        )
        self.operation = operation


class RecordNotFoundError(BaseAppException):
    """记录不存在异常"""

    def __init__(self, resource: str = "记录", resource_id: Any = None):
        message = f"{resource}不存在"
        if resource_id is not None:
            message += f" (ID: {resource_id})"

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )
        self.resource = resource
        self.resource_id = resource_id


class DuplicateRecordError(BaseAppException):
    """记录重复异常"""

    def __init__(self, resource: str = "记录", field: str = "", value: Any = None):
        message = f"{resource}已存在"
        if field and value is not None:
            message += f" ({field}: {value})"

        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )
        self.resource = resource
        self.field = field
        self.value = value


class DatabaseConstraintError(BaseAppException):
    """数据库约束违反异常"""

    def __init__(self, constraint: str = "", message: str = ""):
        if not message:
            message = f"数据约束违反: {constraint}" if constraint else "数据约束违反"

        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.constraint = constraint


# ================ 验证相关异常 ================


class ValidationError(BaseAppException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        field_errors: list[dict[str, str]] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field_errors": field_errors or []},
        )
        self.field_errors = field_errors or []


class InvalidParameterError(BaseAppException):
    """无效参数异常"""

    def __init__(self, parameter: str, value: Any = None, expected: str = ""):
        message = f"无效参数: {parameter}"
        if value is not None:
            message += f" (值: {value})"
        if expected:
            message += f" (期望: {expected})"

        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.parameter = parameter
        self.value = value
        self.expected = expected


# ================ 认证授权相关异常 ================


class AuthenticationError(BaseAppException):
    """认证失败异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(BaseAppException):
    """授权失败异常"""

    def __init__(self, message: str = "权限不足", required_permission: str = ""):
        if required_permission:
            message += f" (需要权限: {required_permission})"

        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )
        self.required_permission = required_permission


class TokenExpiredError(AuthenticationError):
    """令牌过期异常"""

    def __init__(self, token_type: str = "token"):
        super().__init__(message=f"{token_type}已过期")
        self.token_type = token_type


class InvalidTokenError(AuthenticationError):
    """无效令牌异常"""

    def __init__(self, token_type: str = "token"):
        super().__init__(message=f"无效的{token_type}")
        self.token_type = token_type


# ================ 业务逻辑相关异常 ================


class BusinessLogicError(BaseAppException):
    """业务逻辑异常"""

    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
        )


class ResourceLockedError(BaseAppException):
    """资源被锁定异常"""

    def __init__(self, resource: str = "资源", locked_by: str = ""):
        message = f"{resource}已被锁定"
        if locked_by:
            message += f" (锁定者: {locked_by})"

        super().__init__(
            message=message,
            status_code=status.HTTP_423_LOCKED,
        )
        self.resource = resource
        self.locked_by = locked_by


class OperationNotAllowedError(BaseAppException):
    """操作不被允许异常"""

    def __init__(self, operation: str = "", reason: str = ""):
        message = "操作不被允许"
        if operation:
            message = f"操作 '{operation}' 不被允许"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.operation = operation
        self.reason = reason


# ================ 外部服务相关异常 ================


class ExternalServiceError(BaseAppException):
    """外部服务异常"""

    def __init__(self, service: str, message: str = "", status_code: int | None = None):
        if not message:
            message = f"外部服务 '{service}' 调用失败"

        super().__init__(
            message=message,
            status_code=status_code or status.HTTP_502_BAD_GATEWAY,
        )
        self.service = service


class ServiceUnavailableError(BaseAppException):
    """服务不可用异常"""

    def __init__(self, service: str = "服务", retry_after: int | None = None):
        message = f"{service}暂时不可用"
        if retry_after:
            message += f"，请 {retry_after} 秒后重试"

        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.service = service
        self.retry_after = retry_after


# ================ 配置相关异常 ================


class ConfigurationError(BaseAppException):
    """配置错误异常"""

    def __init__(self, config_key: str = "", message: str = ""):
        if not message:
            message = "配置错误"
            if config_key:
                message += f": {config_key}"

        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        self.config_key = config_key


# ================ 限流相关异常 ================


class RateLimitExceededError(BaseAppException):
    """限流异常"""

    def __init__(
        self,
        limit: int | None = None,
        window: int | None = None,
        retry_after: int | None = None,
    ):
        message = "请求频率超过限制"
        if limit and window:
            message += f" (限制: {limit}次/{window}秒)"
        if retry_after:
            message += f"，请 {retry_after} 秒后重试"

        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


# ================ 文件相关异常 ================


class FileError(BaseAppException):
    """文件操作异常"""

    def __init__(self, message: str, file_path: str = ""):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.file_path = file_path


class FileNotFoundError(FileError):
    """文件不存在异常"""

    def __init__(self, file_path: str = ""):
        message = "文件不存在"
        if file_path:
            message += f": {file_path}"
        super().__init__(message=message, file_path=file_path)


class FileTooLargeError(FileError):
    """文件过大异常"""

    def __init__(self, max_size: int | None = None, file_path: str = ""):
        message = "文件过大"
        if max_size:
            message += f" (最大允许: {max_size} bytes)"
        super().__init__(message=message, file_path=file_path)
        self.max_size = max_size


class UnsupportedFileTypeError(FileError):
    """不支持的文件类型异常"""

    def __init__(self, file_type: str = "", allowed_types: list[str] | None = None):
        message = "不支持的文件类型"
        if file_type:
            message += f": {file_type}"
        if allowed_types:
            message += f" (允许的类型: {', '.join(allowed_types)})"

        super().__init__(message=message)
        self.file_type = file_type
        self.allowed_types = allowed_types or []


# ================ 异常转换工具函数 ================


def database_exception_handler(e: Exception, operation: str = "") -> BaseAppException:
    """
    数据库异常转换器

    将数据库异常转换为对应的业务异常

    Args:
        e: 原始异常
        operation: 操作类型

    Returns:
        转换后的业务异常
    """
    error_msg = str(e).lower()

    # 重复键异常
    if any(keyword in error_msg for keyword in ["duplicate", "unique", "already exists"]):
        return DuplicateRecordError()

    # 外键约束异常
    elif any(keyword in error_msg for keyword in ["foreign key", "constraint"]):
        return DatabaseConstraintError()

    # 记录不存在异常
    elif any(keyword in error_msg for keyword in ["not found", "no such", "does not exist"]):
        return RecordNotFoundError()

    # 其他数据库异常
    else:
        return DatabaseError(message=str(e), operation=operation)


def to_http_exception(e: BaseAppException) -> HTTPException:
    """
    将业务异常转换为FastAPI HTTPException

    Args:
        e: 业务异常

    Returns:
        HTTPException实例
    """
    return HTTPException(
        status_code=e.status_code,
        detail=e.to_dict(),
    )

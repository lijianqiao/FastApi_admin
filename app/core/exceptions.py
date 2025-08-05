"""*- coding: utf-8 -*-.

@Author: li
@Email: lijianqiao2906@live.com
@FileName: exceptions.py
@DateTime: 2025/03/08 04:45:00
@Docs: 应用程序异常处理.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.core.config import settings
from app.utils.logger import logger


class APIError(Exception):
    """API异常基类."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "服务器内部错误",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化API异常.

        Args:
            status_code: HTTP状态码
            message: 错误消息
            detail: 详细信息

        """
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(APIError):
    """资源不存在异常."""

    def __init__(
        self,
        message: str = "请求的资源不存在",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化资源不存在异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_404_NOT_FOUND


class BadRequestException(APIError):
    """错误请求异常."""

    def __init__(
        self,
        message: str = "请求参数错误",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化错误请求异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


class UnauthorizedException(APIError):
    """未授权异常."""

    def __init__(
        self,
        message: str = "未授权访问",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化未授权异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            detail=detail,
        )


class ForbiddenException(APIError):
    """禁止访问异常."""

    def __init__(
        self,
        message: str = "禁止访问",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化禁止访问异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            detail=detail,
        )


class VersionConflictError(APIError):
    """版本冲突异常."""

    def __init__(
        self,
        message: str = "版本冲突",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化版本冲突异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            detail=detail,
        )


class ConflictException(APIError):
    """资源冲突异常."""

    def __init__(
        self,
        message: str = "资源冲突",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化资源冲突异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            detail=detail,
        )


class BusinessException(APIError):
    """业务逻辑异常."""

    def __init__(
        self,
        message: str = "业务逻辑错误",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化业务逻辑异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            detail=detail,
        )


# DAO层专用异常
class DAOException(APIError):
    """DAO层异常基类."""

    def __init__(
        self,
        message: str = "数据访问错误",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化DAO层异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class RecordNotFoundException(DAOException):
    """记录不存在异常."""

    def __init__(
        self,
        message: str = "记录不存在",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化记录不存在异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_404_NOT_FOUND


class DuplicateRecordException(DAOException):
    """重复记录异常."""

    def __init__(
        self,
        message: str = "记录已存在",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化重复记录异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_409_CONFLICT


class DatabaseConnectionException(DAOException):
    """数据库连接异常."""

    def __init__(
        self,
        message: str = "数据库连接失败",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化数据库连接异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class DatabaseTransactionException(DAOException):
    """数据库事务异常."""

    def __init__(
        self,
        message: str = "数据库事务执行失败",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化数据库事务异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ValidationException(DAOException):
    """数据验证异常."""

    def __init__(
        self,
        message: str = "数据验证失败",
        detail: str | dict[str, Any] | None = None,
    ) -> None:
        """初始化数据验证异常.

        Args:
            message: 错误消息
            detail: 详细信息

        """
        super().__init__(
            message=message,
            detail=detail,
        )
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


async def api_exception_handler(_request: Request, exc: APIError) -> Response:
    """API异常处理器.

    Args:
        request (Request): 请求对象
        exc (APIError): API异常

    Returns:
        Response: HTTP响应

    """
    logger.error(f"API异常: {exc.message} - 详细信息: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError | ValidationError) -> Response:
    """验证异常处理器.

    Args:
        request (Request): 请求对象
        exc (Union[RequestValidationError, ValidationError]): 验证异常

    Returns:
        Response: HTTP响应

    """
    error_details = [
        {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]

    logger.error(f"验证异常: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "请求数据验证失败",
            "detail": error_details,
        },
    )


async def tortoise_not_found_exception_handler(_request: Request, exc: DoesNotExist) -> Response:
    """Tortoise ORM 数据不存在异常处理器.

    Args:
        request (Request): 请求对象
        exc (DoesNotExist): 数据不存在异常

    Returns:
        Response: HTTP响应

    """
    logger.error(f"数据不存在异常: {exc!s}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": status.HTTP_404_NOT_FOUND,
            "message": "请求的资源不存在",
            "detail": str(exc),
        },
    )


async def tortoise_integrity_error_handler(_request: Request, exc: IntegrityError) -> Response:
    """Tortoise ORM 完整性约束异常处理器.

    Args:
        request (Request): 请求对象
        exc (IntegrityError): 完整性约束异常

    Returns:
        Response: HTTP响应

    """
    logger.error(f"数据完整性异常: {exc!s}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": status.HTTP_409_CONFLICT,
            "message": "数据完整性约束冲突",
            "detail": str(exc),
        },
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> Response:
    """通用异常处理器.

    Args:
        request (Request): 请求对象
        exc (Exception): 异常

    Returns:
        Response: HTTP响应

    """
    logger.exception(f"未处理的异常: {exc!s}")
    error_message = "服务器内部错误"
    error_detail = None
    if settings.DEBUG:
        error_detail = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": error_message,
            "detail": error_detail,
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器.

    Args:
        app (FastAPI): FastAPI应用实例

    """
    app.add_exception_handler(APIError, api_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DoesNotExist, tortoise_not_found_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, tortoise_integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]

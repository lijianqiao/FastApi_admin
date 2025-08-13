"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_logger.py
@DateTime: 2025/07/08
@Docs: 简化的操作日志装饰器系统
"""

import asyncio
import functools
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.dao.operation_log import OperationLogDAO
from app.utils.logger import logger
from app.utils.request_context import get_request_id


class OperationContext:
    """简化的操作上下文"""

    def __init__(self, operation_type: str, operation_name: str):
        self.operation_id = str(uuid4())
        self.operation_type = operation_type
        self.operation_name = operation_name
        self.user_id: str | None = None
        self.username: str | None = None
        self.resource_type: str | None = None
        self.resource_id: str | None = None
        self.start_time = time.time()
        self.end_time: float | None = None
        self.status = "pending"
        self.error_message: str | None = None
        self.ip_address: str | None = None

    def set_success(self):
        """设置操作成功"""
        self.status = "success"
        self.end_time = time.time()

    def set_error(self, error: Exception | str):
        """设置操作失败"""
        self.status = "error"
        self.end_time = time.time()
        if isinstance(error, Exception):
            detail = getattr(error, "detail", None)
            self.error_message = str(detail) if detail else str(error)
        else:
            self.error_message = error

    def get_duration_ms(self) -> float:
        """获取操作耗时（毫秒）"""
        end_time = self.end_time or time.time()
        return round((end_time - self.start_time) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "operation_id": self.operation_id,
            "user_id": self.user_id,
            "username": self.username,
            "operation_type": self.operation_type,
            "operation_name": self.operation_name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "duration_ms": self.get_duration_ms(),
            "error_message": self.error_message,
            "ip_address": self.ip_address,
            "created_at": datetime.fromtimestamp(self.start_time),
        }


# 简化版本：移除复杂的队列处理，直接使用异步记录


def _extract_basic_info(context: OperationContext, args: tuple, kwargs: dict):
    """提取基本信息：用户信息和资源ID"""
    # 提取用户信息 - 支持多种参数名称
    current_user = kwargs.get("current_user")
    if not current_user:
        # 检查args中的User对象
        for arg in args:
            if hasattr(arg, "id") and hasattr(arg, "username"):
                current_user = arg
                break

    if current_user:
        if isinstance(current_user, dict):
            context.user_id = current_user.get("id")
            context.username = current_user.get("username")
        else:
            context.user_id = str(getattr(current_user, "id", None))
            context.username = getattr(current_user, "username", None)

    # 提取资源ID
    for key in ["id", "user_id", "role_id", "menu_id", "permission_id"]:
        value = kwargs.get(key)
        if value:
            context.resource_id = str(value)
            break

    # 从args中查找UUID类型的参数
    if not context.resource_id:
        for arg in args:
            if isinstance(arg, UUID | str) and len(str(arg)) > 10:
                context.resource_id = str(arg)
                break


def _extract_request_info(context: OperationContext, args: tuple, kwargs: dict):
    """提取请求信息：IP地址"""
    # 从kwargs中查找Request对象
    request = kwargs.get("request") or kwargs.get("req")

    # 从args中查找Request对象
    if not request:
        for arg in args:
            if hasattr(arg, "client") and hasattr(arg, "headers"):
                request = arg
                break

    if request:
        # 提取IP地址
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            context.ip_address = forwarded_for.split(",")[0].strip()
        else:
            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                context.ip_address = real_ip
            else:
                context.ip_address = request.client.host if request.client else "unknown"


async def _log_to_database(context: OperationContext):
    """异步记录到数据库"""
    try:
        operation_log_dao = OperationLogDAO()

        # 构建数据库记录数据
        log_data = {
            "user_id": context.user_id,
            "module": context.resource_type or "unknown",
            "action": context.operation_type,
            "resource_id": context.resource_id,
            "resource_type": context.resource_type,
            "method": _get_http_method(context.operation_type),
            "path": f"/api/{context.resource_type or 'unknown'}",
            "ip_address": context.ip_address or "unknown",
            "response_code": 200 if context.status == "success" else 500,
            "response_time": int(context.get_duration_ms()),
            "description": _build_description(context),
        }

        await operation_log_dao.create(**log_data)
        logger.debug(f"操作日志已保存: {context.operation_id}")
    except Exception as e:
        logger.error(f"保存操作日志失败: {e}")


def _get_http_method(operation_type: str) -> str:
    """根据操作类型获取HTTP方法"""
    mapping = {
        "create": "POST",
        "query": "GET",
        "update": "PUT",
        "delete": "DELETE",
    }
    return mapping.get(operation_type, "POST")


def _build_description(context: OperationContext) -> str:
    """构建操作描述"""
    parts = []
    if context.username:
        parts.append(f"用户: {context.username}")
    if context.operation_name:
        parts.append(f"操作: {context.operation_name}")
    if context.resource_type:
        parts.append(f"资源: {context.resource_type}")
    if context.resource_id:
        parts.append(f"ID: {context.resource_id}")
    if context.error_message:
        parts.append(f"错误: {context.error_message}")
    req_id = get_request_id()
    if req_id:
        parts.append(f"req_id: {req_id}")
    return " | ".join(parts)


def operation_log(operation_type: str, operation_name: str, resource_type: str | None = None) -> Callable:
    """简化的操作日志装饰器

    Args:
        operation_type: 操作类型 (create, query, update, delete)
        operation_name: 操作名称描述
        resource_type: 资源类型
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 创建操作上下文
            context = OperationContext(operation_type, operation_name)
            context.resource_type = resource_type or _extract_resource_type(func)

            # 提取基本信息
            _extract_basic_info(context, args, kwargs)
            _extract_request_info(context, args, kwargs)

            try:
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 设置成功状态
                context.set_success()

                # 异步记录日志
                asyncio.create_task(_log_to_database(context))

                return result

            except Exception as e:
                # 设置错误状态
                context.set_error(e)

                # 异步记录日志
                asyncio.create_task(_log_to_database(context))

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def operation_log_with_context(operation_type: str, operation_name: str, resource_type: str | None = None) -> Callable:
    """增强版操作日志装饰器 - 支持FastAPI依赖注入

    自动从FastAPI的依赖注入中获取OperationContext
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 创建操作上下文
            context = OperationContext(operation_type, operation_name)
            context.resource_type = resource_type or _extract_resource_type(func)

            # 优先从依赖注入中获取OperationContext
            operation_context = kwargs.get("operation_context")
            if not operation_context:
                # 从位置参数中查找包含 user 和 request 属性的 OperationContext
                for arg in args:
                    if hasattr(arg, "user") and hasattr(arg, "request"):
                        operation_context = arg
                        break
            if operation_context:
                # 从依赖注入的上下文中提取信息
                context.user_id = str(operation_context.user.id)
                context.username = operation_context.user.username
                context.ip_address = _extract_ip_from_request(operation_context.request)
                # 注意：不要移除operation_context，业务方法需要这个参数
            else:
                # 降级到原有的提取方式
                _extract_basic_info(context, args, kwargs)
                _extract_request_info(context, args, kwargs)

            # 提取资源ID
            _extract_resource_id_from_params(context, args, kwargs)

            try:
                # 执行原函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 设置成功状态
                context.set_success()

                # 异步记录日志
                asyncio.create_task(_log_to_database(context))

                return result

            except Exception as e:
                # 设置错误状态
                context.set_error(e)

                # 异步记录日志
                asyncio.create_task(_log_to_database(context))

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def _extract_ip_from_request(request) -> str:
    """从Request对象提取IP地址"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def _extract_resource_id_from_params(context: OperationContext, args: tuple, kwargs: dict):
    """从参数中提取资源ID"""
    # 提取资源ID
    for key in ["id", "user_id", "role_id", "menu_id", "permission_id"]:
        value = kwargs.get(key)
        if value:
            context.resource_id = str(value)
            break

    # 从args中查找UUID类型的参数
    if not context.resource_id:
        for arg in args:
            if isinstance(arg, UUID | str) and len(str(arg)) > 10:
                context.resource_id = str(arg)
                break


def _extract_resource_type(func: Callable) -> str:
    """从函数名提取资源类型"""
    module_name = func.__module__
    if "services" in module_name:
        parts = module_name.split(".")
        for part in parts:
            if part != "services" and not part.startswith("app"):
                return part
    return func.__name__.split("_")[0] if "_" in func.__name__ else "unknown"


# 便捷装饰器
def log_create(resource_type: str | None = None) -> Callable:
    """创建操作日志装饰器"""
    return operation_log("create", "创建", resource_type)


def log_update(resource_type: str | None = None) -> Callable:
    """更新操作日志装饰器"""
    return operation_log("update", "更新", resource_type)


def log_delete(resource_type: str | None = None) -> Callable:
    """删除操作日志装饰器"""
    return operation_log("delete", "删除", resource_type)


def log_query(resource_type: str | None = None) -> Callable:
    """查询操作日志装饰器"""
    return operation_log("query", "查询", resource_type)


def log_export(resource_type: str | None = None) -> Callable:
    """导出操作日志装饰器"""
    return operation_log("export", "导出", resource_type)


def log_import(resource_type: str | None = None) -> Callable:
    """导入操作日志装饰器"""
    return operation_log("import", "导入", resource_type)


# 便捷装饰器 - 支持依赖注入
def log_create_with_context(resource_type: str | None = None) -> Callable:
    """创建操作日志装饰器 - 支持依赖注入"""
    return operation_log_with_context("create", "创建", resource_type)


def log_update_with_context(resource_type: str | None = None) -> Callable:
    """更新操作日志装饰器 - 支持依赖注入"""
    return operation_log_with_context("update", "更新", resource_type)


def log_delete_with_context(resource_type: str | None = None) -> Callable:
    """删除操作日志装饰器 - 支持依赖注入"""
    return operation_log_with_context("delete", "删除", resource_type)


def log_query_with_context(resource_type: str | None = None) -> Callable:
    """查询操作日志装饰器 - 支持依赖注入"""
    return operation_log_with_context("query", "查询", resource_type)

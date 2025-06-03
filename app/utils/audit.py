"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: audit.py
@DateTime: 2025/06/03 02:32:03
@Docs: 审计日志装饰器 - 自动记录用户操作
"""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


def audit_log(
    action: str,
    resource: str,
    get_resource_id: Callable[[Any], str] | None = None,
):
    """
    审计日志装饰器

    Args:
        action: 操作类型 (CREATE, UPDATE, DELETE, VIEW)
        resource: 资源类型 (User, Role, Permission)
        get_resource_id: 从结果中提取资源ID的函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 初始化变量，避免在 finally 块中未绑定
            result = None
            status = "FAILED"
            error_message = None

            # 执行原函数
            try:
                result = await func(*args, **kwargs)
                status = "SUCCESS"
                error_message = None
            except Exception as e:
                result = None
                status = "FAILED"
                error_message = str(e)
                logger.error(f"操作失败: {action} {resource}", exc_info=True, extra={"error_message": error_message})
                raise
            finally:
                # 异步记录审计日志
                asyncio.create_task(
                    _create_audit_log(
                        args=args,
                        kwargs=kwargs,
                        result=result,
                        action=action,
                        resource=resource,
                        status=status,
                        error_message=error_message,
                        get_resource_id=get_resource_id,
                    )
                )

            return result

        return wrapper

    return decorator


async def _create_audit_log(
    args: tuple,
    kwargs: dict,
    result: Any,
    action: str,
    resource: str,
    status: str,
    error_message: str | None,
    get_resource_id: Callable[[Any], str] | None,
):
    """创建审计日志记录"""
    try:
        # 提取会话和用户信息
        session = None
        user_id = None
        request = None

        # 从参数中提取session
        for arg in args:
            if isinstance(arg, AsyncSession):
                session = arg
                break

        # 从kwargs中提取参数
        if "session" in kwargs:
            session = kwargs["session"]
        if "current_user" in kwargs:
            user_id = kwargs["current_user"].id
        if "request" in kwargs:
            request = kwargs["request"]

        # 如果没有session，跳过记录
        if not session:
            logger.warning("无法记录审计日志: 未找到数据库会话")
            return

        # 提取资源ID
        resource_id = None
        if get_resource_id and result:
            try:
                resource_id = get_resource_id(result)
            except Exception as e:
                logger.warning(f"提取资源ID失败: {e}")

        # 提取IP和User-Agent
        ip_address = None
        user_agent = None
        if request and isinstance(request, Request):
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # 创建审计日志
        audit_record = AuditLog(
            user_id=str(user_id) if user_id else None,
            action=action,
            resource=resource,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"{action} {resource}",
            error_message=error_message,
        )

        session.add(audit_record)
        await session.commit()

        logger.info(
            f"审计日志记录成功: {action} {resource}",
            extra={
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "status": status,
            },
        )

    except Exception as e:
        logger.error(f"记录审计日志失败: {e}", exc_info=True)


# 常用的装饰器预设
def audit_create(resource: str, get_id: Callable[[Any], str] | None = None):
    """创建操作审计装饰器"""
    return audit_log("CREATE", resource, get_id)


def audit_update(resource: str, get_id: Callable[[Any], str] | None = None):
    """更新操作审计装饰器"""
    return audit_log("UPDATE", resource, get_id)


def audit_delete(resource: str, get_id: Callable[[Any], str] | None = None):
    """删除操作审计装饰器"""
    return audit_log("DELETE", resource, get_id)


def audit_view(resource: str):
    """查看操作审计装饰器"""
    return audit_log("VIEW", resource)


# 辅助函数：提取ID
def get_user_id(result: Any) -> str:
    """从用户结果中提取ID"""
    if hasattr(result, "id"):
        return str(result.id)
    if isinstance(result, dict) and "id" in result:
        return str(result["id"])
    return ""


def get_role_id(result: Any) -> str:
    """从角色结果中提取ID"""
    if hasattr(result, "id"):
        return str(result.id)
    if isinstance(result, dict) and "id" in result:
        return str(result["id"])
    return ""


def get_permission_id(result: Any) -> str:
    """从权限结果中提取ID"""
    if hasattr(result, "id"):
        return str(result.id)
    if isinstance(result, dict) and "id" in result:
        return str(result["id"])
    return ""

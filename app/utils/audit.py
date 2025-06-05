"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: audit_improved.py
@DateTime: 2025/06/03
@Docs: 审计日志装饰器

提供审计日志装饰器、日志记录、ID提取等通用工具，支持事务一致性和异步记录。
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
    use_same_session: bool = True,
):
    """
    改进版审计日志装饰器

    Args:
        action: 操作类型 (CREATE, UPDATE, DELETE, VIEW)
        resource: 资源类型 (User, Role, Permission)
        get_resource_id: 从结果中提取资源ID的函数
        use_same_session: 是否使用同一个会话（确保事务一致性）
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 初始化变量
            result = None
            status = "FAILED"
            error_message = None
            session = None

            # 提取session
            session = _extract_session(args, kwargs)

            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                status = "SUCCESS"
                error_message = None

                # 同步记录审计日志（在同一事务中）
                if use_same_session and session:
                    await _create_audit_log_sync(
                        session=session,
                        args=args,
                        kwargs=kwargs,
                        result=result,
                        action=action,
                        resource=resource,
                        status=status,
                        error_message=error_message,
                        get_resource_id=get_resource_id,
                    )
                else:
                    # 异步记录（使用新会话）
                    await asyncio.create_task(
                        _create_audit_log_async(
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

            except Exception as e:
                result = None
                status = "FAILED"
                error_message = str(e)
                logger.error(f"操作失败: {action} {resource}", exc_info=True, extra={"error_message": error_message})

                # 记录失败的审计日志
                if use_same_session and session:
                    try:
                        await _create_audit_log_sync(
                            session=session,
                            args=args,
                            kwargs=kwargs,
                            result=result,
                            action=action,
                            resource=resource,
                            status=status,
                            error_message=error_message,
                            get_resource_id=get_resource_id,
                        )
                    except Exception as audit_error:
                        logger.error(f"记录失败审计日志时出错: {audit_error}")

                raise

            return result

        return wrapper

    return decorator


def _extract_session(args: tuple, kwargs: dict) -> AsyncSession | None:
    """提取数据库会话"""
    # 从参数中提取session
    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg

    # 从kwargs中提取session
    if "session" in kwargs:
        return kwargs["session"]

    return None


async def _create_audit_log_sync(
    session: AsyncSession,
    args: tuple,
    kwargs: dict,
    result: Any,
    action: str,
    resource: str,
    status: str,
    error_message: str | None,
    get_resource_id: Callable[[Any], str] | None,
):
    """在同一事务中同步创建审计日志"""
    try:
        # 提取用户信息和请求信息
        user_id = None
        request = None

        if "current_user" in kwargs:
            user_id = kwargs["current_user"].id
        if "request" in kwargs:
            request = kwargs["request"]

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

        # 创建审计日志（不自动提交，由主事务控制）
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
        # 注意：不在这里提交，由调用方的事务统一控制

        logger.debug(
            f"审计日志已添加到事务: {action} {resource}",
            extra={
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "status": status,
            },
        )

    except Exception as e:
        logger.error(f"添加审计日志到事务失败: {e}", exc_info=True)


async def _create_audit_log_async(
    args: tuple,
    kwargs: dict,
    result: Any,
    action: str,
    resource: str,
    status: str,
    error_message: str | None,
    get_resource_id: Callable[[Any], str] | None,
):
    """异步创建审计日志（使用新的数据库连接）"""
    from app.db.session import sqlalchemy_config

    try:
        # 使用新的数据库会话
        async with sqlalchemy_config.get_session() as new_session:
            await _create_audit_log_sync(
                session=new_session,
                args=args,
                kwargs=kwargs,
                result=result,
                action=action,
                resource=resource,
                status=status,
                error_message=error_message,
                get_resource_id=get_resource_id,
            )
            await new_session.commit()

            logger.info(
                f"异步审计日志记录成功: {action} {resource}",
                extra={
                    "action": action,
                    "resource": resource,
                    "status": status,
                },
            )

    except Exception as e:
        logger.error(f"异步记录审计日志失败: {e}", exc_info=True)


# 常用的装饰器预设
def audit_create(resource: str, get_id: Callable[[Any], str] | None = None, use_same_session: bool = True):
    """创建操作审计装饰器"""
    return audit_log("CREATE", resource, get_id, use_same_session)


def audit_update(resource: str, get_id: Callable[[Any], str] | None = None, use_same_session: bool = True):
    """更新操作审计装饰器"""
    return audit_log("UPDATE", resource, get_id, use_same_session)


def audit_delete(resource: str, get_id: Callable[[Any], str] | None = None, use_same_session: bool = True):
    """删除操作审计装饰器"""
    return audit_log("DELETE", resource, get_id, use_same_session)


def audit_view(resource: str, use_same_session: bool = False):
    """查看操作审计装饰器（通常使用异步记录）"""
    return audit_log("VIEW", resource, None, use_same_session)


# 辅助函数：提取ID
def get_model_id(result: Any) -> str:
    """通用的模型ID提取函数"""
    if hasattr(result, "id"):
        return str(result.id)
    if isinstance(result, dict) and "id" in result:
        return str(result["id"])
    return ""


def get_user_id(result: Any) -> str:
    """从用户结果中提取ID"""
    return get_model_id(result)


def get_role_id(result: Any) -> str:
    """从角色结果中提取ID"""
    return get_model_id(result)


def get_permission_id(result: Any) -> str:
    """从权限结果中提取ID"""
    return get_model_id(result)

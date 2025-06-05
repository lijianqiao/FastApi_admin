"""
审计日志 API 路由
只读接口，所有接口均为查询和统计
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_async_session
from app.exceptions import RecordNotFoundError
from app.models.models import User
from app.schemas.schemas import AuditLogQuery, AuditLogResponse, PagedResponse
from app.services.audit_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


def get_audit_service(db: AsyncSession = Depends(get_async_session)) -> AuditLogService:
    return AuditLogService(db)


@router.get("/{log_id}", response_model=AuditLogResponse, summary="根据ID获取审计日志")
async def get_audit_log_by_id(
    log_id: int = Path(..., description="审计日志ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> AuditLogResponse:
    """根据ID获取审计日志

    Args:
        log_id: 审计日志ID
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        审计日志对象

    Raises:
        HTTPException: 日志不存在时返回404
    """
    service = AuditLogService(db)
    try:
        return await service.get_audit_log_by_id(log_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/user/{user_id}", response_model=list[AuditLogResponse], summary="获取用户的审计日志")
async def get_user_audit_logs(
    user_id: UUID = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> list[AuditLogResponse]:
    """获取指定用户的审计日志

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量
        offset: 偏移量

    Returns:
        用户的审计日志列表
    """
    service = AuditLogService(db)
    return await service.get_user_audit_logs(user_id=user_id, limit=limit, offset=offset)


@router.get("/latest", response_model=list[AuditLogResponse], summary="获取最新的审计日志")
async def get_latest_audit_logs(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100, description="限制数量"),
) -> list[AuditLogResponse]:
    """获取最新的审计日志

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量

    Returns:
        最新的审计日志列表
    """
    service = AuditLogService(db)
    return await service.get_latest_audit_logs(limit=limit)


@router.get("/", response_model=PagedResponse[AuditLogResponse], summary="条件查询审计日志")
async def query_audit_logs(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    user_id: UUID | None = Query(None, description="用户ID"),
    action: str | None = Query(None, description="操作类型"),
    resource: str | None = Query(None, description="资源类型"),
    status: str | None = Query(None, description="操作状态"),
    start_date: datetime | None = Query(None, description="开始日期"),
    end_date: datetime | None = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=200, description="每页数量"),
    sort_by: str | None = Query(None, description="排序字段"),
    sort_desc: bool = Query(False, description="降序排序"),
    include_deleted: bool = Query(False, description="包含已删除"),
) -> PagedResponse[AuditLogResponse]:
    """根据条件分页查询审计日志

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        user_id: 用户ID
        action: 操作类型
        resource: 资源类型
        status: 操作状态
        start_date: 开始日期
        end_date: 结束日期
        page: 页码
        size: 每页数量
        sort_by: 排序字段
        sort_desc: 是否降序
        include_deleted: 是否包含已删除

    Returns:
        分页的审计日志列表
    """
    service = AuditLogService(db)
    query = AuditLogQuery(
        user_id=user_id,
        action=action,
        resource=resource,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_desc=sort_desc,
        include_deleted=include_deleted,
    )
    return await service.query_audit_logs(query)


@router.get("/action/{action}", response_model=list[AuditLogResponse], summary="根据操作类型获取审计日志")
async def get_audit_logs_by_action(
    action: str = Path(..., description="操作类型"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> list[AuditLogResponse]:
    """根据操作类型获取审计日志

    Args:
        action: 操作类型
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量
        offset: 偏移量

    Returns:
        审计日志列表
    """
    service = AuditLogService(db)
    return await service.get_audit_logs_by_action(action=action, limit=limit, offset=offset)


@router.get("/resource/{resource}", response_model=list[AuditLogResponse], summary="根据资源类型获取审计日志")
async def get_audit_logs_by_resource(
    resource: str = Path(..., description="资源类型"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> list[AuditLogResponse]:
    """根据资源类型获取审计日志

    Args:
        resource: 资源类型
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量
        offset: 偏移量

    Returns:
        审计日志列表
    """
    service = AuditLogService(db)
    return await service.get_audit_logs_by_resource(resource=resource, limit=limit, offset=offset)


@router.get("/failed", response_model=list[AuditLogResponse], summary="获取失败的操作日志")
async def get_failed_operations(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> list[AuditLogResponse]:
    """获取失败的操作日志

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量
        offset: 偏移量

    Returns:
        失败的操作日志列表
    """
    service = AuditLogService(db)
    return await service.get_failed_operations(limit=limit, offset=offset)


@router.get("/date-range", response_model=list[AuditLogResponse], summary="根据日期范围获取审计日志")
async def get_audit_logs_by_date_range(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> list[AuditLogResponse]:
    """根据日期范围获取审计日志

    Args:
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        current_user: 当前认证用户
        limit: 限制数量
        offset: 偏移量

    Returns:
        审计日志列表
    """
    service = AuditLogService(db)
    return await service.get_audit_logs_by_date_range(start_date, end_date, limit=limit, offset=offset)


@router.get("/count/action/{action}", response_model=dict, summary="统计指定操作类型的日志数量")
async def count_logs_by_action(
    action: str = Path(..., description="操作类型"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """统计指定操作类型的日志数量

    Args:
        action: 操作类型
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        包含操作类型和数量的字典
    """
    service = AuditLogService(db)
    count = await service.count_logs_by_action(action)
    return {"action": action, "count": count}


@router.get("/count/user/{user_id}", response_model=dict, summary="统计指定用户的日志数量")
async def count_logs_by_user(
    user_id: UUID = Path(..., description="用户ID"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """统计指定用户的日志数量

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        包含用户ID和数量的字典
    """
    service = AuditLogService(db)
    count = await service.count_logs_by_user(user_id)
    return {"user_id": str(user_id), "count": count}


@router.get("/summary", response_model=dict, summary="获取审计日志统计摘要")
async def get_audit_summary(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """获取审计日志统计摘要

    Args:
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        审计日志统计摘要字典
    """
    service = AuditLogService(db)
    return await service.get_audit_summary()

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log.py
@DateTime: 2025/01/01
@Docs: 操作日志相关的Pydantic模型
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.base import ListQueryRequest, ORMBase, PaginatedResponse
from app.schemas.types import ObjectUUID


class OperationLogBase(ORMBase):
    """操作日志基础字段 (直接映射模型)"""

    module: str = Field(description="操作模块")
    action: str = Field(description="操作动作")
    path: str = Field(description="请求路径")
    method: str = Field(description="请求方法")
    ip_address: str | None = Field(default=None, description="IP地址")
    response_code: int = Field(description="响应状态码")
    response_time: int = Field(description="响应时间（毫秒）")


class OperationLogResponse(OperationLogBase):
    """操作日志响应模型"""

    user_id: ObjectUUID | None = Field(default=None, description="用户ID")
    username: str | None = Field(default=None, description="操作用户名 (服务层填充)")
    details: dict | None = Field(default=None, description="操作详情")


class OperationLogListRequest(ListQueryRequest):
    """操作日志列表查询请求"""

    keyword: str | None = Field(default=None, description="关键字（模块/动作/路径/IP）")
    username: str | None = Field(default=None, description="按用户名模糊搜索")
    status: str | None = Field(default=None, description="状态（success/fail）")
    start_date: date | None = Field(default=None, description="开始日期")
    end_date: date | None = Field(default=None, description="结束日期")


class OperationLogListResponse(PaginatedResponse[OperationLogResponse]):
    """操作日志列表响应"""

    pass


class OperationLogStatisticsRequest(BaseModel):
    """操作日志统计请求"""

    start_date: date
    end_date: date
    user_ids: list[ObjectUUID] | None = Field(default=None, description="用户ID列表")


class OperationLogStatisticsResponse(BaseModel):
    """操作日志统计响应"""

    data: dict

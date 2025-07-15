"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/07/05
@Docs: 基础响应模式
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.types import ObjectUUID


class BaseResponse[DataType](BaseModel):
    """基础响应模式"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="成功", description="响应消息")
    data: DataType | None = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="响应时间")


class BaseRequest(BaseModel):
    """基础请求模式"""

    model_config = ConfigDict(extra="forbid", use_enum_values=True, alias_generator=to_camel, populate_by_name=True)


class ORMBase(BaseRequest):
    """
    所有与ORM模型对应的Pydantic模型的基类。
    自动包含id, version, created_at等通用字段。
    """

    id: ObjectUUID
    version: int = Field(description="数据版本号")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginationRequest(BaseModel):
    """分页请求模式"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")

    model_config = ConfigDict(extra="forbid")


class SoftDeleteRequest(BaseModel):
    """软删除请求模式"""

    include_deleted: bool = Field(default=False, description="是否包含已删除的数据")

    model_config = ConfigDict(extra="forbid")


class RestoreRequest(BaseModel):
    """恢复请求模式"""

    ids: list[ObjectUUID] = Field(description="要恢复的ID列表", min_length=1)

    model_config = ConfigDict(extra="forbid")


class BulkDeleteRequest(BaseModel):
    """批量删除请求模式"""

    ids: list[ObjectUUID] = Field(description="要删除的ID列表", min_length=1)
    hard_delete: bool = Field(default=False, description="是否硬删除")

    model_config = ConfigDict(extra="forbid")


class PaginatedResponse[DataType](BaseModel):
    """分页响应模式"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="成功", description="响应消息")
    data: list[DataType] = Field(default_factory=list, description="响应数据")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页大小")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="响应时间")

    @property
    def total_pages(self) -> int:
        """计算总页数"""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1


class ErrorResponse(BaseModel):
    """错误响应模式"""

    code: int = Field(description="错误代码")
    message: str = Field(description="错误消息")
    detail: Any = Field(default=None, description="错误详情")


class SoftDeletedDataResponse[DataType](BaseModel):
    """软删除数据响应"""

    active_data: list[DataType] = Field(default_factory=list, description="活跃数据")
    deleted_data: list[DataType] = Field(default_factory=list, description="已删除数据")
    active_count: int = Field(default=0, description="活跃数据数量")
    deleted_count: int = Field(default=0, description="已删除数据数量")


class OperationResponse(BaseModel):
    """操作结果响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="操作成功", description="响应消息")
    success_count: int = Field(default=0, description="成功数量")
    failed_count: int = Field(default=0, description="失败数量")
    failed_items: list[dict[str, Any]] = Field(default_factory=list, description="失败项详情")


# 常用响应类型
SuccessResponse = BaseResponse[dict[str, Any]]
ListResponse = BaseResponse[list[dict[str, Any]]]


# ================= 新增基础类 =================


class SearchRequest(BaseModel):
    """搜索请求基类"""

    keyword: str | None = Field(default=None, description="搜索关键词", max_length=100)

    model_config = ConfigDict(extra="forbid")


class FilterRequest(BaseModel):
    """筛选请求基类"""

    is_active: bool | None = Field(default=None, description="是否激活")
    start_date: datetime | None = Field(default=None, description="开始时间")
    end_date: datetime | None = Field(default=None, description="结束时间")

    model_config = ConfigDict(extra="forbid")


class SortRequest(BaseModel):
    """排序请求基类"""

    sort_by: str | None = Field(default=None, description="排序字段")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="排序方向")

    model_config = ConfigDict(extra="forbid")


class ListQueryRequest(PaginationRequest, SearchRequest, FilterRequest, SortRequest):
    """通用列表查询请求（组合分页、搜索、筛选、排序）"""

    include_deleted: bool = Field(default=False, description="是否包含已删除数据")

    model_config = ConfigDict(extra="forbid")


class StatusUpdateRequest(BaseModel):
    """状态更新请求"""

    is_active: bool = Field(description="激活状态")

    model_config = ConfigDict(extra="forbid")


class PasswordUpdateRequest(BaseModel):
    """密码更新请求"""

    old_password: str = Field(description="原密码", min_length=6, max_length=128)
    new_password: str = Field(description="新密码", min_length=6, max_length=128)
    confirm_password: str = Field(description="确认密码", min_length=6, max_length=128)

    model_config = ConfigDict(extra="forbid")


class BulkAssignRequest(BaseModel):
    """批量分配请求"""

    target_ids: list[ObjectUUID] = Field(description="目标ID列表", min_length=1)
    assign_ids: list[ObjectUUID] = Field(description="分配的ID列表", min_length=0)

    model_config = ConfigDict(extra="forbid")


class TreeQueryRequest(BaseModel):
    """树形查询请求"""

    parent_id: ObjectUUID | None = Field(default=None, description="父节点ID")
    include_children: bool = Field(default=True, description="是否包含子节点")
    max_depth: int | None = Field(default=None, ge=1, le=10, description="最大深度")

    model_config = ConfigDict(extra="forbid")


class TreeResponse[NodeType](BaseModel):
    """树形结构响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="成功", description="响应消息")
    data: list[NodeType] = Field(default_factory=list, description="树形数据")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="响应时间")


class StatisticsResponse(BaseModel):
    """统计数据响应"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="成功", description="响应消息")
    data: dict[str, Any] = Field(default_factory=dict, description="统计数据")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="响应时间")


class TokenResponse(BaseModel):
    """Token响应基类"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str | None = Field(default=None, description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")


class AuthRequest(BaseModel):
    """认证请求基类"""

    username: str = Field(description="用户名", min_length=3, max_length=50)
    password: str = Field(description="密码", min_length=6, max_length=128)

    model_config = ConfigDict(extra="forbid")


class BatchOperationRequest(BaseModel):
    """批量操作请求基类"""

    ids: list[ObjectUUID] = Field(description="操作对象ID列表", min_length=1)
    operation: str = Field(description="操作类型")
    params: dict[str, Any] | None = Field(default=None, description="操作参数")

    model_config = ConfigDict(extra="forbid")

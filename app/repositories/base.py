"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/03
@Docs: ORM基类和Repository基类 - 使用 advanced-alchemy 的基类，采用最小最优设计
"""

from abc import ABC
from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from advanced_alchemy.base import BigIntAuditBase, UUIDAuditBase
from advanced_alchemy.filters import CollectionFilter, FilterTypes
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger

logger = get_logger(__name__)

ModelT = TypeVar("ModelT", bound=UUIDAuditBase | BigIntAuditBase)
IdType = TypeVar("IdType", UUID, int)  # ID类型变量，可以是UUID或int


class AbstractBaseRepository(SQLAlchemyAsyncRepository[ModelT], Generic[ModelT, IdType], ABC):
    """
    抽象基础Repository类，提供通用的CRUD操作。

    支持软删除和审计字段，所有具体仓库需继承本类。

    Attributes:
        model_type: 具体模型类型，子类需指定
    """

    model_type: type[ModelT]  # 子类需要指定具体的模型类型

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """
        初始化Repository实例。

        Args:
            session: SQLAlchemy异步会话
            **kwargs: 其他参数
        Raises:
            ValueError: 未指定model_type时抛出
        """
        super().__init__(session=session, **kwargs)
        if not hasattr(self, "model_type") or self.model_type is None:
            raise ValueError("Repository子类必须指定model_type属性")

    def _apply_soft_delete_filter(self, filters: list[FilterTypes], include_deleted: bool) -> list[FilterTypes]:
        """
        辅助方法：如果模型支持软删除且不需要包含已删除记录，则添加软删除过滤器。

        Args:
            filters: 过滤器列表
            include_deleted: 是否包含已删除记录
        Returns:
            处理后的过滤器列表
        """
        if hasattr(self.model_type, "is_deleted") and not include_deleted:
            filters.append(CollectionFilter(field_name="is_deleted", values=[False]))
        return list(filters)  # 返回副本以保持一致性

    async def create_record(self, data: ModelT | dict[str, Any]) -> ModelT:
        """
        创建新的记录。

        Args:
            data: 待创建的数据对象或字典
        Returns:
            创建后的模型对象
        """
        if isinstance(data, dict):
            obj_in = self.model_type(**data)
        else:
            obj_in = data
        return await super().add(obj_in)

    async def get_by_id(
            self, item_id: IdType, auto_expunge: bool = True, include_deleted: bool = False
    ) -> ModelT | None:
        """
        通过ID获取单个记录。

        Args:
            item_id: 记录ID
            auto_expunge: 是否自动expunge
            include_deleted: 是否包含已删除记录
        Returns:
            匹配的模型对象或None
        """
        filters: list[FilterTypes] = [CollectionFilter(field_name="id", values=[item_id])]
        processed_filters = self._apply_soft_delete_filter(filters, include_deleted)
        return await super().get_one_or_none(*processed_filters, auto_expunge=auto_expunge)

    async def get_one_by_field(
            self,
            field_name: str,
            value: Any,
            auto_expunge: bool = True,
            include_deleted: bool = False,
    ) -> ModelT | None:
        """
        根据指定字段和值获取单个记录。

        Args:
            field_name: 字段名
            value: 字段值
            auto_expunge: 是否自动expunge
            include_deleted: 是否包含已删除记录
        Returns:
            匹配的模型对象或None
        Raises:
            AttributeError: 字段不存在时抛出
        """
        if not hasattr(self.model_type, field_name):
            raise AttributeError(f"模型 {self.model_type.__name__} 不存在字段 {field_name}")

        filters: list[FilterTypes] = [CollectionFilter(field_name=field_name, values=[value])]
        processed_filters = self._apply_soft_delete_filter(filters, include_deleted)
        return await super().get_one_or_none(*processed_filters, auto_expunge=auto_expunge)

    async def get_all_records(
            self,
            *filters: FilterTypes,  # 接收可变数量的位置参数作为过滤器
            include_deleted: bool = False,
            auto_expunge: bool = True,
    ) -> Sequence[ModelT]:
        """
        获取所有符合条件的记录。

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除记录
            auto_expunge: 是否自动expunge
        Returns:
            匹配的模型对象序列
        """
        filter_list = list(filters)
        processed_filters = self._apply_soft_delete_filter(filter_list, include_deleted)
        return await super().list(*processed_filters, auto_expunge=auto_expunge)

    async def get_all_by_field(
            self,
            field_name: str,
            value: Any,
            include_deleted: bool = False,
            auto_expunge: bool = True,
            other_filters: Sequence[FilterTypes] | None = None,  # 明确的关键字参数
    ) -> Sequence[ModelT]:
        """
        根据指定字段和值获取所有匹配的记录，可附加其他过滤器。

        Args:
            field_name: 字段名
            value: 字段值
            include_deleted: 是否包含已删除记录
            auto_expunge: 是否自动expunge
            other_filters: 其他过滤器
        Returns:
            匹配的模型对象序列
        Raises:
            AttributeError: 字段不存在时抛出
        """
        if not hasattr(self.model_type, field_name):
            raise AttributeError(f"模型 {self.model_type.__name__} 不存在字段 {field_name}")

        initial_filters: list[FilterTypes] = [CollectionFilter(field_name=field_name, values=[value])]
        if other_filters:
            initial_filters.extend(other_filters)

        processed_filters = self._apply_soft_delete_filter(initial_filters, include_deleted)
        return await super().list(*processed_filters, auto_expunge=auto_expunge)

    async def update_record(self, item_id: IdType, data: ModelT | dict[str, Any]) -> ModelT | None:
        """
        更新指定ID的记录。

        Args:
            item_id: 记录ID
            data: 更新数据对象或字典
        Returns:
            更新后的模型对象或None
        Raises:
            ValueError: 记录不存在时抛出
        """
        db_obj = await self.get_by_id(item_id, include_deleted=False)
        if not db_obj:
            raise ValueError(f"ID为{item_id}的记录不存在")

        if isinstance(data, dict):
            for k, v in data.items():
                setattr(db_obj, k, v)
        else:
            for k, v in data.__dict__.items():
                setattr(db_obj, k, v)
        updated_obj = await super().update(db_obj)
        return updated_obj

    async def delete_record(self, item_id: IdType, hard_delete: bool = False) -> ModelT | None:
        """
        删除指定ID的记录。

        Args:
            item_id: 记录ID
            hard_delete: 是否物理删除（True为物理删除，False为软删除）
        Returns:
            被删除的模型对象或None
        Raises:
            ValueError: 记录不存在时抛出
        """
        db_obj = await self.get_by_id(item_id, include_deleted=True)
        if not db_obj:
            raise ValueError(f"ID为{item_id}的记录不存在")

        # 软删除：仅当实例有 is_deleted 属性时赋值
        if hasattr(db_obj, "is_deleted") and not hard_delete:
            # 直接赋值，类型检查用 ignore 规避
            db_obj.is_deleted = True  # type: ignore[attr-defined]
            await super().update(db_obj)
            return db_obj
        else:
            return await super().delete(db_obj)

    async def record_exists(self, *filters: FilterTypes, include_deleted: bool = False) -> bool:
        """
        检查是否存在符合条件的记录。

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除记录
        Returns:
            存在返回True，否则False
        """
        count = await self.count_records(*filters, include_deleted=include_deleted)
        return count > 0

    async def count_records(self, *filters: FilterTypes, include_deleted: bool = False) -> int:
        """
        计算符合条件的记录数量。

        Args:
            *filters: 过滤器
            include_deleted: 是否包含已删除记录
        Returns:
            记录数量
        """
        filter_list = list(filters)
        processed_filters = self._apply_soft_delete_filter(filter_list, include_deleted)
        return await super().count(*processed_filters)


# 定义具体的Repository类型
UUIDModelT = TypeVar("UUIDModelT", bound=UUIDAuditBase)
BigIntAuditBaseT = TypeVar("BigIntAuditBaseT", bound=BigIntAuditBase)


class BaseRepository(AbstractBaseRepository[UUIDModelT, UUID], Generic[UUIDModelT]):
    """
    基础Repository类，适用于UUID主键并支持审计字段的模型。

    继承自AbstractBaseRepository，封装通用数据访问逻辑。
    """

    pass


class AutoIdBaseRepository(AbstractBaseRepository[BigIntAuditBaseT, int], Generic[BigIntAuditBaseT]):
    """
    自增ID Repository类，适用于自增整数ID并支持审计字段的模型。

    继承自AbstractBaseRepository，封装通用数据访问逻辑。
    """

    pass

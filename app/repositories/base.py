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

from advanced_alchemy.filters import CollectionFilter, FilterTypes
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AutoIdModel, BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel | AutoIdModel)
IdType = TypeVar("IdType", UUID, int)  # ID类型变量，可以是UUID或int


class AbstractBaseRepository(SQLAlchemyAsyncRepository[ModelT], Generic[ModelT, IdType], ABC):
    """
    抽象基础Repository类，提供通用的CRUD操作。
    支持软删除和审计字段。
    """

    model_type: type[ModelT]  # 子类需要指定具体的模型类型

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        super().__init__(session=session, **kwargs)
        if not hasattr(self, "model_type") or self.model_type is None:
            logger.error(f"存储库 {self.__class__.__name__} 必须定义 'model_type' 属性.")
            raise AttributeError(f"存储库 {self.__class__.__name__} 必须定义 'model_type' 属性.")

    def _apply_soft_delete_filter(self, filters: list[FilterTypes], include_deleted: bool) -> list[FilterTypes]:
        """
        辅助方法：如果模型支持软删除且不需要包含已删除记录，则添加软删除过滤器。
        """
        if hasattr(self.model_type, "is_deleted") and not include_deleted:
            has_is_deleted_filter = any(
                isinstance(f, CollectionFilter) and f.field_name == "is_deleted" for f in filters
            )
            if not has_is_deleted_filter:
                # 创建一个新的列表副本进行修改，避免直接修改传入的列表（如果是从 *args 转换来的）
                processed_filters = list(filters)
                processed_filters.append(CollectionFilter(field_name="is_deleted", values=[False]))
                return processed_filters
        return list(filters)  # 返回副本以保持一致性

    async def create_record(self, data: ModelT | dict[str, Any]) -> ModelT:
        """创建新的记录。"""
        if isinstance(data, dict):
            obj_in = self.model_type(**data)
        else:
            obj_in = data
        return await super().add(obj_in)

    async def get_by_id(
        self, item_id: IdType, auto_expunge: bool = True, include_deleted: bool = False
    ) -> ModelT | None:
        """通过ID获取单个记录。"""
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
        """根据指定字段和值获取单个记录。"""
        if not hasattr(self.model_type, field_name):
            logger.error(f"模型 {self.model_type.__name__} 没有字段 {field_name}")
            raise AttributeError(f"模型 {self.model_type.__name__} 没有字段 {field_name}")

        filters: list[FilterTypes] = [CollectionFilter(field_name=field_name, values=[value])]
        processed_filters = self._apply_soft_delete_filter(filters, include_deleted)
        return await super().get_one_or_none(*processed_filters, auto_expunge=auto_expunge)

    async def get_all_records(
        self,
        *filters: FilterTypes,  # 接收可变数量的位置参数作为过滤器
        include_deleted: bool = False,
        auto_expunge: bool = True,
    ) -> Sequence[ModelT]:
        """获取所有符合条件的记录。"""
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
        """根据指定字段和值获取所有匹配的记录，可附加其他过滤器。"""
        if not hasattr(self.model_type, field_name):
            logger.error(f"模型 {self.model_type.__name__} 没有字段 {field_name}")
            raise AttributeError(f"模型 {self.model_type.__name__} 没有字段 {field_name}")

        initial_filters: list[FilterTypes] = [CollectionFilter(field_name=field_name, values=[value])]
        if other_filters:
            initial_filters.extend(other_filters)

        # _apply_soft_delete_filter 内部会创建列表副本
        processed_filters = self._apply_soft_delete_filter(initial_filters, include_deleted)
        return await super().list(*processed_filters, auto_expunge=auto_expunge)

    async def update_record(self, item_id: IdType, data: ModelT | dict[str, Any]) -> ModelT | None:
        """更新指定ID的记录。"""
        db_obj = await self.get_by_id(item_id, include_deleted=False)
        if not db_obj:
            return None

        if isinstance(data, dict):
            for field, value_update in data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value_update)
            updated_obj = await super().update(db_obj)
        else:
            if hasattr(data, "id") and data.id != item_id:  # type: ignore[attr-defined]
                logger.error("在更新期间无法更改现有记录的 ID.")
                raise ValueError("在更新期间无法更改现有记录的 ID.")
            updated_obj = await super().update(data)
        return updated_obj

    async def delete_record(self, item_id: IdType, hard_delete: bool = False) -> ModelT | None:
        """删除指定ID的记录。"""
        db_obj = await self.get_by_id(item_id, include_deleted=True)
        if not db_obj:
            return None

        if hasattr(self.model_type, "is_deleted") and not hard_delete:
            if getattr(db_obj, "is_deleted", False):
                return db_obj
            db_obj.is_deleted = True  # type: ignore[attr-defined]
            # 软删除也是一种更新
            return await super().update(db_obj)
        else:
            # 硬删除，super().delete() 需要主键值
            return await super().delete(item_id)  # type: ignore[arg-type]

    async def record_exists(self, *filters: FilterTypes, include_deleted: bool = False) -> bool:
        """检查是否存在符合条件的记录。"""
        count = await self.count_records(*filters, include_deleted=include_deleted)
        return count > 0

    async def count_records(self, *filters: FilterTypes, include_deleted: bool = False) -> int:
        """计算符合条件的记录数量。"""
        filter_list = list(filters)
        processed_filters = self._apply_soft_delete_filter(filter_list, include_deleted)
        return await super().count(*processed_filters)


# 定义具体的Repository类型
UUIDModelT = TypeVar("UUIDModelT", bound=BaseModel)
AutoIdModelT = TypeVar("AutoIdModelT", bound=AutoIdModel)


class BaseRepository(AbstractBaseRepository[UUIDModelT, UUID], Generic[UUIDModelT]):
    """基础Repository类，适用于UUID主键并支持审计字段的模型。"""

    pass


class AutoIdBaseRepository(AbstractBaseRepository[AutoIdModelT, int], Generic[AutoIdModelT]):
    """自增ID Repository类，适用于自增整数ID并支持审计字段的模型。"""

    pass

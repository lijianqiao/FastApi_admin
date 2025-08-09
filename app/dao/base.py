"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/07/05
@Docs: 基础DAO层，提供高性能的CRUD操作
"""

import asyncio
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction

from app.core.exceptions import (
    DatabaseConnectionException,
    DatabaseTransactionException,
    DuplicateRecordException,
    RecordNotFoundException,
    ValidationException,
    VersionConflictError,
)
from app.models.base import BaseModel
from app.utils.logger import logger

# 定义泛型类型变量
T = TypeVar("T", bound=BaseModel)


class BaseDAO[T: BaseModel]:
    """基础DAO类，提供高性能的数据库操作"""

    def __init__(self, model: type[T]):
        self.model = model

    async def get_by_id(self, id: UUID, include_deleted: bool = True) -> T:
        """根据ID获取单个对象

        Args:
            id: 对象ID
            include_deleted: 是否包含已软删除的对象，默认True

        Returns:
            对象实例

        Raises:
            RecordNotFoundException: 当记录不存在时
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            if include_deleted:
                obj = await self.model.get_or_none(id=id)
            else:
                obj = await self.model.get_or_none(id=id, is_deleted=False)

            if obj is None:
                raise RecordNotFoundException(f"ID为{id}的记录不存在")
            return obj
        except RecordNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取对象失败: {e}")
            raise DatabaseConnectionException(f"数据库查询失败: {str(e)}") from e

    async def get_by_ids(self, ids: list[UUID]) -> list[T]:
        """根据ID列表批量获取对象

        Args:
            ids: 对象ID列表

        Returns:
            对象列表

        Raises:
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            return await self.model.filter(id__in=ids).all()
        except Exception as e:
            logger.error(f"批量获取对象失败: {e}")
            raise DatabaseConnectionException(f"批量查询失败: {str(e)}") from e

    async def get_one(self, include_deleted: bool = True, **filters) -> T:
        """根据条件获取单个对象

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 过滤条件

        Returns:
            对象实例

        Raises:
            RecordNotFoundException: 当记录不存在时
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}
            if not include_deleted:
                valid_filters["is_deleted"] = False
            obj = await self.model.filter(**valid_filters).first()

            if obj is None:
                raise RecordNotFoundException(f"符合条件{valid_filters}的记录不存在")
            return obj
        except RecordNotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取单个对象失败: {e}")
            raise DatabaseConnectionException(f"条件查询失败: {str(e)}") from e

    async def get_all(self, include_deleted: bool = True, **filters) -> list[T]:
        """获取所有对象

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 其他过滤条件

        Returns:
            对象列表

        Raises:
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}
            if not include_deleted:
                valid_filters["is_deleted"] = False
            return await self.model.filter(**valid_filters).all()
        except Exception as e:
            logger.error(f"获取对象列表失败: {e}")
            raise DatabaseConnectionException(f"列表查询失败: {str(e)}") from e

    async def exists(self, include_deleted: bool = True, **filters) -> bool:
        """检查对象是否存在

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 过滤条件

        Returns:
            是否存在

        Raises:
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}
            if not include_deleted:
                valid_filters["is_deleted"] = False
            return await self.model.filter(**valid_filters).exists()
        except Exception as e:
            logger.error(f"检查对象存在性失败: {e}")
            raise DatabaseConnectionException(f"存在性检查失败: {str(e)}") from e

    async def count(self, include_deleted: bool = True, **filters) -> int:
        """获取对象数量

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 过滤条件

        Returns:
            对象数量

        Raises:
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}
            if not include_deleted:
                valid_filters["is_deleted"] = False
            return await self.model.filter(**valid_filters).count()
        except Exception as e:
            logger.error(f"获取对象数量失败: {e}")
            raise DatabaseConnectionException(f"计数查询失败: {str(e)}") from e

    async def create(self, **data) -> T:
        """创建单个对象

        Args:
            **data: 对象数据

        Returns:
            创建的对象实例

        Raises:
            DuplicateRecordException: 当记录重复时
            ValidationException: 当数据验证失败时
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            return await self.model.create(**data)
        except IntegrityError as e:
            logger.error(f"创建对象失败，数据完整性错误: {e}")
            raise DuplicateRecordException(f"记录已存在或违反唯一约束: {str(e)}") from e
        except Exception as e:
            logger.error(f"创建对象失败: {e}")
            raise DatabaseConnectionException(f"创建操作失败: {str(e)}") from e

    async def bulk_create(self, objects_data: list[dict[str, Any]]) -> list[T]:
        """批量创建对象（高性能）

        Args:
            objects_data: 对象数据列表

        Returns:
            创建的对象列表

        Raises:
            ValidationException: 当数据验证失败时
            DatabaseTransactionException: 当批量操作失败时
        """
        try:
            if not objects_data:
                return []
            objects = [self.model(**data) for data in objects_data]
            result = await self.model.bulk_create(objects)
            return result or []
        except IntegrityError as e:
            logger.error(f"批量创建对象失败，数据完整性错误: {e}")
            raise ValidationException(f"批量创建数据验证失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"批量创建对象失败: {e}")
            raise DatabaseTransactionException(f"批量创建操作失败: {str(e)}") from e

    async def bulk_create_ignore_conflicts(
        self, objects_data: list[dict[str, Any]], conflict_fields: list[str] | None = None
    ) -> list[T]:
        """批量创建对象，忽略冲突（INSERT IGNORE模式）

        Args:
            objects_data: 对象数据列表
            conflict_fields: 冲突字段列表

        Returns:
            创建的对象列表

        Raises:
            DatabaseTransactionException: 当批量操作失败时
        """
        try:
            if not objects_data:
                return []

            # 分批处理大量数据
            batch_size = 1000
            all_created = []

            async with in_transaction():
                for i in range(0, len(objects_data), batch_size):
                    batch_data = objects_data[i : i + batch_size]
                    objects = [self.model(**data) for data in batch_data]

                    # 使用on_conflict处理冲突
                    result = await self.model.bulk_create(
                        objects,
                        on_conflict=conflict_fields or ["id"],
                        update_fields=[],  # 空列表表示忽略冲突
                    )
                    if result:
                        all_created.extend(result)

                    logger.debug(f"批量创建对象（忽略冲突）: {len(result or [])}/{len(batch_data)} 条")

            return all_created
        except Exception as e:
            logger.error(f"批量创建对象（忽略冲突）失败: {e}")
            raise DatabaseTransactionException(f"批量创建（忽略冲突）操作失败: {str(e)}") from e

    async def bulk_create_in_batches(self, objects_data: list[dict[str, Any]], batch_size: int = 1000) -> list[T]:
        """分批次批量创建对象（适用于大数据量）

        Args:
            objects_data: 对象数据列表
            batch_size: 批次大小

        Returns:
            创建的对象列表

        Raises:
            DatabaseTransactionException: 当批量操作失败时
        """
        try:
            if not objects_data:
                return []

            all_created = []
            total_batches = (len(objects_data) + batch_size - 1) // batch_size

            async with in_transaction():
                batch_data = []
                batch_num: int | None = None
                for i in range(0, len(objects_data), batch_size):
                    batch_data = objects_data[i : i + batch_size]
                    batch_num = i // batch_size + 1

                try:
                    objects = [self.model(**data) for data in batch_data]
                    result = await self.model.bulk_create(objects)
                    if result:
                        all_created.extend(result)

                    logger.debug(
                        f"批量创建进度: {batch_num}/{total_batches}, 本批次: {len(result or [])}/{len(batch_data)}"
                    )

                except Exception as batch_error:
                    logger.error(f"批次 {batch_num} 创建失败: {batch_error}")

            logger.info(f"分批次批量创建完成: {len(all_created)}/{len(objects_data)} 条")
            return all_created

        except Exception as e:
            logger.error(f"分批次批量创建失败: {e}")
            raise DatabaseTransactionException(f"分批次批量创建操作失败: {str(e)}") from e

    async def update_by_id(self, id: UUID, **data) -> T:
        """根据ID更新对象

        Args:
            id: 对象ID
            **data: 更新数据

        Returns:
            更新后的对象实例

        Raises:
            RecordNotFoundException: 当记录不存在时
            ValidationException: 当数据验证失败时
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            obj = await self.get_by_id(id)
            # 使用 update_from_dict 更新字段，然后使用 save(update_fields) 确保 updated_at 自动更新
            obj.update_from_dict(data)
            # 获取需要更新的字段名称，加上 updated_at 字段
            update_fields = list(data.keys()) + ['updated_at']
            await obj.save(update_fields=update_fields)
            return obj
        except RecordNotFoundException:
            raise
        except IntegrityError as e:
            logger.error(f"更新对象失败，数据完整性错误: {e}")
            raise ValidationException(f"更新数据验证失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"更新对象失败: {e}")
            raise DatabaseConnectionException(f"更新操作失败: {str(e)}") from e

    async def update_by_filter(self, filters: dict[str, Any], **data) -> int:
        """根据条件批量更新

        Args:
            filters: 过滤条件
            **data: 更新数据

        Returns:
            更新的记录数量

        Raises:
            ValidationException: 当数据验证失败时
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 为批量更新添加 updated_at 字段的自动更新
            data['updated_at'] = datetime.now()
            return await self.model.filter(**filters).update(**data)
        except IntegrityError as e:
            logger.error(f"条件更新失败，数据完整性错误: {e}")
            raise ValidationException(f"批量更新数据验证失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"条件更新失败: {e}")
            raise DatabaseConnectionException(f"条件更新操作失败: {str(e)}") from e

    async def bulk_update(self, updates: list[dict[str, Any]], id_field: str = "id") -> int:
        """批量更新对象（高性能）

        Args:
            updates: 更新数据列表
            id_field: ID字段名

        Returns:
            更新的记录数量

        Raises:
            ValidationException: 当数据验证失败时
            DatabaseTransactionException: 当批量操作失败时
        """
        try:
            if not updates:
                return 0

            update_count = 0
            async with in_transaction():
                for update_data in updates:
                    if id_field not in update_data:
                        continue

                    obj_id = update_data.pop(id_field)
                    # 为每个更新添加 updated_at 字段
                    update_data['updated_at'] = datetime.now()
                    count = await self.model.filter(id=obj_id).update(**update_data)
                    update_count += count

            return update_count
        except IntegrityError as e:
            logger.error(f"批量更新对象失败，数据完整性错误: {e}")
            raise ValidationException(f"批量更新数据验证失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"批量更新对象失败: {e}")
            raise DatabaseTransactionException(f"批量更新操作失败: {str(e)}") from e

    async def bulk_update_optimized(
        self, updates: list[dict[str, Any]], id_field: str = "id", batch_size: int = 1000
    ) -> int:
        """优化的批量更新对象（事务处理 + 分批）

        Args:
            updates: 更新数据列表
            id_field: ID字段名
            batch_size: 批次大小

        Returns:
            更新的记录数量

        Raises:
            ValidationException: 当数据验证失败时
            DatabaseTransactionException: 当批量操作失败时
        """
        try:
            if not updates:
                return 0

            total_updated = 0
            total_batches = (len(updates) + batch_size - 1) // batch_size

            for i in range(0, len(updates), batch_size):
                batch_updates = updates[i : i + batch_size]
                batch_num = i // batch_size + 1
                batch_updated = 0

                try:
                    # 使用事务处理每个批次
                    async with in_transaction():
                        for update_data in batch_updates:
                            if id_field not in update_data:
                                continue

                            obj_id = update_data.pop(id_field)
                            # 为每个更新添加 updated_at 字段
                            update_data['updated_at'] = datetime.now()
                            count = await self.model.filter(id=obj_id).update(**update_data)
                            batch_updated += count

                    total_updated += batch_updated
                    logger.debug(
                        f"批量更新进度: {batch_num}/{total_batches}, 本批次: {batch_updated}/{len(batch_updates)}"
                    )

                except Exception as batch_error:
                    logger.error(f"批次 {batch_num} 更新失败: {batch_error}")
                    continue

            logger.info(f"优化批量更新完成: {total_updated}/{len(updates)} 条")
            return total_updated

        except IntegrityError as e:
            logger.error(f"优化批量更新失败，数据完整性错误: {e}")
            raise ValidationException(f"优化批量更新数据验证失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"优化批量更新失败: {e}")
            raise DatabaseTransactionException(f"优化批量更新操作失败: {str(e)}") from e

    async def delete_by_id(self, id: UUID, soft: bool = True) -> bool:
        """根据ID删除对象

        Args:
            id: 对象ID
            soft: 是否软删除（默认True）

        Returns:
            是否删除成功
        """
        if soft:
            return await self.soft_delete_by_id(id)
        else:
            return await self.hard_delete_by_id(id)

    async def delete_by_ids(self, ids: list[UUID], soft: bool = True) -> int:
        """根据ID列表批量删除

        Args:
            ids: 对象ID列表
            soft: 是否软删除（默认True）

        Returns:
            删除的数量
        """
        if soft:
            return await self.soft_delete_by_ids(ids)
        else:
            return await self.hard_delete_by_ids(ids)

    async def delete_by_filter(self, soft: bool = True, **filters) -> int:
        """根据条件批量删除

        Args:
            soft: 是否软删除（默认True）
            **filters: 过滤条件

        Returns:
            删除的数量
        """
        if soft:
            return await self.soft_delete_by_filter(**filters)
        else:
            return await self.hard_delete_by_filter(**filters)

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: list[str] | None = None,
        include_deleted: bool = True,
        **filters,
    ) -> tuple[list[T], int]:
        """分页获取对象（高性能）

        Args:
            page: 页码，从1开始
            page_size: 每页大小
            order_by: 排序字段列表
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 其他过滤条件

        Returns:
            (对象列表, 总数)的元组

        Raises:
            DatabaseConnectionException: 当数据库连接失败时
        """
        try:
            # 计算偏移量
            offset = (page - 1) * page_size

            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}

            # 添加软删除过滤条件
            if not include_deleted:
                valid_filters["is_deleted"] = False

            # 构建查询
            q_objects = filters.pop("q_objects", [])
            queryset = self.model.filter(*q_objects, **valid_filters)

            # 添加排序
            if order_by:
                queryset = queryset.order_by(*order_by)

            # 同时执行计数和分页查询（并行执行提高性能）
            total_task = queryset.count()
            objects_task = queryset.offset(offset).limit(page_size).all()

            total, objects = await asyncio.gather(total_task, objects_task)

            return objects, total
        except Exception as e:
            logger.error(f"分页获取对象失败: {e}")
            raise DatabaseConnectionException(f"分页查询失败: {str(e)}") from e

    def get_queryset(self, include_deleted: bool = True, **filters) -> QuerySet[T]:
        """获取查询集，用于复杂查询

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **filters: 过滤条件

        Returns:
            QuerySet查询集
        """
        # 过滤掉None值，避免ORM查询异常
        valid_filters = {k: v for k, v in filters.items() if v is not None}
        if not include_deleted:
            valid_filters["is_deleted"] = False
        return self.model.filter(**valid_filters)

    async def bulk_upsert(
        self, objects_data: list[dict[str, Any]], conflict_fields: list[str], update_fields: list[str] | None = None
    ) -> list[T]:
        """批量插入或更新（UPSERT操作）"""
        try:
            # 如果没有指定更新字段，则更新除冲突字段外的所有字段
            if update_fields is None:
                if objects_data:
                    update_fields = [key for key in objects_data[0].keys() if key not in conflict_fields]
                else:
                    update_fields = []

            objects = [self.model(**data) for data in objects_data]
            result = await self.model.bulk_create(objects, on_conflict=conflict_fields, update_fields=update_fields)
            return result or []
        except Exception as e:
            logger.error(f"批量UPSERT失败: {e}")
            return []

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **kwargs) -> tuple[T, bool]:
        """获取或创建对象"""
        try:
            return await self.model.get_or_create(defaults=defaults, **kwargs)
        except Exception as e:
            logger.error(f"获取或创建对象失败: {e}")
            # 返回默认值 - 创建一个新对象
            if defaults:
                data = {**kwargs, **defaults}
            else:
                data = kwargs
            obj = self.model(**data)
            return obj, True

    # 软删除方法
    async def soft_delete_by_id(self, id: UUID) -> bool:
        """根据ID软删除对象（标记为已删除）"""
        try:
            count = await self.model.filter(id=id, is_deleted=False).update(is_deleted=True)
            return count > 0
        except Exception as e:
            logger.error(f"软删除对象失败: {e}")
            return False

    async def soft_delete_by_ids(self, ids: list[UUID]) -> int:
        """根据ID列表批量软删除"""
        try:
            return await self.model.filter(id__in=ids, is_deleted=False).update(is_deleted=True)
        except Exception as e:
            logger.error(f"批量软删除对象失败: {e}")
            return 0

    async def soft_delete_by_filter(self, **filters) -> int:
        """根据条件批量软删除"""
        try:
            # 添加is_deleted=False条件，避免重复软删除
            filters["is_deleted"] = False
            return await self.model.filter(**filters).update(is_deleted=True)
        except Exception as e:
            logger.error(f"条件软删除失败: {e}")
            return 0

    # 硬删除方法（物理删除）
    async def hard_delete_by_id(self, id: UUID) -> bool:
        """根据ID硬删除对象（物理删除）"""
        try:
            obj = await self.get_by_id(id)
            if obj:
                await obj.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"硬删除对象失败: {e}")
            return False

    async def hard_delete_by_ids(self, ids: list[UUID]) -> int:
        """根据ID列表批量硬删除"""
        try:
            return await self.model.filter(id__in=ids).delete()
        except Exception as e:
            logger.error(f"批量硬删除对象失败: {e}")
            return 0

    async def hard_delete_by_filter(self, **filters) -> int:
        """根据条件批量硬删除"""
        try:
            return await self.model.filter(**filters).delete()
        except Exception as e:
            logger.error(f"条件硬删除失败: {e}")
            return 0

    # 恢复软删除的对象
    async def restore_by_id(self, id: UUID) -> bool:
        """恢复软删除的对象"""
        try:
            count = await self.model.filter(id=id, is_deleted=True).update(is_deleted=False)
            return count > 0
        except Exception as e:
            logger.error(f"恢复对象失败: {e}")
            return False

    async def restore_by_ids(self, ids: list[UUID]) -> int:
        """批量恢复软删除的对象"""
        try:
            return await self.model.filter(id__in=ids, is_deleted=True).update(is_deleted=False)
        except Exception as e:
            logger.error(f"批量恢复对象失败: {e}")
            return 0

    # 便利方法 - 针对特定状态的查询
    async def get_active_by_id(self, id: UUID) -> T | None:
        """根据ID获取未删除的对象（便利方法）"""
        return await self.get_by_id(id, include_deleted=False)

    async def get_active_all(self, **filters) -> list[T]:
        """获取所有未删除的对象（便利方法）"""
        return await self.get_all(include_deleted=False, **filters)

    async def get_deleted_all(self, **filters) -> list[T]:
        """获取所有已软删除的对象"""
        try:
            filters["is_deleted"] = True
            return await self.model.filter(**filters).all()
        except Exception as e:
            logger.error(f"获取已删除对象列表失败: {e}")
            return []

    async def count_active(self, **filters) -> int:
        """统计未删除对象的数量（便利方法）"""
        return await self.count(include_deleted=False, **filters)

    async def count_deleted(self, **filters) -> int:
        """统计已软删除对象的数量"""
        try:
            filters["is_deleted"] = True
            return await self.model.filter(**filters).count()
        except Exception as e:
            logger.error(f"统计已删除对象数量失败: {e}")
            return 0

    async def get_active_paginated(
        self, page: int = 1, page_size: int = 10, order_by: list[str] | None = None, **filters
    ) -> tuple[list[T], int]:
        """分页获取未删除的对象（便利方法）"""
        return await self.get_paginated(page, page_size, order_by, include_deleted=False, **filters)

    async def update_with_optimistic_lock(self, obj_to_update: T, data_to_update: dict) -> T:
        """
        使用乐观锁更新对象。

        Args:
            obj_to_update: 从数据库获取的、包含当前版本号的模型实例。
            data_to_update: 需要更新的字段字典。

        Raises:
            VersionConflictError: 如果版本不匹配，说明数据已被修改。
            DoesNotExist: 如果对象已被物理删除。

        Returns:
            更新后的模型实例。
        """
        current_version = obj_to_update.version
        # 添加 updated_at 字段的自动更新和版本号递增
        update_data = {**data_to_update, "version": current_version + 1, "updated_at": datetime.now()}

        # 执行原子性的 UPDATE ... WHERE version = ? 操作
        rows_affected = await self.model.filter(id=obj_to_update.id, version=current_version).update(**update_data)

        if rows_affected == 0:
            # 更新失败，检查是因为对象不存在还是版本冲突
            exists = await self.model.filter(id=obj_to_update.id).exists()
            if not exists:
                raise DoesNotExist("对象已被物理删除，无法更新。")
            else:
                raise VersionConflictError(f"对象 {obj_to_update.id} 的数据版本已过期，请刷新后重试。")

        # 更新成功后，刷新本地实例以获取最新数据
        await obj_to_update.refresh_from_db(fields=list(update_data.keys()))
        return obj_to_update

    async def get_or_none(self, **kwargs: Any) -> T | None:
        """
        根据条件获取单个对象，如果不存在则返回 None。

        !!! a "提示"
            在覆盖此方法或实现新的查询方法时，请务C<prefetch_related>
            或 C<select_related> 来优化关联查询，避免 N+1 问题。

            - 使用 `select_related` 预加载 **一对一** 或 **多对一** 关系。
            - 使用 `prefetch_related` 预加载 **一对多** 或 **多对多** 关系。

        Args:
            **kwargs: 查询条件

        Returns:
            单个模型实例或 None
        """
        return await self.model.get_or_none(**kwargs)

    # 新增通用查询方法
    async def find_by_fields(self, include_deleted: bool = True, **fields) -> list[T]:
        """根据多个字段查询对象

        Args:
            include_deleted: 是否包含已软删除的对象，默认True
            **fields: 字段条件

        Returns:
            对象列表
        """
        try:
            if not include_deleted:
                fields["is_deleted"] = False
            return await self.model.filter(**fields).all()
        except Exception as e:
            logger.error(f"按字段查询失败: {e}")
            return []

    async def find_like(self, field: str, value: str, include_deleted: bool = True) -> list[T]:
        """模糊查询

        Args:
            field: 字段名
            value: 查询值
            include_deleted: 是否包含已软删除的对象，默认True

        Returns:
            对象列表
        """
        try:
            if include_deleted:
                filter_dict = {f"{field}__icontains": value}
            else:
                filter_dict = {f"{field}__icontains": value, "is_deleted": False}
            return await self.model.filter(**filter_dict).all()
        except Exception as e:
            logger.error(f"模糊查询失败: {e}")
            return []

    async def find_in_range(
        self, field: str, start_value: Any, end_value: Any, include_deleted: bool = True
    ) -> list[T]:
        """范围查询

        Args:
            field: 字段名
            start_value: 开始值
            end_value: 结束值
            include_deleted: 是否包含已软删除的对象，默认True

        Returns:
            对象列表
        """
        try:
            if include_deleted:
                filter_dict = {f"{field}__gte": start_value, f"{field}__lte": end_value}
            else:
                filter_dict = {f"{field}__gte": start_value, f"{field}__lte": end_value, "is_deleted": False}
            return await self.model.filter(**filter_dict).all()
        except Exception as e:
            logger.error(f"范围查询失败: {e}")
            return []

    # 关联查询优化方法
    async def get_with_related(
        self,
        id: UUID,
        select_related: list[str] | None = None,
        prefetch_related: list[str] | None = None,
        include_deleted: bool = True,
    ) -> T | None:
        """根据ID获取对象，预加载关联数据

        Args:
            id: 对象ID
            select_related: 一对一或多对一关联字段列表
            prefetch_related: 一对多或多对多关联字段列表
            include_deleted: 是否包含已软删除的对象

        Returns:
            对象实例或None
        """
        try:
            if include_deleted:
                queryset = self.model.filter(id=id)
            else:
                queryset = self.model.filter(id=id, is_deleted=False)

            if select_related:
                queryset = queryset.select_related(*select_related)
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)

            return await queryset.first()
        except Exception as e:
            logger.error(f"获取关联对象失败: {e}")
            return None

    async def get_all_with_related(
        self,
        select_related: list[str] | None = None,
        prefetch_related: list[str] | None = None,
        include_deleted: bool = True,
        **filters,
    ) -> list[T]:
        """获取所有对象，预加载关联数据

        Args:
            select_related: 一对一或多对一关联字段列表
            prefetch_related: 一对多或多对多关联字段列表
            include_deleted: 是否包含已软删除的对象
            **filters: 其他过滤条件

        Returns:
            对象列表
        """
        try:
            if not include_deleted:
                filters["is_deleted"] = False

            queryset = self.model.filter(**filters)

            if select_related:
                queryset = queryset.select_related(*select_related)
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)

            return await queryset.all()
        except Exception as e:
            logger.error(f"获取关联对象列表失败: {e}")
            return []

    async def get_paginated_with_related(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: list[str] | None = None,
        select_related: list[str] | None = None,
        prefetch_related: list[str] | None = None,
        include_deleted: bool = True,
        **filters,
    ) -> tuple[list[T], int]:
        """分页获取对象，预加载关联数据（高性能）

        Args:
            page: 页码，从1开始
            page_size: 每页大小
            order_by: 排序字段列表
            select_related: 一对一或多对一关联字段列表
            prefetch_related: 一对多或多对多关联字段列表
            include_deleted: 是否包含已软删除的对象
            **filters: 其他过滤条件

        Returns:
            (对象列表, 总数)的元组
        """
        try:
            # 计算偏移量
            offset = (page - 1) * page_size

            # 从过滤器中提取Q对象
            q_objects = filters.pop("q_objects", [])

            # 过滤掉None值，避免ORM查询异常
            valid_filters = {k: v for k, v in filters.items() if v is not None}

            # 添加软删除过滤条件
            if not include_deleted:
                valid_filters["is_deleted"] = False

            # 构建查询
            queryset = self.model.filter(*q_objects, **valid_filters)

            # 添加关联查询优化
            if select_related:
                queryset = queryset.select_related(*select_related)
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)

            # 添加排序
            if order_by:
                queryset = queryset.order_by(*order_by)

            # 先执行计数查询（不包含关联，提高性能）
            count_queryset = self.model.filter(*q_objects, **valid_filters)
            total = await count_queryset.count()

            # 再执行分页查询（包含关联）
            objects = await queryset.offset(offset).limit(page_size).all()

            return objects, total
        except Exception as e:
            logger.error(f"分页获取关联对象失败: {e}")
            return [], 0

    def get_queryset_with_related(
        self,
        select_related: list[str] | None = None,
        prefetch_related: list[str] | None = None,
        include_deleted: bool = True,
        **filters,
    ) -> QuerySet[T]:
        """获取查询集，预加载关联数据

        Args:
            select_related: 一对一或多对一关联字段列表
            prefetch_related: 一对多或多对多关联字段列表
            include_deleted: 是否包含已软删除的对象
            **filters: 其他过滤条件

        Returns:
            QuerySet查询集
        """
        if not include_deleted:
            filters["is_deleted"] = False

        queryset = self.model.filter(**filters)

        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        return queryset

    async def bulk_soft_delete_optimized(self, ids: list[UUID], batch_size: int = 1000) -> int:
        """优化的批量软删除（事务处理 + 分批）

        Args:
            ids: 要删除的对象ID列表
            batch_size: 每批处理的数量，默认1000

        Returns:
            删除的对象数量
        """
        try:
            if not ids:
                return 0

            total_deleted = 0
            total_batches = (len(ids) + batch_size - 1) // batch_size

            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                batch_num = i // batch_size + 1
                batch_deleted = 0

                try:
                    # 使用事务处理每个批次
                    async with in_transaction():
                        batch_deleted = await self.model.filter(id__in=batch_ids, is_deleted=False).update(
                            is_deleted=True
                        )

                    total_deleted += batch_deleted
                    logger.debug(
                        f"批量软删除进度: {batch_num}/{total_batches}, 本批次: {batch_deleted}/{len(batch_ids)}"
                    )

                except Exception as batch_error:
                    logger.error(f"批次 {batch_num} 软删除失败: {batch_error}")
                    continue

            logger.info(f"优化批量软删除完成: {total_deleted}/{len(ids)} 条")
            return total_deleted

        except Exception as e:
            logger.error(f"优化批量软删除失败: {e}")
            return 0

    async def bulk_restore_optimized(self, ids: list[UUID], batch_size: int = 1000) -> int:
        """优化的批量恢复（事务处理 + 分批）

        Args:
            ids: 要恢复的对象ID列表
            batch_size: 每批处理的数量，默认1000

        Returns:
            恢复的对象数量
        """
        try:
            if not ids:
                return 0

            total_restored = 0
            total_batches = (len(ids) + batch_size - 1) // batch_size

            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                batch_num = i // batch_size + 1
                batch_restored = 0

                try:
                    # 使用事务处理每个批次
                    async with in_transaction():
                        batch_restored = await self.model.filter(id__in=batch_ids, is_deleted=True).update(
                            is_deleted=False
                        )

                    total_restored += batch_restored
                    logger.debug(
                        f"批量恢复进度: {batch_num}/{total_batches}, 本批次: {batch_restored}/{len(batch_ids)}"
                    )

                except Exception as batch_error:
                    logger.error(f"批次 {batch_num} 恢复失败: {batch_error}")
                    continue

            logger.info(f"优化批量恢复完成: {total_restored}/{len(ids)} 条")
            return total_restored

        except Exception as e:
            logger.error(f"优化批量恢复失败: {e}")
            return 0

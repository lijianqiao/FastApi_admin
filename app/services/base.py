"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/07/05
@Docs: 基础服务类
"""

from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException
from tortoise.exceptions import DoesNotExist

from app.core.exceptions import VersionConflictError
from app.dao.base import BaseDAO
from app.models.base import BaseModel
from app.schemas.types import ModelDict
from app.utils.deps import OperationContext

# 定义泛型类型变量
T = TypeVar("T", bound=BaseModel)


class BaseService[T: BaseModel]:
    """
    基础服务类，使用DAO层进行数据操作，并提供钩子函数。

    钩子函数 (Hooks):
    - 单个对象操作:
        - `before_create(data)`: 在创建对象之前调用。
        - `after_create(obj)`: 在创建对象之后调用。
        - `before_update(obj, data)`: 在更新对象之前调用。
        - `after_update(obj)`: 在更新对象之后调用。
    - 批量操作:
        - `before_bulk_create(data_list)`: 在批量创建之前调用。
        - `after_bulk_create(obj_list)`: 在批量创建之后调用。
        - `before_bulk_update(update_list)`: 在批量更新之前调用。
        - `before_update_by_filter(filters, data)`: 在按条件更新之前调用。

    注意：为了保持高性能，批量更新操作 (`bulk_update`, `update_by_filter`)
    不提供 `after` 钩子，因为这些操作通常不会返回更新后的对象列表。
    """

    def __init__(self, dao: BaseDAO[T]):
        """
        初始化服务，接受具体的DAO实例

        Args:
            dao: 具体的DAO实例（如UserDAO、RoleDAO等）
        """
        self.dao = dao
        self.model = dao.model

    # ------------------- 钩子函数 (Hooks) -------------------
    async def before_create(self, data: ModelDict) -> ModelDict:
        """创建对象前的钩子函数"""
        return data

    async def after_create(self, obj: T) -> None:
        """创建对象后的钩子函数"""
        pass

    async def before_update(self, obj: T, data: ModelDict) -> ModelDict:
        """更新对象前的钩子函数"""
        return data

    async def after_update(self, obj: T) -> None:
        """更新对象后的钩子函数"""
        pass

    async def before_bulk_create(self, objects_data: list[ModelDict]) -> list[ModelDict]:
        """批量创建前的钩子函数"""
        return objects_data

    async def after_bulk_create(self, objects: list[T]) -> None:
        """批量创建后的钩子函数"""
        pass

    async def before_bulk_update(self, updates: list[ModelDict]) -> list[ModelDict]:
        """批量更新前的钩子函数"""
        return updates

    async def before_update_by_filter(self, filters: ModelDict, data: ModelDict) -> tuple[ModelDict, ModelDict]:
        """按条件更新前的钩子函数"""
        return filters, data

    # ------------------- CRUD基础操作 -------------------
    async def get_by_id(self, id: UUID) -> T | None:
        """根据ID获取单个对象"""
        return await self.dao.get_by_id(id)

    async def get_by_ids(self, ids: list[UUID]) -> list[T]:
        """根据ID列表批量获取对象"""
        return await self.dao.get_by_ids(ids)

    async def get_one(self, **filters) -> T | None:
        """根据条件获取单个对象"""
        return await self.dao.get_one(**filters)

    async def get_all(self, **filters) -> list[T]:
        """获取所有对象"""
        return await self.dao.get_all(**filters)

    async def exists(self, **filters) -> bool:
        """检查对象是否存在"""
        return await self.dao.exists(**filters)

    async def count(self, **filters) -> int:
        """获取对象数量"""
        return await self.dao.count(**filters)

    async def create(self, operation_context: OperationContext, **data) -> T | None:
        """创建对象，并触发 pre/post 钩子"""
        processed_data = await self.before_create(data)
        obj = await self.dao.create(**processed_data)
        if obj:
            await self.after_create(obj)
        return obj

    async def bulk_create(self, objects_data: list[dict[str, Any]]) -> list[T]:
        """批量创建对象，并触发钩子"""
        processed_data = await self.before_bulk_create(objects_data)
        objects = await self.dao.bulk_create(processed_data)
        if objects:
            await self.after_bulk_create(objects)
        return objects

    async def update(self, id: UUID, operation_context: OperationContext, **data) -> T | None:
        """
        更新对象，并触发 pre/post 钩子。
        此方法现在集成了乐观锁。
        """
        version = data.pop("version", None)
        if version is None:
            raise HTTPException(status_code=400, detail="更新请求必须包含 version 字段以进行乐观锁校验。")

        obj = await self.dao.get_by_id(id)
        if not obj:
            return None

        # 预检查：提前拦截掉版本不匹配的请求
        if obj.version != version:
            raise HTTPException(
                status_code=409,  # 409 Conflict 是最适合此场景的状态码
                detail=f"数据版本已过期，服务器当前版本为 {obj.version}，您提交的版本为 {version}。请刷新后重试。",
            )

        # 执行 before 钩子
        processed_data = await self.before_update(obj, data)

        try:
            # 调用新的、带乐观锁的DAO方法
            updated_obj = await self.dao.update_with_optimistic_lock(obj, processed_data)
        except VersionConflictError as e:
            # 捕获DAO层抛出的版本冲突异常
            raise HTTPException(status_code=409, detail=str(e)) from e
        except DoesNotExist as e:
            # 捕获对象可能已被物理删除的异常
            raise HTTPException(status_code=404, detail=str(e)) from e

        # 执行 after 钩子
        if updated_obj:
            await self.after_update(updated_obj)

        return updated_obj

    async def bulk_update(self, updates: list[dict[str, Any]], id_field: str = "id") -> int:
        """批量更新对象，并触发 before 钩子"""
        processed_updates = await self.before_bulk_update(updates)
        return await self.dao.bulk_update(processed_updates, id_field)

    async def update_by_filter(self, filters: dict[str, Any], **data) -> int:
        """根据条件批量更新，并触发 before 钩子"""
        processed_filters, processed_data = await self.before_update_by_filter(filters, data)
        return await self.dao.update_by_filter(processed_filters, **processed_data)

    async def delete(self, id: UUID, operation_context: OperationContext) -> bool:
        """删除对象（软删除）"""
        return await self.dao.delete_by_id(id)

    async def delete_by_ids(self, ids: list[UUID], operation_context: OperationContext) -> int:
        """批量删除对象（软删除）"""
        return await self.dao.delete_by_ids(ids)

    async def delete_by_filter(self, **filters) -> int:
        """根据条件批量删除（软删除）"""
        return await self.dao.delete_by_filter(**filters)

    async def get_paginated(
        self, page: int = 1, page_size: int = 10, order_by: list[str] | None = None, **filters
    ) -> tuple[list[T], int]:
        """分页获取对象"""
        return await self.dao.get_paginated(page, page_size, order_by, **filters)

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **kwargs) -> tuple[T, bool]:
        """获取或创建对象"""
        return await self.dao.get_or_create(defaults, **kwargs)

    async def bulk_upsert(
        self, objects_data: list[dict[str, Any]], conflict_fields: list[str], update_fields: list[str] | None = None
    ) -> list[T]:
        """批量插入或更新"""
        return await self.dao.bulk_upsert(objects_data, conflict_fields, update_fields)

    # 硬删除方法（物理删除）
    async def hard_delete(self, id: UUID) -> bool:
        """硬删除对象（物理删除）"""
        return await self.dao.hard_delete_by_id(id)

    async def hard_delete_by_ids(self, ids: list[UUID]) -> int:
        """批量硬删除对象"""
        return await self.dao.hard_delete_by_ids(ids)

    async def hard_delete_by_filter(self, **filters) -> int:
        """根据条件批量硬删除"""
        return await self.dao.hard_delete_by_filter(**filters)

    # 恢复方法
    async def restore(self, id: UUID) -> bool:
        """恢复软删除的对象"""
        return await self.dao.restore_by_id(id)

    async def restore_by_ids(self, ids: list[UUID]) -> int:
        """批量恢复软删除的对象"""
        return await self.dao.restore_by_ids(ids)

    # 查询增强方法（保留常用的便利方法）
    async def get_active_all(self, **filters) -> list[T]:
        """获取所有未删除的对象"""
        return await self.dao.get_active_all(**filters)

    async def count_active(self, **filters) -> int:
        """统计未删除对象的数量"""
        return await self.dao.count_active(**filters)

    # ------------------- 关联查询优化方法 -------------------
    async def get_with_related(
        self, id: UUID, select_related: list[str] | None = None, prefetch_related: list[str] | None = None
    ) -> T | None:
        """根据ID获取对象（关联查询优化）"""
        return await self.dao.get_with_related(id, select_related, prefetch_related)

    async def get_all_with_related(
        self, select_related: list[str] | None = None, prefetch_related: list[str] | None = None, **filters
    ) -> list[T]:
        """获取所有对象（关联查询优化）"""
        objects, _ = await self.dao.get_paginated_with_related(
            page=1,
            page_size=10000,  # 设置足够大的页面大小获取所有记录
            select_related=select_related,
            prefetch_related=prefetch_related,
            **filters,
        )
        return objects

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
        """分页获取对象（关联查询优化）"""

        result = await self.dao.get_paginated_with_related(
            page, page_size, order_by, select_related, prefetch_related, include_deleted, **filters
        )

        return result

    # ------------------- 通用业务方法 -------------------
    async def activate(self, id: UUID) -> bool:
        """激活对象（设置is_active=True）"""
        try:
            count = await self.dao.update_by_filter({"id": id, "is_deleted": False}, is_active=True)
            return count > 0
        except Exception:
            return False

    async def deactivate(self, id: UUID) -> bool:
        """停用对象（设置is_active=False）"""
        try:
            count = await self.dao.update_by_filter({"id": id, "is_deleted": False}, is_active=False)
            return count > 0
        except Exception:
            return False

    async def bulk_activate(self, ids: list[UUID]) -> int:
        """批量激活对象"""
        try:
            return await self.dao.update_by_filter({"id__in": ids, "is_deleted": False}, is_active=True)
        except Exception:
            return 0

    async def bulk_deactivate(self, ids: list[UUID]) -> int:
        """批量停用对象"""
        try:
            return await self.dao.update_by_filter({"id__in": ids, "is_deleted": False}, is_active=False)
        except Exception:
            return 0

    async def bulk_create_optimized(self, objects_data: list[dict[str, Any]], batch_size: int = 1000) -> list[T]:
        """批量创建对象（支持大数据量）"""
        processed_data = await self.before_bulk_create(objects_data)
        objects = await self.dao.bulk_create_in_batches(processed_data, batch_size)
        if objects:
            await self.after_bulk_create(objects)
        return objects

    async def bulk_create_ignore_conflicts(
        self, objects_data: list[dict[str, Any]], conflict_fields: list[str] | None = None
    ) -> list[T]:
        """批量创建对象，忽略冲突"""
        processed_data = await self.before_bulk_create(objects_data)
        objects = await self.dao.bulk_create_ignore_conflicts(processed_data, conflict_fields)
        if objects:
            await self.after_bulk_create(objects)
        return objects

    async def bulk_update_optimized(
        self, updates: list[dict[str, Any]], id_field: str = "id", batch_size: int = 1000
    ) -> int:
        """批量更新对象"""
        processed_updates = await self.before_bulk_update(updates)
        return await self.dao.bulk_update_optimized(processed_updates, id_field, batch_size)

    async def bulk_delete_optimized(self, ids: list[UUID], batch_size: int = 1000) -> int:
        """批量删除（使用分批处理）"""
        # 使用现有的批量删除方法，分批处理大数据量
        if len(ids) <= batch_size:
            return await self.dao.delete_by_ids(ids)

        total_deleted = 0
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            deleted_count = await self.dao.delete_by_ids(batch_ids)
            total_deleted += deleted_count
        return total_deleted

    async def bulk_restore_optimized(self, ids: list[UUID], batch_size: int = 1000) -> int:
        """批量恢复（使用分批处理）"""
        # 使用现有的批量恢复方法，分批处理大数据量
        if len(ids) <= batch_size:
            return await self.dao.restore_by_ids(ids)

        total_restored = 0
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            restored_count = await self.dao.restore_by_ids(batch_ids)
            total_restored += restored_count
        return total_restored

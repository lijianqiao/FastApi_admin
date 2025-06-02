"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/02 23:30:00
@Docs: 仓库基类 - 基于 advanced-alchemy 的企业级数据访问层

提供统一的CRUD操作、分页查询、批量操作等企业级功能
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import UUIDAuditBase
from app.models.schemas.schemas import PageQuery, PageResponse
from app.utils.logger import get_logger

# 类型变量
ModelType = TypeVar("ModelType", bound=UUIDAuditBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = get_logger(__name__)


class BaseRepository(SQLAlchemyAsyncRepository[ModelType], Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    企业级仓库基类

    基于 advanced-alchemy 提供统一的数据访问接口，包含：
    - 标准CRUD操作
    - 分页查询
    - 批量操作
    - 审计日志
    - 查询优化
    """

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """初始化仓库"""
        super().__init__(session=session, **kwargs)
        self.logger = logger

    # ===================== 基础CRUD操作 =====================

    async def create_record(self, data: CreateSchemaType, *, auto_commit: bool = True) -> ModelType:
        """
        创建记录

        Args:
            data: 创建数据
            auto_commit: 是否自动提交事务

        Returns:
            创建的模型实例
        """
        try:
            # 转换为字典
            if isinstance(data, BaseModel):
                create_data = data.model_dump(exclude_unset=True)
            else:
                create_data = data

            # 创建模型实例
            model_instance = self.model_type(**create_data)

            # 使用 advanced-alchemy 的 add 方法
            instance = await self.add(model_instance, auto_commit=auto_commit)

            self.logger.info("创建记录成功", extra={"model": self.model_type.__name__, "id": instance.id})
            return instance

        except Exception as e:
            create_data = data.model_dump(exclude_unset=True) if isinstance(data, BaseModel) else data
            self.logger.error(f"创建记录失败: {e}", extra={"model": self.model_type.__name__, "data": create_data})
            raise

    async def get_by_id(self, id_: UUID | str) -> ModelType | None:
        """
        根据ID获取记录

        Args:
            id_: 记录ID

        Returns:
            模型实例或None
        """
        try:
            instance = await self.get(id_)
            return instance

        except Exception as e:
            self.logger.error(f"获取记录失败: {e}", extra={"model": self.model_type.__name__, "id": id_})
            raise

    async def update_record(
        self, id_: UUID | str, data: UpdateSchemaType | dict[str, Any], *, auto_commit: bool = True
    ) -> ModelType:
        """
        更新记录

        Args:
            id_: 记录ID
            data: 更新数据
            auto_commit: 是否自动提交事务

        Returns:
            更新后的模型实例
        """
        try:
            # 获取现有实例
            existing_instance = await self.get(id_)
            if not existing_instance:
                raise ValueError(f"Record with id {id_} not found")

            # 转换为字典
            if isinstance(data, BaseModel):
                update_data = data.model_dump(exclude_unset=True)
            else:
                update_data = data

            # 更新实例属性
            for key, value in update_data.items():
                if hasattr(existing_instance, key):
                    setattr(existing_instance, key, value)

            # 使用 advanced-alchemy 的 update 方法 - 需要传入模型实例
            instance = await self.update(existing_instance, auto_commit=auto_commit)

            self.logger.info("更新记录成功", extra={"model": self.model_type.__name__, "id": id_})
            return instance

        except Exception as e:
            self.logger.error(f"更新记录失败: {e}", extra={"model": self.model_type.__name__, "id": id_})
            raise

    async def delete_record(self, id_: UUID | str, *, auto_commit: bool = True) -> bool:
        """
        删除记录

        Args:
            id_: 记录ID
            auto_commit: 是否自动提交事务

        Returns:
            是否删除成功
        """
        try:
            # 硬删除 - 移除软删除相关逻辑
            await self.delete(id_, auto_commit=auto_commit)
            self.logger.info("删除记录成功", extra={"model": self.model_type.__name__, "id": id_})
            return True

        except Exception as e:
            self.logger.error(f"删除记录失败: {e}", extra={"model": self.model_type.__name__, "id": id_})
            return False

    # ===================== 查询操作 =====================

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        where_clauses: list[Any] | None = None,
        order_by: list[Any] | None = None,
    ) -> list[ModelType]:
        """
        获取多条记录

        Args:
            skip: 跳过数量
            limit: 限制数量
            where_clauses: 查询条件
            order_by: 排序条件

        Returns:
            模型实例列表
        """
        try:
            statement = select(self.model_type)

            # 添加查询条件
            if where_clauses:
                statement = statement.where(and_(*where_clauses))

            # 添加排序
            if order_by:
                statement = statement.order_by(*order_by)
            else:
                # 默认按创建时间倒序
                if hasattr(self.model_type, "created_at"):
                    statement = statement.order_by(desc(self.model_type.created_at))

            # 分页
            statement = statement.offset(skip).limit(limit)

            # 执行查询
            result = await self.session.execute(statement)
            instances = result.scalars().all()

            return list(instances)

        except Exception as e:
            self.logger.error(f"查询多条记录失败: {e}", extra={"model": self.model_type.__name__})
            raise

    async def get_paginated(
        self,
        page_query: PageQuery,
        *,
        where_clauses: list[Any] | None = None,
        search_fields: list[str] | None = None,
        search_term: str | None = None,
    ) -> PageResponse[ModelType]:
        """
        分页查询

        Args:
            page_query: 分页查询参数
            where_clauses: 查询条件
            search_fields: 搜索字段
            search_term: 搜索关键词

        Returns:
            分页响应
        """
        try:
            # 构建基础查询
            statement = select(self.model_type)
            count_statement = select(func.count(self.model_type.id))

            # 添加查询条件
            conditions = []
            if where_clauses:
                conditions.extend(where_clauses)

            # 搜索条件
            if search_term and search_fields:
                search_conditions = []
                for field in search_fields:
                    if hasattr(self.model_type, field):
                        attr = getattr(self.model_type, field)
                        search_conditions.append(attr.ilike(f"%{search_term}%"))

                if search_conditions:
                    conditions.append(or_(*search_conditions))

            if conditions:
                where_clause = and_(*conditions)
                statement = statement.where(where_clause)
                count_statement = count_statement.where(where_clause)

            # 排序
            if page_query.sort_by:
                if hasattr(self.model_type, page_query.sort_by):
                    order_column = getattr(self.model_type, page_query.sort_by)
                    if page_query.sort_order == "desc":
                        statement = statement.order_by(desc(order_column))
                    else:
                        statement = statement.order_by(order_column)
            else:
                # 默认按创建时间倒序
                if hasattr(self.model_type, "created_at"):
                    statement = statement.order_by(desc(self.model_type.created_at))

            # 分页
            offset = (page_query.page - 1) * page_query.size
            statement = statement.offset(offset).limit(page_query.size)

            # 执行查询
            count_result = await self.session.execute(count_statement)
            total = count_result.scalar() or 0

            result = await self.session.execute(statement)
            items = result.scalars().all()

            # 计算分页信息
            total_pages = (total + page_query.size - 1) // page_query.size
            has_next = page_query.page < total_pages
            has_prev = page_query.page > 1

            return PageResponse(
                items=list(items),
                total=total,
                page=page_query.page,
                size=page_query.size,
                pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
            )

        except Exception as e:
            self.logger.error(f"分页查询失败: {e}", extra={"model": self.model_type.__name__})
            raise

    # ===================== 批量操作 =====================

    async def bulk_create(self, data_list: list[CreateSchemaType], *, auto_commit: bool = True) -> list[ModelType]:
        """
        批量创建记录

        Args:
            data_list: 创建数据列表
            auto_commit: 是否自动提交事务

        Returns:
            创建的模型实例列表
        """
        try:
            # 转换数据为模型实例
            instances = []
            for data in data_list:
                if isinstance(data, BaseModel):
                    create_data = data.model_dump(exclude_unset=True)
                else:
                    create_data = data
                instance = self.model_type(**create_data)
                instances.append(instance)

            # 使用 advanced-alchemy 的 add_many 方法
            result_instances = await self.add_many(instances, auto_commit=auto_commit)

            self.logger.info(
                "批量创建记录成功", extra={"model": self.model_type.__name__, "count": len(result_instances)}
            )
            return list(result_instances)

        except Exception as e:
            self.logger.error(
                f"批量创建记录失败: {e}", extra={"model": self.model_type.__name__, "count": len(data_list)}
            )
            raise

    async def bulk_update(self, updates: list[dict[str, Any]], *, auto_commit: bool = True) -> list[ModelType]:
        """
        批量更新记录

        Args:
            updates: 更新数据列表，每个包含id和更新字段
            auto_commit: 是否自动提交事务

        Returns:
            更新的模型实例列表
        """
        try:
            instances = []
            for update_data in updates:
                id_ = update_data.pop("id")
                instance = await self.update_record(id_, update_data, auto_commit=False)
                instances.append(instance)

            if auto_commit:
                await self.session.commit()

            self.logger.info("批量更新记录成功", extra={"model": self.model_type.__name__, "count": len(instances)})
            return instances

        except Exception as e:
            self.logger.error(
                f"批量更新记录失败: {e}", extra={"model": self.model_type.__name__, "count": len(updates)}
            )
            await self.session.rollback()
            raise

    async def bulk_delete(self, ids: list[UUID | str], *, auto_commit: bool = True) -> bool:
        """
        批量删除记录

        Args:
            ids: 记录ID列表
            auto_commit: 是否自动提交事务

        Returns:
            是否删除成功
        """
        try:
            for id_ in ids:
                await self.delete_record(id_, auto_commit=False)

            if auto_commit:
                await self.session.commit()

            self.logger.info("批量删除记录成功", extra={"model": self.model_type.__name__, "count": len(ids)})
            return True

        except Exception as e:
            self.logger.error(f"批量删除记录失败: {e}", extra={"model": self.model_type.__name__, "count": len(ids)})
            await self.session.rollback()
            return False

    # ===================== 统计查询 =====================

    async def count_records(self, *, where_clauses: list[Any] | None = None) -> int:
        """
        统计记录数量

        Args:
            where_clauses: 查询条件

        Returns:
            记录数量
        """
        try:
            statement = select(func.count(self.model_type.id))

            # 添加查询条件
            if where_clauses:
                statement = statement.where(and_(*where_clauses))

            result = await self.session.execute(statement)
            return result.scalar() or 0

        except Exception as e:
            self.logger.error(f"统计记录失败: {e}", extra={"model": self.model_type.__name__})
            raise

    async def exists_record(self, *, where_clauses: list[Any] | None = None) -> bool:
        """
        检查记录是否存在

        Args:
            where_clauses: 查询条件

        Returns:
            是否存在
        """
        try:
            count = await self.count_records(where_clauses=where_clauses)
            return count > 0

        except Exception as e:
            self.logger.error(f"检查记录存在性失败: {e}", extra={"model": self.model_type.__name__})
            raise

    # ===================== 便捷方法 =====================

    async def get_by_field(self, field: str, value: Any) -> ModelType | None:
        """
        根据字段值查询记录

        Args:
            field: 字段名
            value: 字段值

        Returns:
            模型实例或None
        """
        try:
            if not hasattr(self.model_type, field):
                raise ValueError(f"字段 {field} 不存在于模型 {self.model_type.__name__}")

            conditions = [getattr(self.model_type, field) == value]
            statement = select(self.model_type).where(and_(*conditions))
            result = await self.session.execute(statement)
            return result.scalar_one_or_none()

        except Exception as e:
            self.logger.error(
                f"根据字段查询失败: {e}", extra={"model": self.model_type.__name__, "field": field, "value": value}
            )
            raise

    async def get_all_by_field(self, field: str, value: Any) -> list[ModelType]:
        """
        根据字段值查询所有匹配记录

        Args:
            field: 字段名
            value: 字段值

        Returns:
            模型实例列表
        """
        try:
            if not hasattr(self.model_type, field):
                raise ValueError(f"字段 {field} 不存在于模型 {self.model_type.__name__}")

            conditions = [getattr(self.model_type, field) == value]
            return await self.get_multi(where_clauses=conditions)

        except Exception as e:
            self.logger.error(
                f"根据字段查询所有记录失败: {e}",
                extra={"model": self.model_type.__name__, "field": field, "value": value},
            )
            raise

    async def search(
        self,
        search_term: str,
        search_fields: list[str],
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        搜索记录

        Args:
            search_term: 搜索关键词
            search_fields: 搜索字段列表
            skip: 跳过数量
            limit: 限制数量

        Returns:
            匹配的模型实例列表
        """
        try:
            if not search_term or not search_fields:
                return []

            # 构建搜索条件
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_type, field):
                    attr = getattr(self.model_type, field)
                    search_conditions.append(attr.ilike(f"%{search_term}%"))

            if not search_conditions:
                return []

            where_clauses = [or_(*search_conditions)]

            return await self.get_multi(skip=skip, limit=limit, where_clauses=where_clauses)

        except Exception as e:
            self.logger.error(
                f"搜索记录失败: {e}",
                extra={"model": self.model_type.__name__, "search_term": search_term, "search_fields": search_fields},
            )
            raise

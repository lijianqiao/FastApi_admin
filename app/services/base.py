"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/03
@Docs: 服务层基类 - 专注业务逻辑，分页和事务管理
"""

import logging
from abc import ABC
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Any, Generic

from advanced_alchemy.filters import FilterTypes
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import database_exception_handler
from app.repositories import AbstractBaseRepository, IdType, ModelT
from app.schemas.schemas import BaseQuery, PagedResponse
from app.utils.logger import get_logger


class AppBaseService(Generic[ModelT, IdType], ABC):
    """
    应用服务层基类。
    提供分页、事务管理等企业级功能，专注业务逻辑。
    """

    # 子类必须定义的属性
    repository_type: type[AbstractBaseRepository[ModelT, IdType]]

    # 可选的 Pydantic 模型定义
    create_schema: type[BaseModel] | None = None
    update_schema: type[BaseModel] | None = None
    response_schema: type[BaseModel] | None = None

    def __init__(self, session: AsyncSession):
        """
        初始化服务。

        Args:
            session: SQLAlchemy 异步会话实例。
        """
        self.session: AsyncSession = session
        self.logger: logging.Logger = get_logger(self.__class__.__name__)

        if not hasattr(self, "repository_type") or self.repository_type is None:
            self.logger.error(f"服务 {self.__class__.__name__} 必须定义 'repository_type' 属性。")
            raise AttributeError(
                f"服务 {self.__class__.__name__} 必须定义 'repository_type' 属性，"
                f"指向一个继承自 AbstractBaseRepository 的 Repository 类。"
            )

        self.repository: AbstractBaseRepository[ModelT, IdType] = self.repository_type(session=self.session)
        self.logger.info(f"服务 {self.__class__.__name__} 已初始化，使用仓库 {self.repository.__class__.__name__}")

    # ==================== 基础 CRUD 操作 ====================
    async def get_record_by_id(self, item_id: IdType, include_deleted: bool = False) -> ModelT | None:
        """
        通过ID获取单个记录。

        Args:
            item_id: 记录ID
            include_deleted: 是否包含已删除的记录
        """
        self.logger.debug(f"服务层: 正在通过 ID {item_id} 获取 {self.repository.model_type.__name__}...")

        record = await self.repository.get_by_id(item_id, include_deleted=include_deleted)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.repository.model_type.__name__} 未找到"
            )

        return record

    async def create_record_svc(self, data: BaseModel | dict[str, Any], commit: bool = True) -> ModelT:
        """
        创建新的记录。

        Args:
            data: 创建数据
            commit: 是否自动提交事务
        """
        self.logger.debug(f"服务层: 正在创建 {self.repository.model_type.__name__} 记录...")

        # 数据校验
        validated_data = await self._validate_create_data(data)

        # 业务逻辑验证（子类可重写）
        await self._before_create(validated_data)

        # 创建记录
        record = await self.repository.create_record(validated_data)

        if commit:
            await self.session.commit()
            await self.session.refresh(record)

        # 创建后处理（子类可重写）
        await self._after_create(record)

        return record

    async def update_record_svc(
        self, item_id: IdType, data: BaseModel | dict[str, Any], commit: bool = True
    ) -> ModelT | None:
        """
        更新指定ID的记录。

        Args:
            item_id: 记录ID
            data: 更新数据
            commit: 是否自动提交事务
        """
        self.logger.debug(f"服务层: 正在更新 ID 为 {item_id} 的 {self.repository.model_type.__name__} 记录...")

        # 检查记录是否存在
        existing_record = await self.repository.get_by_id(item_id)
        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.repository.model_type.__name__} 未找到"
            )

        # 数据校验
        validated_data = await self._validate_update_data(data, existing_record)

        # 业务逻辑验证（子类可重写）
        await self._before_update(existing_record, validated_data)

        # 更新记录
        updated_record = await self.repository.update_record(item_id, validated_data)

        if commit:
            await self.session.commit()
            if updated_record:
                await self.session.refresh(updated_record)

        # 更新后处理（子类可重写）
        if updated_record:
            await self._after_update(updated_record)

        return updated_record

    async def delete_record_svc(self, item_id: IdType, hard_delete: bool = False, commit: bool = True) -> ModelT | None:
        """
        删除指定ID的记录。

        Args:
            item_id: 记录ID
            hard_delete: 是否硬删除
            commit: 是否自动提交事务
        """
        self.logger.debug(
            f"服务层: 正在删除 ID 为 {item_id} 的 {self.repository.model_type.__name__} 记录 (硬删除: {hard_delete})..."
        )

        # 检查记录是否存在
        existing_record = await self.repository.get_by_id(item_id)
        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.repository.model_type.__name__} 未找到"
            )

        # 业务逻辑验证（子类可重写）
        await self._before_delete(existing_record)

        # 删除记录
        deleted_record = await self.repository.delete_record(item_id, hard_delete=hard_delete)

        if commit:
            await self.session.commit()

        # 删除后处理（子类可重写）
        if deleted_record:
            await self._after_delete(deleted_record)

        return deleted_record

    # ==================== 分页和查询 ====================

    async def list_records_paginated(
        self,
        pagination: BaseQuery,
        *filters: FilterTypes,
        include_deleted: bool = False,
    ) -> PagedResponse[ModelT]:
        """
        分页获取记录列表 - 支持Repository的FilterTypes。

        Args:
            pagination: 分页参数
            *filters: Repository支持的过滤器
            include_deleted: 是否包含已删除的记录
        """
        self.logger.debug(f"服务层: 正在分页查询 {self.repository.model_type.__name__} 记录...")

        # 应用业务级别的过滤器（子类可重写）
        processed_filters = await self._apply_business_filters(list(filters))

        # 获取总数
        total = await self.repository.count_records(*processed_filters, include_deleted=include_deleted)

        # 获取分页数据
        offset = (pagination.page - 1) * pagination.size
        records = await self.repository.list(
            *processed_filters, limit=pagination.size, offset=offset, auto_expunge=True
        )

        return PagedResponse[ModelT](
            items=records,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size,
        )

    async def list_records_paginated_dict(
        self,
        pagination: BaseQuery,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> PagedResponse[ModelT]:
        """
        分页获取记录列表 - 支持字典过滤器（为向后兼容保留）。

        Args:
            pagination: 分页参数
            filters: 字典格式过滤条件
            include_deleted: 是否包含已删除的记录
        """
        self.logger.debug(f"服务层: 正在分页查询 {self.repository.model_type.__name__} 记录...")

        # 应用业务级别的过滤器
        final_filters = await self._apply_business_filters_dict(filters or {})

        # 构建查询条件
        filter_conditions = self._build_filter_conditions(final_filters)

        # 获取总数
        total = await self.repository.count_records(*filter_conditions, include_deleted=include_deleted)

        # 获取分页数据
        offset = (pagination.page - 1) * pagination.size
        records = await self.repository.list(
            *filter_conditions, limit=pagination.size, offset=offset, auto_expunge=True
        )

        return PagedResponse[ModelT](
            items=records,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size,
        )

    async def list_all_records_svc(
        self, *filters: FilterTypes, include_deleted: bool = False, auto_expunge: bool = True
    ) -> Sequence[ModelT]:
        """
        获取所有符合条件的记录。
        """
        self.logger.debug(f"服务层: 正在列出所有 {self.repository.model_type.__name__} 记录...")

        # 应用业务级别的过滤器
        processed_filters = await self._apply_business_filters(list(filters))

        return await self.repository.get_all_records(
            *processed_filters, include_deleted=include_deleted, auto_expunge=auto_expunge
        )

    async def count_all_records_svc(self, *filters: FilterTypes, include_deleted: bool = False) -> int:
        """
        计算符合条件的记录数量。
        """
        self.logger.debug(f"服务层: 正在计算 {self.repository.model_type.__name__} 记录数量...")

        # 应用业务级别的过滤器
        processed_filters = await self._apply_business_filters(list(filters))

        return await self.repository.count_records(*processed_filters, include_deleted=include_deleted)

    # ==================== 响应数据转换 ====================

    def _transform_response(self, record: ModelT) -> dict[str, Any] | ModelT:
        """
        转换响应数据（子类可重写）。

        Args:
            record: ORM模型实例

        Returns:
            转换后的响应数据
        """
        if self.response_schema:
            # 使用指定的响应模式转换
            return self.response_schema.model_validate(record).model_dump()
        return record

    def _transform_response_list(self, records: Sequence[ModelT]) -> list[dict[str, Any] | ModelT]:
        """
        批量转换响应数据。
        """
        return [self._transform_response(record) for record in records]

    # ==================== 事务管理 ====================

    @asynccontextmanager
    async def transaction(self):
        if self.session.in_transaction():  # 检查是否已在事务中
            self.logger.debug("加入现有事务...")
            try:
                yield self.session
            except Exception as e:
                self.logger.error(f"嵌套事务块中发生错误: {e}", exc_info=True)
                raise  # 错误冒泡到外层事务处理
        else:
            self.logger.debug("开始新事务...")
            async with self.session.begin():  # begin() 会自动处理提交和回滚
                try:
                    yield self.session
                    self.logger.debug("事务块成功完成（等待外部begin()提交）。")
                # SQLAlchemyError 和其他 Exception 会导致 begin() 自动回滚
                except Exception as e:  # 重新抛出，让调用者知道
                    self.logger.error(f"事务中发生错误: {e}", exc_info=True)
                    raise
            self.logger.debug("事务已结束（已提交或回滚）。")

    # ==================== 异常处理 ====================

    def _handle_database_error(self, e: Exception, operation: str) -> None:
        """
        处理数据库异常（子类可重写）。

        Args:
            e: 异常实例
            operation: 操作类型（create/update/delete）
        """
        self.logger.error(f"数据库操作失败 [{operation}]: {e}")

        # 使用统一的异常转换器
        business_exception = database_exception_handler(e, operation)
        raise business_exception

    # ==================== 数据校验钩子（子类可重写） ====================

    async def _validate_create_data(self, data: BaseModel | dict[str, Any]) -> dict[str, Any]:
        """验证创建数据"""
        if self.create_schema and isinstance(data, dict):
            validated = self.create_schema(**data)
            return validated.model_dump(exclude_unset=True)
        elif isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True)
        return data if isinstance(data, dict) else {}

    async def _validate_update_data(self, data: BaseModel | dict[str, Any], existing_record: ModelT) -> dict[str, Any]:
        """验证更新数据"""
        if self.update_schema and isinstance(data, dict):
            validated = self.update_schema(**data)
            return validated.model_dump(exclude_unset=True)
        elif isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True)
        return data if isinstance(data, dict) else {}

    # ==================== 业务逻辑钩子（子类可重写） ====================

    async def _before_create(self, data: dict[str, Any]) -> None:
        """创建前的业务逻辑"""
        pass

    async def _after_create(self, record: ModelT) -> None:
        """创建后的业务逻辑"""
        pass

    async def _before_update(self, existing_record: ModelT, data: dict[str, Any]) -> None:
        """更新前的业务逻辑"""
        pass

    async def _after_update(self, record: ModelT) -> None:
        """更新后的业务逻辑"""
        pass

    async def _before_delete(self, record: ModelT) -> None:
        """删除前的业务逻辑"""
        pass

    async def _after_delete(self, record: ModelT) -> None:
        """删除后的业务逻辑"""
        pass

    # ==================== 过滤器相关 ====================

    async def _apply_business_filters(self, filters: list[FilterTypes]) -> list[FilterTypes]:
        """应用业务级别的过滤器（如数据权限）"""
        # 子类可以重写这个方法来实现业务逻辑过滤
        return filters

    async def _apply_business_filters_dict(self, filters: dict[str, Any]) -> dict[str, Any]:
        """应用业务级别的字典过滤器"""
        # 子类可以重写这个方法来实现业务逻辑过滤
        return filters

    def _build_filter_conditions(self, filters: dict[str, Any]) -> list[FilterTypes]:
        """构建SQLAlchemy的过滤条件。"""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.repository.model_type, key):
                column = getattr(self.repository.model_type, key)
                if isinstance(value, list):
                    conditions.append(column.in_(value))
                else:
                    conditions.append(column == value)
        return conditions

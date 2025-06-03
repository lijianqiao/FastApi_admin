"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/03
@Docs: 服务层基类 (参照 advanced_alchemy 模式重构)
"""

import logging
from abc import ABC
from collections.abc import Sequence  # 确保导入 Sequence
from typing import Any, Generic

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import AbstractBaseRepository, IdType, ModelT
from app.utils.logger import get_logger  # 导入你提供的日志记录器


class AppBaseService(Generic[ModelT, IdType], ABC):
    """
    应用服务层基类。
    每个具体服务类需要定义 `repository_type` 属性，
    该属性指向一个继承自 `AbstractBaseRepository[ModelT, IdType]` 的具体 Repository 类。
    """

    # 子类必须定义 repository_type
    # 例如: repository_type = UserRepository (其中 UserRepository 继承自 BaseRepository[User])
    repository_type: type[AbstractBaseRepository[ModelT, IdType]]

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

    async def get_record_by_id(self, item_id: IdType, include_deleted: bool = False) -> ModelT | None:
        """
        通过ID获取单个记录。
        此方法直接调用 Repository 层对应的方法。
        """
        self.logger.debug(f"服务层: 正在通过 ID {item_id} 获取 {self.repository.model_type.__name__}...")
        return await self.repository.get_by_id(item_id, include_deleted=include_deleted)

    async def create_record_svc(self, data: ModelT | dict[str, Any]) -> ModelT:
        """
        创建新的记录。
        具体服务类应覆盖此方法或实现自己的创建方法，以包含业务逻辑、
        数据校验和应用审计日志装饰器。
        此基类方法提供了一个直接到底层 Repository 的通道。
        """
        self.logger.debug(f"服务层: 正在创建 {self.repository.model_type.__name__} 记录...")
        # 注意：这里假设 data 已经是 Repository 层期望的格式
        return await self.repository.create_record(data)

    async def update_record_svc(self, item_id: IdType, data: ModelT | dict[str, Any]) -> ModelT | None:
        """
        更新指定ID的记录。
        具体服务类应覆盖此方法或实现自己的更新方法。
        """
        self.logger.debug(f"服务层: 正在更新 ID 为 {item_id} 的 {self.repository.model_type.__name__} 记录...")
        return await self.repository.update_record(item_id, data)

    async def delete_record_svc(self, item_id: IdType, hard_delete: bool = False) -> ModelT | None:
        """
        删除指定ID的记录。
        具体服务类应覆盖此方法或实现自己的删除方法。
        """
        self.logger.debug(
            f"服务层: 正在删除 ID 为 {item_id} 的 {self.repository.model_type.__name__} 记录 (硬删除: {hard_delete})..."
        )
        return await self.repository.delete_record(item_id, hard_delete=hard_delete)

    async def list_all_records_svc(
        self, *filters: Any, include_deleted: bool = False, auto_expunge: bool = True
    ) -> Sequence[ModelT]:
        """
        获取所有符合条件的记录。
        具体服务类可以基于此构建更复杂的列表查询方法。
        """
        self.logger.debug(f"服务层: 正在列出所有 {self.repository.model_type.__name__} 记录...")
        return await self.repository.get_all_records(
            *filters, include_deleted=include_deleted, auto_expunge=auto_expunge
        )

    async def count_all_records_svc(self, *filters: Any, include_deleted: bool = False) -> int:
        """
        计算符合条件的记录数量。
        """
        self.logger.debug(f"服务层: 正在计算 {self.repository.model_type.__name__} 记录数量...")
        return await self.repository.count_records(*filters, include_deleted=include_deleted)

    # 你可以在这里添加更多通用的服务层方法，例如：
    # - 处理通用的分页逻辑并返回 PagedResponse schema
    # - 通用的唯一性检查辅助方法等
    # 但保持基类相对轻量也是一个好策略。

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: session.py
@DateTime: 2025/06/02 02:11:23
@Docs: 数据库会话工厂
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.config import AsyncSessionConfig, SQLAlchemyAsyncConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_sqlalchemy_config() -> SQLAlchemyAsyncConfig:
    """创建 SQLAlchemy 配置

    Returns:
        SQLAlchemyAsyncConfig: SQLAlchemy 异步配置对象

    Raises:
        Exception: 创建配置失败时抛出
    """
    try:
        # 创建异步引擎
        engine = create_async_engine(
            str(settings.database_url),
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            # 连接池预ping，确保连接有效性
            pool_pre_ping=True,
        )

        # 创建会话配置
        session_config = AsyncSessionConfig(
            expire_on_commit=False,  # 提交后不过期对象
            autoflush=True,  # 自动刷新
        )  # 创建 SQLAlchemy 配置
        config = SQLAlchemyAsyncConfig(
            engine_instance=engine,
            session_config=session_config,
            create_all=settings.is_development,  # 开发环境自动创建表
        )

        logger.info(
            "数据库配置创建成功",
            extra={
                "database_url": str(settings.database_url).split("@")[0] + "@***",  # 隐藏敏感信息
                "pool_size": settings.database_pool_size,
                "create_all": settings.is_development,
            },
        )

        return config

    except Exception as e:
        logger.error(f"创建数据库配置失败: {e}", exc_info=True)
        raise


@lru_cache
def get_sqlalchemy_config() -> SQLAlchemyAsyncConfig:
    """获取 SQLAlchemy 配置的单例实例

    Returns:
        SQLAlchemyAsyncConfig: 单例 SQLAlchemy 配置
    """
    return create_sqlalchemy_config()


# 全局实例
sqlalchemy_config = get_sqlalchemy_config()


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """获取异步数据库会话的依赖注入函数

    用于 FastAPI 的 Depends() 依赖注入

    Yields:
        AsyncSession: 异步数据库会话

    Raises:
        Exception: 会话错误时抛出
    """
    async with sqlalchemy_config.get_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器

    提供数据库表的创建、删除、连接检查等管理功能
    """

    def __init__(self, config: SQLAlchemyAsyncConfig):
        """初始化数据库管理器

        Args:
            config: SQLAlchemy 配置对象
        """
        self.config = config
        self._engine = config.get_engine()

    async def create_all_tables(self) -> None:
        """创建所有表

        Raises:
            Exception: 创建表失败时抛出
        """
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(UUIDAuditBase.metadata.create_all)
            logger.info("所有数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
            raise

    async def drop_all_tables(self) -> None:
        """删除所有表 (仅用于测试环境)

        Raises:
            ValueError: 生产环境禁止删除所有表
            Exception: 删除表失败时抛出
        """
        if settings.is_production:
            raise ValueError("生产环境禁止删除所有表")

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(UUIDAuditBase.metadata.drop_all)
            logger.warning("所有数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}", exc_info=True)
            raise

    async def check_connection(self) -> bool:
        """检查数据库连接

        Returns:
            bool: 连接成功返回True，否则False
        """
        try:
            async with self.config.get_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("数据库连接检查成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}", exc_info=True)
            return False

    async def close(self) -> None:
        """关闭数据库连接

        Raises:
            Exception: 关闭失败时抛出
        """
        try:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}", exc_info=True)


# 全局数据库管理器实例
database_manager = DatabaseManager(sqlalchemy_config)

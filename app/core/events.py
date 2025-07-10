"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: events.py
@DateTime: 2025/03/08 04:35:00
@Docs: 应用程序事件管理
"""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from tortoise import Tortoise

from app.core.config import settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期上下文管理器

    Args:
        app (FastAPI): FastAPI应用实例
    """
    # 启动事件
    await startup(app)

    # 生命周期运行
    yield

    # 关闭事件
    await shutdown(app)


async def startup(app: FastAPI) -> None:
    """应用程序启动事件

    Args:
        app (FastAPI): FastAPI应用实例
    """
    logger.info(f"应用程序 {settings.APP_NAME} 正在启动...")

    # 初始化数据库连接
    await init_db()

    # 初始化Redis连接
    await init_redis(app)

    logger.info(f"应用程序 {settings.APP_NAME} 启动完成")


async def shutdown(app: FastAPI) -> None:
    """应用程序关闭事件

    Args:
        app (FastAPI): FastAPI应用实例
    """
    logger.info(f"应用程序 {settings.APP_NAME} 正在关闭...")

    # 关闭数据库连接
    await close_db()

    # 关闭Redis连接
    await close_redis(app)

    logger.info(f"应用程序 {settings.APP_NAME} 已关闭")


async def init_db() -> None:
    """初始化数据库连接"""
    try:
        logger.info("正在初始化数据库连接...")
        await Tortoise.init(config=settings.TORTOISE_ORM_CONFIG)
        logger.info("数据库连接初始化完成")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise


async def close_db() -> None:
    """关闭数据库连接"""
    try:
        logger.info("正在关闭数据库连接...")
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


# Redis 连接管理
async def init_redis(app: FastAPI) -> None:
    """初始化Redis连接"""
    logger.info("正在初始化Redis连接...")
    try:
        # 从 settings.REDIS_URI 创建连接池
        # 注意: redis-py 的 from_url 不直接返回连接池，而是返回一个 Redis 实例，该实例内部管理连接。
        # 对于简单的场景，直接使用这个实例即可。如果需要精细控制连接池，可以使用 redis.asyncio.ConnectionPool
        app.state.redis = redis.from_url(
            settings.REDIS_URI,
            encoding="utf-8",
            decode_responses=True,  # 通常希望自动解码响应
        )
        # 测试连接 (可选, 但推荐)
        await app.state.redis.ping()
        logger.info("Redis连接初始化完成并通过ping测试")
    except Exception as e:
        logger.error(f"Redis连接初始化失败: {e}")
        app.state.redis = None  # 明确设置redis状态为None


async def close_redis(app: FastAPI) -> None:
    """关闭Redis连接"""
    logger.info("正在关闭Redis连接...")
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.close()  # 关闭连接
            # 对于由 from_url 创建的实例，其内部可能会管理一个连接池，
            # close() 方法通常会释放相关资源。
            # 如果直接使用 ConnectionPool，则调用 pool.disconnect()
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接时出错: {e}")
    else:
        logger.info("没有活动的Redis连接需要关闭")

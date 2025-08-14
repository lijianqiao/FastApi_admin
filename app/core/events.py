"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: events.py
@DateTime: 2025/03/08 04:35:00
@Docs: 应用程序事件管理
"""

from contextlib import asynccontextmanager
import asyncio
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI

from app.core.config import settings
from app.db.connection import close_database, init_database
from app.utils.logger import logger
from app.utils.metrics import metrics_collector
from app.utils.permission_cache_utils import clear_all_permission_cache


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

    # 初始化权限缓存
    await init_permission_cache()

    # 启动日志归档后台任务
    await start_log_archive_task(app)

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
    await clear_all_permission_cache()  # 清除权限缓存
    await close_redis(app)

    # 停止日志归档后台任务
    await stop_log_archive_task(app)

    logger.info(f"应用程序 {settings.APP_NAME} 已关闭")


async def init_db() -> None:
    """初始化数据库连接（委托到 app.db.connection）。"""
    await init_database()


async def close_db() -> None:
    """关闭数据库连接（委托到 app.db.connection）。"""
    await close_database()


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
        # 测试连接
        await app.state.redis.ping()
        logger.info("Redis连接初始化完成并通过ping测试")
        metrics_collector.set_redis_up(True)
    except Exception as e:
        logger.error(f"Redis连接初始化失败: {e}")
        app.state.redis = None  # 明确设置redis状态为None
        metrics_collector.set_redis_up(False)


async def close_redis(app: FastAPI) -> None:
    """关闭Redis连接"""
    logger.info("正在关闭Redis连接...")
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.close()  # 关闭连接
            logger.info("Redis连接已关闭")
            metrics_collector.set_redis_up(False)
        except Exception as e:
            logger.error(f"关闭Redis连接时出错: {e}")
    else:
        logger.info("没有活动的Redis连接需要关闭")


async def init_permission_cache() -> None:
    """初始化权限缓存系统"""
    try:
        logger.info("正在初始化权限缓存系统...")
        from app.utils.redis_cache import get_redis_cache

        # 测试Redis缓存是否可用
        cache = await get_redis_cache()
        test_key = "permission:cache:test"
        test_value = {"test": "permissions"}

        # 测试缓存操作
        await cache.set(test_key, test_value, 60)  # 设置60秒TTL
        cached_value = await cache.get(test_key)

        if cached_value and cached_value.get("test") == "permissions":
            logger.info("权限缓存系统初始化成功，Redis缓存工作正常")
            # 清除测试数据
            await cache.delete(test_key)
        else:
            logger.warning("权限缓存系统测试失败，将使用内存缓存作为备用方案")

        # 获取缓存统计
        from app.utils.permission_cache_utils import get_permission_cache_stats

        stats = await get_permission_cache_stats()
        logger.info(f"权限缓存统计: {stats}")

    except Exception as e:
        logger.error(f"权限缓存系统初始化失败: {e}")
        logger.info("将使用内存缓存作为备用方案")


# ========== 日志归档后台任务 ==========
async def _log_archive_worker(app: FastAPI) -> None:
    """后台协程：定时压缩与归档操作日志。"""
    from app.utils.log_compression import compress_old_logs

    interval_seconds = max(1, settings.LOG_ARCHIVE_INTERVAL_HOURS) * 3600
    keep_days = max(1, settings.LOG_ARCHIVE_KEEP_DAYS)

    while True:
        try:
            if settings.LOG_ARCHIVE_ENABLED:
                result: dict[str, Any] = await compress_old_logs(keep_days)
                # 仅在有数据时打印关键信息，避免噪声
                if isinstance(result, dict) and result.get("operation_logs", {}).get("compressed", 0) > 0:
                    logger.info(
                        f"日志归档完成: 压缩 {result['operation_logs']['compressed']} 条, "
                        f"删除 {result['operation_logs']['deleted']} 条, 节省 {result['operation_logs']['size_saved']} bytes"
                    )
        except Exception as e:  # noqa: BLE001
            logger.error(f"日志归档任务执行失败: {e}")

        # 等待下一次执行
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


async def start_log_archive_task(app: FastAPI) -> None:
    """启动日志归档任务。"""
    if not settings.LOG_ARCHIVE_ENABLED:
        logger.info("日志归档任务未启用")
        return
    app.state.log_archive_task = asyncio.create_task(_log_archive_worker(app))
    logger.info(
        f"日志归档任务已启动：每 {settings.LOG_ARCHIVE_INTERVAL_HOURS} 小时执行一次，保留 {settings.LOG_ARCHIVE_KEEP_DAYS} 天"
    )


async def stop_log_archive_task(app: FastAPI) -> None:
    """停止日志归档任务。"""
    task = getattr(app.state, "log_archive_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("日志归档任务已停止")

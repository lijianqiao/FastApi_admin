"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: rate_limit.py
@DateTime: 2025/07/15
@Docs: 基于 Redis 的分布式限流（内存回退），提供路由依赖与通用检查函数
"""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.utils.logger import logger
from app.utils.metrics import metrics_collector

try:
    import redis.asyncio as redis
except Exception:  # noqa: BLE001 - 依赖可选
    redis = None  # type: ignore[assignment]


async def _get_redis_client():
    """获取底层 redis-py 客户端；失败返回 None。"""
    try:
        if not redis:
            return None
        # 复用 redis_cache 的客户端以共享连接
        from app.utils.redis_cache import get_redis_cache

        cache = await get_redis_cache()
        client = await cache._get_client()  # type: ignore[attr-defined]
        return client
    except Exception:
        return None


class _MemoryCounter:
    """简单内存计数器（仅在 Redis 不可用时回退使用）。"""

    def __init__(self) -> None:
        self._store: dict[str, tuple[int, float]] = {}

    def incr_with_expire(self, key: str, window_seconds: int) -> int:
        now = time.time()
        value, expires_at = self._store.get(key, (0, 0))
        if now > expires_at:
            value = 0
            expires_at = now + window_seconds
        value += 1
        self._store[key] = (value, expires_at)
        return value


_memory_counter = _MemoryCounter()


async def _incr_with_expire(key: str, window_seconds: int) -> int:
    """在窗口内递增计数并返回当前值；优先使用 Redis，失败回退内存。"""
    client = await _get_redis_client()
    if client is None:
        metrics_collector.set_redis_up(False)
        return _memory_counter.incr_with_expire(key, window_seconds)

    # Lua 原子脚本：存在则 INCR，不存在则 SET 1 EX window
    script = (
        "local exists = redis.call('EXISTS', KEYS[1]) "
        "if exists == 1 then return redis.call('INCR', KEYS[1]) "
        "else redis.call('SET', KEYS[1], 1, 'EX', ARGV[1]); return 1 end"
    )

    async def _eval(client_obj, script_str: str, keys_list: list[str], args_list: list[int]) -> int:
        """兼容不同 redis-py 版本的 EVAL 调用，并处理同步/异步返回。"""
        try:
            result = client_obj.eval(script_str, keys=keys_list, args=args_list)
        except TypeError:
            # 兼容旧签名: eval(script, numkeys, *keys_and_args)
            result = client_obj.eval(script_str, len(keys_list), *(keys_list + args_list))
        if inspect.isawaitable(result):
            result = await result
        return int(result)

    try:
        current: int = await _eval(client, script, [key], [window_seconds])
        metrics_collector.set_redis_up(True)
        return int(current)
    except Exception as e:  # noqa: BLE001 - 记录并回退
        logger.error(f"RateLimit Redis eval 失败: {e}")
        metrics_collector.set_redis_up(False)
        return _memory_counter.incr_with_expire(key, window_seconds)


def _default_key_builder(scope: str) -> Callable[[Request], str]:
    def builder(request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"rl:{scope}:{client_ip}"

    return builder


async def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """通用：检查并更新计数；未超限返回 True。"""
    current = await _incr_with_expire(key, window_seconds)
    return current <= limit


def rate_limit(scope: str, times: int, seconds: int, key_builder: Callable[[Request], str] | None = None):
    """路由依赖：按 scope+客户端构建键在 Redis 窗口计数。"""

    if key_builder is None:
        key_builder = _default_key_builder(scope)

    async def dependency(request: Request) -> None:
        key = key_builder(request)
        allowed = await check_rate_limit(key, times, seconds)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="请求过于频繁，请稍后再试")

    return dependency


def rate_limit_per_ip_per_minute() -> Callable[[Request], Awaitable[None]]:
    """用于全局中间件的每 IP 每分钟限流依赖。"""

    return rate_limit("global:minute", settings.RATE_LIMIT_PER_MINUTE, 60)

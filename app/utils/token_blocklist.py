"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: token_blocklist.py
@DateTime: 2025/07/12
@Docs: JWT jti 黑名单（Redis存储，失效由TTL控制）
"""

from __future__ import annotations

from typing import Final

from app.core.config import settings
from app.utils.logger import logger
from app.utils.redis_cache import _memory_fallback, get_redis_cache

BLOCK_VALUE: Final[bytes] = b"1"


def _block_key(jti: str) -> str:
    return f"{settings.JWT_BLOCKLIST_PREFIX}{jti}"


def is_jti_blocked_sync(jti: str) -> bool:
    """同步兜底检查（仅用于无法使用异步时）。始终返回False。"""
    return False


async def block_jti_async(jti: str, ttl_seconds: int) -> bool:
    """将jti加入黑名单，TTL由令牌剩余有效期决定。"""
    key = _block_key(jti)
    try:
        redis_cache = await get_redis_cache()
        ok = await redis_cache.set_plain(key, BLOCK_VALUE, ttl_seconds)
        if not ok:
            await _memory_fallback.set(key, True, ttl_seconds)
        return True
    except Exception as e:
        logger.error(f"block_jti 失败: {e}")
        return False


async def is_jti_blocked_async(jti: str) -> bool:
    key = _block_key(jti)
    try:
        redis_cache = await get_redis_cache()
        # 先查Redis
        exists = await redis_cache.exists(key)
        if exists:
            return True
        # 再查内存兜底
        val = await _memory_fallback.get(key)
        return bool(val)
    except Exception:
        return False


def is_jti_blocked(jti: str) -> bool:
    """尽可能为安全路径提供同步判断（verify中使用）。

    注意：当仅有异步Redis时，此函数只能返回False（避免阻塞）。
    在关键路径会结合服务层明确异步撤销写入。
    """
    try:
        # 仅做内存兜底快速判定（不阻塞）
        key = _block_key(jti)
        cached = _memory_fallback._cache.get(key)  # type: ignore[attr-defined]
        return bool(cached)
    except Exception:
        return False

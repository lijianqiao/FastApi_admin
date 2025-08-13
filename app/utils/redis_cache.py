"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: redis_cache.py
@DateTime: 2025/07/11
@Docs: Redis缓存管理器
"""

import pickle
from typing import Any

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from app.core.config import settings
from app.utils.logger import logger


class RedisCache:
    """Redis缓存管理器"""

    def __init__(self):
        self._redis_client = None
        self._is_connected = False

    async def _get_client(self):
        """获取Redis客户端连接"""
        if not redis:
            logger.warning("Redis未安装，使用内存缓存作为备用方案")
            return None

        if not self._redis_client or not self._is_connected:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URI,
                    decode_responses=False,  # 使用bytes以支持pickle
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                )
                # 测试连接
                await self._redis_client.ping()
                self._is_connected = True
                logger.info("Redis连接成功")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self._redis_client = None
                self._is_connected = False

        return self._redis_client

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否设置成功
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            # 序列化数据
            if isinstance(value, dict | list | set):
                # 对于集合类型，转换为列表后序列化
                if isinstance(value, set):
                    value = list(value)
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = pickle.dumps(value)

            # 设置缓存
            result = await client.setex(key, ttl, serialized_value)
            logger.debug(f"Redis缓存设置: {key}, TTL: {ttl}秒")
            return bool(result)

        except Exception as e:
            logger.error(f"Redis设置缓存失败: {key}, 错误: {e}")
            return False

    async def set_plain(self, key: str, value: bytes | str, ttl: int) -> bool:
        """设置原始值（不pickle），用于布尔标记或字符串。

        Args:
            key: 键
            value: 值（bytes或str）
            ttl: 过期秒数

        Returns:
            是否成功
        """
        try:
            client = await self._get_client()
            if not client:
                return False
            if isinstance(value, str):
                value_bytes = value.encode()
            else:
                value_bytes = value
            result = await client.setex(key, ttl, value_bytes)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set_plain 失败: {key}, 错误: {e}")
            return False

    async def get(self, key: str) -> Any | None:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        try:
            client = await self._get_client()
            if not client:
                return None

            # 获取缓存
            cached_data = await client.get(key)
            if cached_data is None:
                return None

            # 反序列化数据
            value = pickle.loads(cached_data)

            # 如果原来是集合类型，转换回集合
            if isinstance(value, list) and key.endswith(":permissions"):
                value = set(value)

            logger.debug(f"Redis缓存命中: {key}")
            return value

        except Exception as e:
            logger.error(f"Redis获取缓存失败: {key}, 错误: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            result = await client.delete(key)
            logger.debug(f"Redis缓存删除: {key}")
            return bool(result)

        except Exception as e:
            logger.error(f"Redis删除缓存失败: {key}, 错误: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存

        Args:
            pattern: 匹配模式，如 "user:permissions:*"

        Returns:
            删除的键数量
        """
        try:
            client = await self._get_client()
            if not client:
                return 0

            # 查找匹配的键
            keys = await client.keys(pattern)
            if not keys:
                return 0

            # 批量删除
            result = await client.delete(*keys)
            logger.debug(f"Redis批量删除缓存: {pattern}, 删除数量: {result}")
            return result

        except Exception as e:
            logger.error(f"Redis批量删除缓存失败: {pattern}, 错误: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            result = await client.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Redis检查缓存存在性失败: {key}, 错误: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取缓存剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        try:
            client = await self._get_client()
            if not client:
                return -2

            result = await client.ttl(key)
            return result

        except Exception as e:
            logger.error(f"Redis获取TTL失败: {key}, 错误: {e}")
            return -2

    async def clear_all(self) -> bool:
        """清除所有缓存（谨慎使用）

        Returns:
            是否清除成功
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            # 只清除权限相关的缓存
            patterns = ["user:permissions:*", "role:permissions:*", "permission:cache:*"]

            total_deleted = 0
            for pattern in patterns:
                deleted = await self.delete_pattern(pattern)
                total_deleted += deleted

            logger.info(f"Redis权限缓存清除完成, 删除数量: {total_deleted}")
            return True

        except Exception as e:
            logger.error(f"Redis清除所有缓存失败: {e}")
            return False

    async def close(self):
        """关闭Redis连接"""
        if self._redis_client:
            await self._redis_client.close()
            self._is_connected = False
            logger.info("Redis连接已关闭")


# 全局Redis缓存实例
_redis_cache = RedisCache()


async def get_redis_cache() -> RedisCache:
    """获取Redis缓存实例"""
    return _redis_cache


class MemoryFallback:
    """内存缓存备用方案（当Redis不可用时）"""

    def __init__(self):
        self._cache = {}

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置内存缓存"""
        import time

        self._cache[key] = {"value": value, "expires_at": time.time() + ttl}
        return True

    async def get(self, key: str) -> Any | None:
        """获取内存缓存"""
        import time

        if key not in self._cache:
            return None

        cache_item = self._cache[key]
        if time.time() > cache_item["expires_at"]:
            del self._cache[key]
            return None

        return cache_item["value"]

    async def delete(self, key: str) -> bool:
        """删除内存缓存"""
        self._cache.pop(key, None)
        return True

    async def clear_all(self) -> bool:
        """清除所有内存缓存"""
        self._cache.clear()
        return True


# 内存备用缓存实例
_memory_fallback = MemoryFallback()

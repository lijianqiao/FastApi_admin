"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cache_service_new.py
@DateTime: 2025/06/06 22:04:22
@Docs: 缓存服务 - 处理权限和角色缓存
"""

import json
from typing import Any

import redis.asyncio as redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """缓存服务类"""

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.prefix = settings.cache_key_prefix
        self.expire_time = settings.cache_expire_minutes * 60  # 转换为秒

    async def init_redis(self):
        """初始化Redis连接"""
        if settings.redis_url:
            try:
                self.redis_client = redis.from_url(str(settings.redis_url))
                await self.redis_client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败: {e}, 缓存功能将被禁用")
                self.redis_client = None
        else:
            logger.info("未配置Redis URL，缓存功能被禁用")

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        """获取缓存"""
        if not self.redis_client:
            return None

        try:
            cached_key = self._get_key(key)
            data = await self.redis_client.get(cached_key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"缓存读取失败 {key}: {e}")
        return None

    async def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """设置缓存"""
        if not self.redis_client:
            return False

        try:
            cached_key = self._get_key(key)
            expire_time = expire or self.expire_time
            await self.redis_client.setex(cached_key, expire_time, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"缓存写入失败 {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False

        try:
            cached_key = self._get_key(key)
            await self.redis_client.delete(cached_key)
            return True
        except Exception as e:
            logger.warning(f"缓存删除失败 {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存"""
        if not self.redis_client:
            return 0

        try:
            cached_pattern = self._get_key(pattern)
            keys = await self.redis_client.keys(cached_pattern)
            if keys:
                return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"批量缓存删除失败 {pattern}: {e}")
        return 0

    # === 用户权限缓存方法 ===
    async def get_user_permissions(self, user_id: str) -> list[str] | None:
        """获取用户权限缓存"""
        return await self.get(f"user_permissions:{user_id}")

    async def set_user_permissions(self, user_id: str, permissions: list[str]) -> bool:
        """设置用户权限缓存"""
        return await self.set(f"user_permissions:{user_id}", permissions)

    async def delete_user_permissions(self, user_id: str) -> bool:
        """删除用户权限缓存"""
        return await self.delete(f"user_permissions:{user_id}")

    # === 用户角色缓存方法 ===
    async def get_user_roles(self, user_id: str) -> list[dict] | None:
        """获取用户角色缓存"""
        return await self.get(f"user_roles:{user_id}")

    async def set_user_roles(self, user_id: str, roles: list[dict]) -> bool:
        """设置用户角色缓存"""
        return await self.set(f"user_roles:{user_id}", roles)

    async def delete_user_roles(self, user_id: str) -> bool:
        """删除用户角色缓存"""
        return await self.delete(f"user_roles:{user_id}")

    # === 角色权限缓存方法 ===
    async def get_role_permissions(self, role_id: str) -> list[str] | None:
        """获取角色权限缓存"""
        return await self.get(f"role_permissions:{role_id}")

    async def set_role_permissions(self, role_id: str, permissions: list[str]) -> bool:
        """设置角色权限缓存"""
        return await self.set(f"role_permissions:{role_id}", permissions)

    async def delete_role_permissions(self, role_id: str) -> bool:
        """删除角色权限缓存"""
        return await self.delete(f"role_permissions:{role_id}")

    # === Token黑名单方法 ===
    async def add_token_to_blacklist(self, jti: str, expire_time: int) -> bool:
        """将token JTI添加到黑名单"""
        try:
            blacklist_key = f"blacklist:{jti}"
            return await self.set(blacklist_key, "1", expire=expire_time)
        except Exception as e:
            logger.warning(f"添加token到黑名单失败 {jti}: {e}")
            return False

    async def is_token_blacklisted(self, jti: str) -> bool:
        """检查token是否在黑名单中"""
        try:
            blacklist_key = f"blacklist:{jti}"
            result = await self.get(blacklist_key)
            return result is not None
        except Exception as e:
            logger.warning(f"检查token黑名单失败 {jti}: {e}")
            return False

    async def clear_user_tokens(self, user_id: str) -> int:
        """清理用户的所有token（用于全设备登出）"""
        count = 0
        try:
            # 清理用户相关的token记录
            count += await self.delete_pattern(f"user_tokens:{user_id}")
            count += await self.delete_pattern(f"refresh_tokens:{user_id}:*")
        except Exception as e:
            logger.warning(f"清理用户token失败 {user_id}: {e}")
        return count

    # === 批量清理方法 ===
    async def clear_user_cache(self, user_id: str) -> int:
        """清理用户相关的所有缓存"""
        count = 0
        count += await self.delete_pattern(f"user_permissions:{user_id}")
        count += await self.delete_pattern(f"user_roles:{user_id}")
        return count

    async def clear_role_cache(self, role_id: str) -> int:
        """清理角色相关的所有缓存"""
        count = 0
        count += await self.delete_pattern(f"role_permissions:{role_id}")
        # 清理所有用户的权限缓存（因为角色权限变了）
        count += await self.delete_pattern("user_permissions:*")
        return count


# 全局缓存服务实例
cache_service = CacheService()

"""缓存服务层 - 提供动态TTL管理和缓存优化.

@Author: li
@Email: lijianqiao2906@live.com
@FileName: cache_service.py
@DateTime: 2025/07/08
@Docs: 缓存服务层，提供动态TTL管理和缓存策略优化
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.utils.logger import logger
from app.utils.redis_cache import get_redis_cache


class CacheScenario(str, Enum):
    """缓存场景枚举."""

    # 权限相关缓存
    USER_PERMISSIONS = "user_permissions"  # 用户权限缓存
    ROLE_PERMISSIONS = "role_permissions"  # 角色权限缓存
    MENU_PERMISSIONS = "menu_permissions"  # 菜单权限缓存

    # 用户相关缓存
    USER_PROFILE = "user_profile"  # 用户资料缓存
    USER_SETTINGS = "user_settings"  # 用户设置缓存

    # 系统相关缓存
    SYSTEM_CONFIG = "system_config"  # 系统配置缓存
    API_RATE_LIMIT = "api_rate_limit"  # API限流缓存

    # 业务相关缓存
    DASHBOARD_DATA = "dashboard_data"  # 仪表板数据缓存
    REPORT_DATA = "report_data"  # 报表数据缓存


class DynamicCacheManager:
    """动态缓存管理器 - 根据业务场景调整TTL."""

    def __init__(self):
        self.base_ttl = settings.PERMISSION_CACHE_TTL
        self.scenario_ttl_map = self._init_scenario_ttl_map()
        self.peak_hours = [(9, 12), (14, 18)]  # 业务高峰时段

    def _init_scenario_ttl_map(self) -> dict[CacheScenario, dict[str, int]]:
        """初始化场景TTL映射表.

        Returns:
            dict[CacheScenario, dict[str, int]]: 场景TTL配置
        """
        return {
            # 权限相关 - 根据权限变更频率调整
            CacheScenario.USER_PERMISSIONS: {
                "normal": 3600,  # 正常时段1小时
                "peak": 1800,  # 高峰时段30分钟
                "admin_active": 600,  # 管理员活跃时10分钟
                "role_changed": 300,  # 角色变更后5分钟
            },
            CacheScenario.ROLE_PERMISSIONS: {
                "normal": 7200,  # 正常时段2小时
                "peak": 3600,  # 高峰时段1小时
                "admin_active": 1800,  # 管理员活跃时30分钟
            },
            CacheScenario.MENU_PERMISSIONS: {
                "normal": 3600,  # 正常时段1小时
                "peak": 1800,  # 高峰时段30分钟
                "user_login": 900,  # 用户登录后15分钟
            },
            # 用户相关 - 根据用户活跃度调整
            CacheScenario.USER_PROFILE: {
                "normal": 1800,  # 正常时段30分钟
                "active_user": 900,  # 活跃用户15分钟
                "profile_updated": 300,  # 资料更新后5分钟
            },
            CacheScenario.USER_SETTINGS: {
                "normal": 3600,  # 正常时段1小时
                "settings_changed": 600,  # 设置变更后10分钟
            },
            # 系统相关 - 根据系统负载调整
            CacheScenario.SYSTEM_CONFIG: {
                "normal": 7200,  # 正常时段2小时
                "config_updated": 300,  # 配置更新后5分钟
            },
            CacheScenario.API_RATE_LIMIT: {
                "normal": 60,  # 正常时段1分钟
                "high_load": 30,  # 高负载时30秒
            },
            # 业务相关 - 根据数据更新频率调整
            CacheScenario.DASHBOARD_DATA: {
                "normal": 600,  # 正常时段10分钟
                "peak": 300,  # 高峰时段5分钟
                "real_time": 60,  # 实时数据1分钟
            },
            CacheScenario.REPORT_DATA: {
                "normal": 1800,  # 正常时段30分钟
                "data_updated": 300,  # 数据更新后5分钟
            },
        }

    def get_dynamic_ttl(self, scenario: CacheScenario, context: dict[str, Any] | None = None) -> int:
        """根据业务场景和上下文获取动态TTL.

        Args:
            scenario: 缓存场景
            context: 上下文信息

        Returns:
            int: 动态计算的TTL（秒）
        """
        if context is None:
            context = {}

        scenario_config = self.scenario_ttl_map.get(scenario, {})

        # 检查特殊上下文
        if context.get("admin_active"):
            return scenario_config.get("admin_active", scenario_config.get("normal", self.base_ttl))

        if context.get("role_changed"):
            return scenario_config.get("role_changed", scenario_config.get("normal", self.base_ttl))

        if context.get("profile_updated"):
            return scenario_config.get("profile_updated", scenario_config.get("normal", self.base_ttl))

        if context.get("config_updated"):
            return scenario_config.get("config_updated", scenario_config.get("normal", self.base_ttl))

        if context.get("data_updated"):
            return scenario_config.get("data_updated", scenario_config.get("normal", self.base_ttl))

        if context.get("real_time"):
            return scenario_config.get("real_time", scenario_config.get("normal", self.base_ttl))

        if context.get("high_load"):
            return scenario_config.get("high_load", scenario_config.get("normal", self.base_ttl))

        # 检查是否为高峰时段
        if self._is_peak_hour():
            return scenario_config.get("peak", scenario_config.get("normal", self.base_ttl))

        # 默认返回正常时段TTL
        return scenario_config.get("normal", self.base_ttl)

    def _is_peak_hour(self) -> bool:
        """检查当前是否为业务高峰时段.

        Returns:
            bool: 是否为高峰时段
        """
        current_hour = datetime.now().hour
        for start_hour, end_hour in self.peak_hours:
            if start_hour <= current_hour < end_hour:
                return True
        return False

    async def set_cache_with_dynamic_ttl(
        self, key: str, value: Any, scenario: CacheScenario, context: dict[str, Any] | None = None
    ) -> bool:
        """使用动态TTL设置缓存.

        Args:
            key: 缓存键
            value: 缓存值
            scenario: 缓存场景
            context: 上下文信息

        Returns:
            bool: 设置是否成功
        """
        ttl = self.get_dynamic_ttl(scenario, context)

        try:
            cache = await get_redis_cache()
            success = await cache.set(key, value, ttl)

            if success:
                logger.info(f"动态缓存设置成功: key={key}, scenario={scenario.value}, ttl={ttl}秒, context={context}")
            else:
                logger.warning(f"动态缓存设置失败: key={key}, scenario={scenario.value}")

            return success

        except Exception as e:
            logger.error(f"动态缓存设置异常: key={key}, scenario={scenario.value}, error={e}")
            return False

    async def update_permission_cache_ttl(self, user_id: UUID, context: dict[str, Any] | None = None) -> bool:
        """更新用户权限缓存的TTL.

        Args:
            user_id: 用户ID
            context: 上下文信息

        Returns:
            bool: 更新是否成功
        """
        cache_key = f"user:permissions:{user_id}"

        try:
            cache = await get_redis_cache()

            # 检查缓存是否存在
            cached_value = await cache.get(cache_key)
            if cached_value is None:
                logger.info(f"权限缓存不存在，无需更新TTL: user_id={user_id}")
                return True

            # 计算新的TTL
            new_ttl = self.get_dynamic_ttl(CacheScenario.USER_PERMISSIONS, context)

            # 重新设置缓存以更新TTL
            success = await cache.set(cache_key, cached_value, new_ttl)

            if success:
                logger.info(f"权限缓存TTL更新成功: user_id={user_id}, new_ttl={new_ttl}秒, context={context}")
            else:
                logger.warning(f"权限缓存TTL更新失败: user_id={user_id}")

            return success

        except Exception as e:
            logger.error(f"权限缓存TTL更新异常: user_id={user_id}, error={e}")
            return False

    async def batch_update_cache_ttl(
        self, cache_keys: list[str], scenario: CacheScenario, context: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """批量更新缓存TTL.

        Args:
            cache_keys: 缓存键列表
            scenario: 缓存场景
            context: 上下文信息

        Returns:
            dict[str, bool]: 每个键的更新结果
        """
        results = {}
        new_ttl = self.get_dynamic_ttl(scenario, context)

        try:
            cache = await get_redis_cache()

            # 并发处理所有缓存键
            async def update_single_cache(key: str) -> tuple[str, bool]:
                try:
                    cached_value = await cache.get(key)
                    if cached_value is None:
                        return key, True  # 缓存不存在，视为成功

                    success = await cache.set(key, cached_value, new_ttl)
                    return key, success

                except Exception as e:
                    logger.error(f"更新缓存TTL失败: key={key}, error={e}")
                    return key, False

            # 并发执行更新任务
            tasks = [update_single_cache(key) for key in cache_keys]
            update_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for result in update_results:
                if isinstance(result, tuple):
                    key, success = result
                    results[key] = success
                else:
                    # 处理异常情况
                    logger.error(f"批量更新缓存TTL异常: {result}")

            success_count = sum(1 for success in results.values() if success)
            logger.info(
                f"批量更新缓存TTL完成: scenario={scenario.value}, new_ttl={new_ttl}秒, "
                f"成功={success_count}/{len(cache_keys)}, context={context}"
            )

        except Exception as e:
            logger.error(f"批量更新缓存TTL异常: scenario={scenario.value}, error={e}")
            # 如果出现异常，将所有键标记为失败
            results = dict.fromkeys(cache_keys, False)

        return results

    async def get_cache_performance_stats(self) -> dict[str, Any]:
        """获取缓存性能统计信息.

        Returns:
            dict[str, Any]: 缓存性能统计
        """
        try:
            cache = await get_redis_cache()

            # 获取Redis信息
            client = await cache._get_client()  # type: ignore
            if not client:
                return {"error": "Redis客户端不可用"}

            info = await client.info()
            memory_info = await client.info("memory")
            stats_info = await client.info("stats")

            # 统计不同场景的缓存键数量
            scenario_stats = {}
            for scenario in CacheScenario:
                pattern = f"*{scenario.value}*"
                keys = await client.keys(pattern)
                scenario_stats[scenario.value] = len(keys)

            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": memory_info.get("used_memory_human"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human"),
                "total_commands_processed": stats_info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": stats_info.get("instantaneous_ops_per_sec"),
                "keyspace_hits": stats_info.get("keyspace_hits"),
                "keyspace_misses": stats_info.get("keyspace_misses"),
                "scenario_cache_counts": scenario_stats,
                "is_peak_hour": self._is_peak_hour(),
                "base_ttl": self.base_ttl,
            }

        except Exception as e:
            logger.error(f"获取缓存性能统计失败: {e}")
            return {"error": str(e)}


# 全局缓存管理器实例
cache_manager = DynamicCacheManager()

"""缓存管理API - 提供缓存性能监控和TTL调整功能.

@Author: li
@Email: lijianqiao2906@live.com
@FileName: cache_management.py
@DateTime: 2025/07/08
@Docs: 缓存管理API，提供缓存性能监控、TTL调整和缓存策略管理
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.permissions.simple_decorators import Permissions, require_permission
from app.schemas.base import BaseResponse
from app.services.cache_service import CacheScenario, cache_manager
from app.utils.deps import OperationContext
from app.utils.metrics import metrics_collector

# 可选模块：默认不挂载到主路由，需在应用入口显式 include_router 才生效
router = APIRouter(prefix="/cache", tags=["缓存管理（可选）"])


@router.get("/performance-stats", summary="获取缓存性能统计")
async def get_cache_performance_stats(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """获取缓存性能统计信息.

    Returns:
        BaseResponse[dict[str, Any]]: 缓存性能统计数据
    """
    stats = await cache_manager.get_cache_performance_stats()
    stats["dependencies"] = {"redis_up": int(metrics_collector._redis_up)}  # 简易附加状态
    return BaseResponse(data=stats, message="获取缓存性能统计成功")


@router.get("/health", summary="缓存健康检查")
async def cache_health(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """返回缓存健康状态（Redis 可用与否）。"""
    return BaseResponse(data={"redis_up": int(metrics_collector._redis_up)}, message="OK")


@router.get("/scenarios", summary="获取缓存场景配置")
async def get_cache_scenarios(
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """获取所有缓存场景的TTL配置.

    Returns:
        BaseResponse[dict[str, Any]]: 缓存场景配置
    """
    scenarios_config = {
        scenario.value: {
            "name": scenario.value,
            "ttl_config": cache_manager.scenario_ttl_map.get(scenario, {}),
            "current_ttl": cache_manager.get_dynamic_ttl(scenario),
        }
        for scenario in CacheScenario
    }

    return BaseResponse(
        data={
            "scenarios": scenarios_config,
            "base_ttl": cache_manager.base_ttl,
            "is_peak_hour": cache_manager._is_peak_hour(),
            "peak_hours": cache_manager.peak_hours,
        },
        message="获取缓存场景配置成功",
    )


@router.post("/update-permission-ttl/{user_id}", summary="更新用户权限缓存TTL")
async def update_user_permission_cache_ttl(
    user_id: UUID,
    context: dict[str, Any] | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """更新指定用户的权限缓存TTL.

    Args:
        user_id: 用户ID
        context: 上下文信息，用于动态TTL计算

    Returns:
        BaseResponse[dict[str, Any]]: 更新结果
    """
    if context is None:
        context = {}

    success = await cache_manager.update_permission_cache_ttl(user_id, context)
    new_ttl = cache_manager.get_dynamic_ttl(CacheScenario.USER_PERMISSIONS, context)

    return BaseResponse(
        data={
            "user_id": str(user_id),
            "success": success,
            "new_ttl": new_ttl,
            "context": context,
        },
        message="更新用户权限缓存TTL完成",
    )


@router.post("/batch-update-ttl", summary="批量更新缓存TTL")
async def batch_update_cache_ttl(
    cache_keys: list[str],
    scenario: CacheScenario,
    context: dict[str, Any] | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """批量更新缓存TTL.

    Args:
        cache_keys: 缓存键列表
        scenario: 缓存场景
        context: 上下文信息

    Returns:
        BaseResponse[dict[str, Any]]: 批量更新结果
    """
    if context is None:
        context = {}

    results = await cache_manager.batch_update_cache_ttl(cache_keys, scenario, context)
    new_ttl = cache_manager.get_dynamic_ttl(scenario, context)

    success_count = sum(1 for success in results.values() if success)

    return BaseResponse(
        data={
            "scenario": scenario.value,
            "new_ttl": new_ttl,
            "total_keys": len(cache_keys),
            "success_count": success_count,
            "failed_count": len(cache_keys) - success_count,
            "results": results,
            "context": context,
        },
        message="批量更新缓存TTL完成",
    )


@router.post("/set-dynamic-cache", summary="使用动态TTL设置缓存")
async def set_cache_with_dynamic_ttl(
    key: str,
    value: Any,
    scenario: CacheScenario,
    context: dict[str, Any] | None = None,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """使用动态TTL设置缓存.

    Args:
        key: 缓存键
        value: 缓存值
        scenario: 缓存场景
        context: 上下文信息

    Returns:
        BaseResponse[dict[str, Any]]: 设置结果
    """
    if context is None:
        context = {}

    success = await cache_manager.set_cache_with_dynamic_ttl(key, value, scenario, context)
    ttl = cache_manager.get_dynamic_ttl(scenario, context)

    return BaseResponse(
        data={
            "key": key,
            "scenario": scenario.value,
            "ttl": ttl,
            "success": success,
            "context": context,
        },
        message="动态缓存设置完成",
    )


@router.get("/ttl-preview", summary="预览动态TTL")
async def preview_dynamic_ttl(
    scenario: CacheScenario,
    admin_active: bool = False,
    role_changed: bool = False,
    profile_updated: bool = False,
    config_updated: bool = False,
    data_updated: bool = False,
    real_time: bool = False,
    high_load: bool = False,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """预览不同上下文下的动态TTL.

    Args:
        scenario: 缓存场景
        admin_active: 管理员活跃
        role_changed: 角色变更
        profile_updated: 资料更新
        config_updated: 配置更新
        data_updated: 数据更新
        real_time: 实时数据
        high_load: 高负载

    Returns:
        BaseResponse[dict[str, Any]]: TTL预览结果
    """
    # 构建上下文
    context = {
        "admin_active": admin_active,
        "role_changed": role_changed,
        "profile_updated": profile_updated,
        "config_updated": config_updated,
        "data_updated": data_updated,
        "real_time": real_time,
        "high_load": high_load,
    }

    # 过滤掉False值
    active_context = {k: v for k, v in context.items() if v}

    # 计算不同情况下的TTL
    normal_ttl = cache_manager.get_dynamic_ttl(scenario, {})
    context_ttl = cache_manager.get_dynamic_ttl(scenario, active_context)

    return BaseResponse(
        data={
            "scenario": scenario.value,
            "normal_ttl": normal_ttl,
            "context_ttl": context_ttl,
            "active_context": active_context,
            "is_peak_hour": cache_manager._is_peak_hour(),
            "scenario_config": cache_manager.scenario_ttl_map.get(scenario, {}),
        },
        message="TTL预览完成",
    )


@router.delete("/clear-scenario-cache/{scenario}", summary="清除指定场景的缓存")
async def clear_scenario_cache(
    scenario: CacheScenario,
    operation_context: OperationContext = Depends(require_permission(Permissions.SYSTEM_ADMIN)),
) -> BaseResponse[dict[str, Any]]:
    """清除指定场景的所有缓存.

    Args:
        scenario: 缓存场景

    Returns:
        BaseResponse[dict[str, Any]]: 清除结果
    """
    try:
        from app.utils.redis_cache import get_redis_cache

        cache = await get_redis_cache()
        client = await cache._get_client()  # type: ignore

        if not client:
            return BaseResponse(data={"error": "Redis客户端不可用"}, message="清除缓存失败")

        # 查找匹配的缓存键
        pattern = f"*{scenario.value}*"
        keys = await client.keys(pattern)

        if not keys:
            return BaseResponse(
                data={
                    "scenario": scenario.value,
                    "cleared_count": 0,
                    "pattern": pattern,
                },
                message="没有找到匹配的缓存键",
            )

        # 删除匹配的键
        deleted_count = await client.delete(*keys)

        return BaseResponse(
            data={
                "scenario": scenario.value,
                "cleared_count": deleted_count,
                "total_keys": len(keys),
                "pattern": pattern,
            },
            message=f"成功清除 {deleted_count} 个缓存键",
        )

    except Exception as e:
        return BaseResponse(data={"error": str(e)}, message="清除缓存时发生错误")

"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: metrics.py
@DateTime: 2025/07/05
@Docs: 应用程序监控指标
"""

import time
from collections import defaultdict
from typing import Any

from app.core.config import settings


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._request_count: dict[str, int] = defaultdict(int)
        self._request_duration: dict[str, list[float]] = defaultdict(list)
        self._error_count: dict[str, int] = defaultdict(int)
        self._active_connections: int = 0
        self._total_requests: int = 0
        self._total_errors: int = 0

    def record_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        """记录请求指标"""
        if not settings.ENABLE_PERFORMANCE_MONITORING:
            return

        endpoint = f"{method} {path}"
        self._request_count[endpoint] += 1
        self._request_duration[endpoint].append(duration)
        self._total_requests += 1

        if status_code >= 400:
            self._error_count[endpoint] += 1
            self._total_errors += 1

    def record_database_operation(self, operation: str, duration: float) -> None:
        """记录数据库操作指标"""
        if not settings.ENABLE_PERFORMANCE_MONITORING:
            return

        self._request_duration[f"db_{operation}"].append(duration)

    def increment_active_connections(self) -> None:
        """增加活跃连接数"""
        self._active_connections += 1

    def decrement_active_connections(self) -> None:
        """减少活跃连接数"""
        self._active_connections = max(0, self._active_connections - 1)

    def get_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        metrics = {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "active_connections": self._active_connections,
            "error_rate": self._total_errors / max(self._total_requests, 1),
            "endpoints": {},
        }

        # 计算每个端点的指标
        for endpoint, count in self._request_count.items():
            durations = self._request_duration.get(endpoint, [])
            errors = self._error_count.get(endpoint, 0)

            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)
            else:
                avg_duration = max_duration = min_duration = 0

            metrics["endpoints"][endpoint] = {
                "count": count,
                "errors": errors,
                "error_rate": errors / max(count, 1),
                "avg_duration": avg_duration,
                "max_duration": max_duration,
                "min_duration": min_duration,
            }

        return metrics

    def reset_metrics(self) -> None:
        """重置指标"""
        self._request_count.clear()
        self._request_duration.clear()
        self._error_count.clear()
        self._total_requests = 0
        self._total_errors = 0


# 全局指标收集器实例
metrics_collector = MetricsCollector()


def get_system_metrics() -> dict[str, Any]:
    """获取系统指标"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // 1024 // 1024,
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // 1024 // 1024 // 1024,
        }
    except ImportError:
        return {"error": "psutil not installed", "message": "请安装psutil以获取系统指标"}
    except Exception as e:
        return {"error": str(e)}


def measure_time(func_name: str):
    """装饰器：测量函数执行时间"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_database_operation(func_name, duration)

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_database_operation(func_name, duration)

        return async_wrapper if hasattr(func, "__code__") and func.__code__.co_flags & 0x80 else sync_wrapper

    return decorator

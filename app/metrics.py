"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: metrics.py
@DateTime: 2025年5月30日
@Docs: Prometheus 指标导出模块
"""

from starlette_exporter import PrometheusMiddleware, handle_metrics


def setup_metrics(app):
    """
    设置 Prometheus 指标中间件和端点。

    Args:
        app: FastAPI 应用实例。
    """
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics", handle_metrics)

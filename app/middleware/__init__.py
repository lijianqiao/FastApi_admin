"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:30:00
@Docs: 中间件模块初始化文件
"""

import os

from fastapi import FastAPI

from .cors import setup_cors_middleware
from .logging import setup_logging_middleware
from .ratelimiter import setup_ratelimiter


def setup_middlewares(app: FastAPI) -> None:
    """设置所有中间件"""
    # 设置日志中间件（应该最先添加，以便记录所有请求）
    setup_logging_middleware(app)

    # 设置CORS中间件
    setup_cors_middleware(app)

    # 全局限流（测试环境下禁用）
    environment = os.getenv("ENVIRONMENT", "development")
    if environment != "testing":
        setup_ratelimiter(app)

    # 其他中间件可以在这里添加
    # setup_rate_limiting_middleware(app)
    # setup_security_middleware(app)

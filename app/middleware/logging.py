"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: logging.py
@DateTime: 2025/06/02 02:30:00
@Docs: 日志中间件设置
"""

from fastapi import FastAPI

from app.utils.logging_middleware import LoggingMiddleware, RequestIDMiddleware


def setup_logging_middleware(app: FastAPI) -> None:
    """设置日志中间件"""
    # 添加请求ID中间件（必须在日志中间件之前）
    app.add_middleware(RequestIDMiddleware)

    # 添加日志记录中间件
    app.add_middleware(LoggingMiddleware)

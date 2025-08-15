"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: middleware.py
@DateTime: 2025/07/05
@Docs: 中间件配置
"""

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.utils.logger import logger
from app.utils.metrics import metrics_collector
from app.utils.rate_limit import rate_limit_per_ip_per_minute
from app.utils.request_context import clear_client_ip, clear_request_id, set_client_ip, set_request_id


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理限流逻辑"""
        limiter = rate_limit_per_ip_per_minute()
        # 作为依赖执行
        await limiter(request)

        return await call_next(request)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志（异常也计入指标）"""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        set_client_ip(request.client.host if request.client else "unknown")

        logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}]")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            try:
                metrics_collector.record_request(request.method, request.url.path, response.status_code, process_time)
            except Exception:
                pass
            logger.info(
                f"Request finished: {request.method} {request.url.path} Status: {response.status_code} [ID: {request_id}]"
            )
            return response
        except Exception as e:
            # 异常路径也统计
            process_time = time.time() - start_time
            status_code = getattr(e, "status_code", 500)
            try:
                metrics_collector.record_request(request.method, request.url.path, status_code, process_time)
            except Exception:
                pass
            logger.exception(
                f"Request error: {request.method} {request.url.path} Status: {status_code} [ID: {request_id}]"
            )
            raise
        finally:
            clear_request_id()
            clear_client_ip()


def setup_middlewares(app: FastAPI) -> None:
    """
    注册中间件
    """
    # CORS 中间件，处理跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip 压缩中间件，减少响应体大小
    if settings.ENABLE_GZIP:
        app.add_middleware(GZipMiddleware, minimum_size=settings.GZIP_MINIMUM_SIZE)

    # Session 中间件（JWT 场景默认关闭，可按需开启）
    if settings.ENABLE_SESSION_MIDDLEWARE:
        app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # 请求日志中间件
    if settings.ENABLE_REQUEST_TRACKING:
        app.add_middleware(RequestLoggerMiddleware)

    # 安全中间件（生产环境）
    if settings.IS_PRODUCTION and settings.ENABLE_TRUSTED_HOST and settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    if settings.IS_PRODUCTION and settings.ENABLE_HTTPS_REDIRECT:
        app.add_middleware(HTTPSRedirectMiddleware)

    # 限流中间件
    app.add_middleware(RateLimitMiddleware)

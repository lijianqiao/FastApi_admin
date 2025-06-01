"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: logging_middleware.py
@DateTime: 2025/06/02
@Docs: 日志记录中间件
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger, log_error_with_context, log_request

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""

    def __init__(self, app, skip_paths: list[str] | None = None):
        """
        初始化日志中间件

        Args:
            app: FastAPI应用实例
            skip_paths: 跳过记录的路径列表
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        # 生成请求ID
        request_id = str(uuid.uuid4())

        # 将request_id添加到request state
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 跳过特定路径的日志记录
        if request.url.path in self.skip_paths:
            response = await call_next(request)
            return response

        # 记录请求开始
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 计算响应时间
            process_time = time.time() - start_time

            # 获取响应大小
            response_size = 0
            if hasattr(response, "headers"):
                content_length = response.headers.get("content-length")
                if content_length:
                    response_size = int(content_length)

            # 记录访问日志
            log_request(
                remote_addr=client_ip,
                method=request.method,
                path=request.url.path,
                protocol=f"{request.url.scheme.upper()}/{request.scope.get('http_version', '1.1')}",
                status_code=response.status_code,
                response_length=response_size,
                user_agent=user_agent,
                response_time=process_time,
                request_id=request_id,
                user_id=getattr(request.state, "user_id", None),
            )

            # 记录请求完成
            logger.info(
                f"请求完成: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": f"{process_time:.3f}s",
                    "response_size": response_size,
                },
            )

            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 计算错误响应时间
            process_time = time.time() - start_time

            # 记录错误日志
            log_error_with_context(
                error=e,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "response_time": process_time,
                },
                request_id=request_id,
                user_id=getattr(request.state, "user_id", None),
            )

            # 重新抛出异常，让错误处理器处理
            raise e

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一个IP（客户端真实IP）
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 如果没有代理头，返回直接连接的IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件（简化版本，仅添加请求ID）"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """为每个请求生成唯一ID"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

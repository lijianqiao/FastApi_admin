"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: cors.py
@DateTime: 2025/06/02 02:30:00
@Docs: CORS中间件设置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def setup_cors_middleware(app: FastAPI) -> None:
    """设置CORS中间件"""
    if settings.cors.allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=settings.cors.allow_methods,
            allow_headers=settings.cors.allow_headers,
        )
